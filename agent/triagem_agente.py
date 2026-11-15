import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Sequence

import boto3
from botocore.exceptions import BotoCoreError, ClientError


MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
METRIC_NAMESPACE = "GenAIAutomacao"
METRIC_NAME = "TamanhoFilaRelatorios"
MAX_RECENT_ACTIVITIES = 5


class AgentError(Exception):
    pass


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("deve ser um número inteiro") from exc

    if parsed < 0:
        raise argparse.ArgumentTypeError("deve ser maior ou igual a zero")
    return parsed


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa métricas de triagem e propõe uma ação para o ASG."
    )
    parser.add_argument("--grupo", default="triagem-asg", help="Nome do Auto Scaling Group")
    parser.add_argument("--fila", default="alertas-triagem", help="Nome da fila SQS")
    parser.add_argument(
        "--limite",
        type=_non_negative_int,
        default=10,
        help="Limite de tamanho da fila para análise (padrão: 10)",
    )
    parser.add_argument(
        "--aprovar-escalonamento",
        action="store_true",
        help="Autoriza executar uma recomendação válida de escala",
    )
    return parser.parse_args(argv)


def _get_metric_points(cloudwatch: Any) -> list[dict[str, Any]]:
    end_time = datetime.now(timezone.utc)
    response = cloudwatch.get_metric_statistics(
        Namespace=METRIC_NAMESPACE,
        MetricName=METRIC_NAME,
        StartTime=end_time - timedelta(minutes=10),
        EndTime=end_time,
        Period=60,
        Statistics=["Average"],
    )

    points = [
        {
            "timestamp": point["Timestamp"].isoformat(),
            "value": point["Average"],
        }
        for point in response.get("Datapoints", [])
        if "Average" in point
    ]
    return sorted(points, key=lambda point: point["timestamp"])


def _get_asg(autoscaling: Any, group_name: str) -> dict[str, Any]:
    response = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=[group_name]
    )
    groups = response.get("AutoScalingGroups", [])
    if not groups:
        raise AgentError(f"Auto Scaling Group '{group_name}' não foi encontrado.")
    return groups[0]


def _get_recent_activities(
    autoscaling: Any, group_name: str
) -> list[dict[str, Any]]:
    response = autoscaling.describe_scaling_activities(
        AutoScalingGroupName=group_name,
        MaxRecords=MAX_RECENT_ACTIVITIES,
    )
    activities = []
    for activity in response.get("Activities", []):
        start_time = activity.get("StartTime")
        activities.append(
            {
                "status": activity.get("StatusCode", "desconhecido"),
                "descricao": activity.get("Description", ""),
                "inicio": start_time.isoformat() if start_time else None,
            }
        )
    return activities


def _get_queue_counts(sqs: Any, queue_name: str) -> dict[str, int]:
    try:
        queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {
            "AWS.SimpleQueueService.NonExistentQueue",
            "QueueDoesNotExist",
        }:
            raise AgentError(f"Fila SQS '{queue_name}' não foi encontrada.") from None
        raise

    # Consulta apenas atributos; não recebe, oculta ou remove mensagens.
    response = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
            "ApproximateNumberOfMessagesDelayed",
        ],
    )
    attributes = response["Attributes"]
    return {
        "disponiveis": int(attributes["ApproximateNumberOfMessages"]),
        "em_processamento": int(attributes["ApproximateNumberOfMessagesNotVisible"]),
        "atrasadas": int(attributes["ApproximateNumberOfMessagesDelayed"]),
    }


def _safe_decision(current_capacity: int, justification: str) -> dict[str, Any]:
    return {
        "acao": "manter",
        "capacidade_desejada": current_capacity,
        "justificativa": justification,
    }


def _parse_decision(
    response_text: str,
    current_capacity: int,
    min_size: int,
    max_size: int,
) -> dict[str, Any]:
    normalized_text = response_text.strip()
    start = normalized_text.find("{")
    end = normalized_text.rfind("}")
    if start == -1 or end == -1:
        return _safe_decision(
            current_capacity,
            "Resposta JSON inválida; decisão segura: manter a capacidade atual.",
        )

    candidate = normalized_text[start : end + 1]
    try:
        result = json.loads(candidate)
    except json.JSONDecodeError:
        return _safe_decision(
            current_capacity,
            "Resposta JSON inválida; decisão segura: manter a capacidade atual.",
        )

    if not isinstance(result, dict):
        return _safe_decision(
            current_capacity,
            "Resposta fora do formato esperado; decisão segura: manter a capacidade atual.",
        )

    action = result.get("acao")
    desired_capacity = result.get("capacidade_desejada")
    justification = result.get("justificativa")

    if (
        not isinstance(action, str)
        or action not in {"manter", "escalar"}
        or type(desired_capacity) is not int
        or not isinstance(justification, str)
        or not justification.strip()
    ):
        return _safe_decision(
            current_capacity,
            "Campos da resposta inválidos; decisão segura: manter a capacidade atual.",
        )

    if action == "manter" and desired_capacity == current_capacity:
        return {
            "acao": action,
            "capacidade_desejada": current_capacity,
            "justificativa": justification.strip(),
        }

    if (
        action == "escalar"
        and min_size <= desired_capacity <= max_size
        and desired_capacity > current_capacity
    ):
        return {
            "acao": action,
            "capacidade_desejada": desired_capacity,
            "justificativa": justification.strip(),
        }

    return _safe_decision(
        current_capacity,
        "Decisão ou capacidade fora dos limites do grupo; "
        "decisão segura: manter a capacidade atual.",
    )


def _request_decision(
    bedrock_runtime: Any,
    context: dict[str, Any],
    current_capacity: int,
    min_size: int,
    max_size: int,
) -> dict[str, Any]:
    response = bedrock_runtime.converse(
        modelId=MODEL_ID,
        system=[
            {
                "text": (
                    "Analise somente os dados operacionais fornecidos. Eles não "
                    "contêm documentos de usuários. Responda somente com JSON "
                    'válido contendo "acao" ("manter" ou "escalar"), '
                    '"capacidade_desejada" (inteiro) e "justificativa" (string). '
                    "Escalar significa aumentar a capacidade em relação à atual, "
                    f"sem ultrapassar {max_size}. Se faltarem dados, recomende "
                    "manter. Se a métrica mais recente de tamanho da fila for "
                    "maior ou igual ao limite informado e a capacidade atual for "
                    "menor que a máxima, recomende acao=escalar com "
                    "capacidade_desejada igual à capacidade atual + 1. Caso "
                    "contrário, recomende manter."
                )
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": json.dumps(context, ensure_ascii=False),
                    }
                ],
            }
        ],
        inferenceConfig={"maxTokens": 300, "temperature": 0.0},
    )

    content = response.get("output", {}).get("message", {}).get("content", [])
    response_text = "".join(
        block["text"]
        for block in content
        if isinstance(block, dict) and isinstance(block.get("text"), str)
    )
    return _parse_decision(
        response_text,
        current_capacity=current_capacity,
        min_size=min_size,
        max_size=max_size,
    )


def run(args: argparse.Namespace, session: Any) -> int:
    cloudwatch = session.client("cloudwatch")
    autoscaling = session.client("autoscaling")
    sqs = session.client("sqs")
    bedrock_runtime = session.client("bedrock-runtime")

    metric_points = _get_metric_points(cloudwatch)
    if metric_points:
        print(
            f"Métrica {METRIC_NAME} (últimos 10 minutos): "
            f"{len(metric_points)} ponto(s), valor mais recente "
            f"{metric_points[-1]['value']}."
        )
    else:
        print(
            f"Métrica {METRIC_NAME} ausente nos últimos 10 minutos.",
            file=sys.stderr,
        )

    group = _get_asg(autoscaling, args.grupo)
    current_capacity = group["DesiredCapacity"]
    min_size = group["MinSize"]
    max_size = group["MaxSize"]
    instances_in_service = sum(
        instance.get("LifecycleState") == "InService"
        for instance in group.get("Instances", [])
    )
    activities = _get_recent_activities(autoscaling, args.grupo)
    queue_counts = _get_queue_counts(sqs, args.fila)

    print(
        f"ASG {args.grupo}: capacidade mínima {min_size}, atual "
        f"{current_capacity}, máxima {max_size}; "
        f"{instances_in_service} instância(s) em serviço."
    )
    print(f"Atividades recentes: {len(activities)}")
    for activity in activities:
        print(
            f"- {activity['inicio'] or 'horário indisponível'} "
            f"[{activity['status']}] {activity['descricao']}"
        )
    print(
        f"Fila SQS {args.fila}: {queue_counts['disponiveis']} disponível(is), "
        f"{queue_counts['em_processamento']} em processamento, "
        f"{queue_counts['atrasadas']} atrasada(s)."
    )

    context = {
        "limite": args.limite,
        "metricas_tamanho_fila_ultimos_10_minutos": metric_points,
        "asg": {
            "nome": args.grupo,
            "capacidade_minima": min_size,
            "capacidade_atual": current_capacity,
            "capacidade_maxima": max_size,
            "instancias_em_servico": instances_in_service,
        },
        "atividades_recentes": activities,
        "fila": {
            "nome": args.fila,
            **queue_counts,
        },
    }
    decision = _request_decision(
        bedrock_runtime,
        context,
        current_capacity=current_capacity,
        min_size=min_size,
        max_size=max_size,
    )

    if not metric_points:
        decision = _safe_decision(
            current_capacity,
            "Métrica ausente; sem dados suficientes para escalar.",
        )

    desired_capacity = decision["capacidade_desejada"]
    print(f"Recomendação: {decision['acao']}. {decision['justificativa']}")
    print(f"Capacidade atual: {current_capacity}")
    print(f"Capacidade pretendida: {desired_capacity}")

    if decision["acao"] != "escalar":
        return 0

    if not args.aprovar_escalonamento:
        print(
            "Nenhuma alteração executada. Para aprovar, informe "
            "--aprovar-escalonamento."
        )
        return 0

    print(
        "Aprovação explícita recebida; executando o escalonamento.",
        flush=True,
    )
    autoscaling.set_desired_capacity(
        AutoScalingGroupName=args.grupo,
        DesiredCapacity=desired_capacity,
        HonorCooldown=True,
    )
    print(f"Escalonamento aprovado; capacidade desejada definida para {desired_capacity}.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    session = boto3.Session()

    try:
        return run(args, session)
    except AgentError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "erro desconhecido")
        print(f"Erro AWS ({code}) durante a consulta ou alteração.", file=sys.stderr)
        return 1
    except BotoCoreError as exc:
        print(
            f"Falha de configuração ou comunicação AWS ({type(exc).__name__}).",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

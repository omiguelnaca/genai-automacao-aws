import sys

import boto3


CONTA_FLOCI = "000000000000"


def main() -> int:
    session = boto3.Session()
    sts = session.client("sts")
    conta = sts.get_caller_identity()["Account"]

    if conta != CONTA_FLOCI:
        print(
            f"Conta AWS inesperada: {conta}. "
            f"O inventário só pode ser executado na conta {CONTA_FLOCI}.",
            file=sys.stderr,
        )
        return 1

    s3 = session.client("s3")
    dynamodb = session.client("dynamodb")
    iam = session.client("iam")

    buckets = [bucket["Name"] for bucket in s3.list_buckets().get("Buckets", [])]

    tabelas = []
    for pagina in dynamodb.get_paginator("list_tables").paginate():
        tabelas.extend(pagina.get("TableNames", []))

    usuarios = []
    for pagina in iam.get_paginator("list_users").paginate():
        usuarios.extend(usuario["UserName"] for usuario in pagina.get("Users", []))

    print("Buckets S3:")
    print("\n".join(f"- {nome}" for nome in buckets) if buckets else "- Nenhum")

    print("\nTabelas DynamoDB:")
    print("\n".join(f"- {nome}" for nome in tabelas) if tabelas else "- Nenhuma")

    print("\nUsuários IAM:")
    print("\n".join(f"- {nome}" for nome in usuarios) if usuarios else "- Nenhum")

    return 0


if __name__ == "__main__":
    sys.exit(main())

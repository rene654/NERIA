import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from load_benchmark import validate_dataset, validate_money


def connection_settings() -> dict[str, Any]:
    password = os.environ.get("POSTGRES_PASSWORD")

    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD no está disponible en el entorno"
        )

    return {
        "host": os.environ.get(
            "POSTGRES_HOST",
            "127.0.0.1",
        ),
        "port": os.environ.get(
            "POSTGRES_PORT",
            "5432",
        ),
        "dbname": os.environ.get(
            "POSTGRES_DB",
            "neria",
        ),
        "user": os.environ.get(
            "POSTGRES_USER",
            "neria_dev",
        ),
        "password": password,
        "connect_timeout": 5,
    }


def delete_existing(
    cursor: psycopg.Cursor[Any],
    manifest_id: str,
) -> None:
    child_tables = (
        "case_relationships",
        "label_actions",
        "label_rules",
        "labels",
        "case_history",
        "case_inputs",
    )

    for table in child_tables:
        cursor.execute(
            f"""
            DELETE FROM benchmark.{table}
            WHERE case_id IN (
                SELECT case_id
                FROM benchmark.cases
                WHERE manifest_id = %s
            )
            """,
            (manifest_id,),
        )

    cursor.execute(
        """
        DELETE FROM benchmark.cases
        WHERE manifest_id = %s
        """,
        (manifest_id,),
    )

    cursor.execute(
        """
        DELETE FROM benchmark.dataset_manifests
        WHERE manifest_id = %s
        """,
        (manifest_id,),
    )


def load_dataset(
    payload: dict[str, Any],
    cases: list[dict[str, Any]],
    dataset_hash: str,
    replace: bool,
) -> None:
    manifest = payload["manifest"]
    manifest_id = manifest["manifest_id"]

    with psycopg.connect(
        **connection_settings()
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM meta.schema_migrations
                WHERE migration_id = %s
                """,
                (manifest["source_migration"],),
            )

            if cursor.fetchone() is None:
                raise ValueError(
                    "La migración fuente no está aplicada"
                )

            cursor.execute(
                """
                SELECT 1
                FROM benchmark.dataset_manifests
                WHERE manifest_id = %s
                """,
                (manifest_id,),
            )

            exists = cursor.fetchone() is not None

            if exists and not replace:
                raise ValueError(
                    "El manifiesto ya existe; "
                    "usa --replace conscientemente"
                )

            if exists:
                delete_existing(
                    cursor,
                    manifest_id,
                )

            cursor.execute(
                """
                INSERT INTO benchmark.dataset_manifests (
                    manifest_id,
                    dataset_name,
                    dataset_version,
                    contract_version,
                    generator_version,
                    random_seed,
                    policy_code,
                    policy_version,
                    source_migration,
                    total_cases,
                    development_cases,
                    holdout_cases,
                    holdout_locked,
                    dataset_hash
                ) VALUES (
                    %(manifest_id)s,
                    %(dataset_name)s,
                    %(dataset_version)s,
                    %(contract_version)s,
                    %(generator_version)s,
                    %(random_seed)s,
                    %(policy_code)s,
                    %(policy_version)s,
                    %(source_migration)s,
                    %(total_cases)s,
                    %(development_cases)s,
                    %(holdout_cases)s,
                    %(holdout_locked)s,
                    %(dataset_hash)s
                )
                """,
                {
                    **manifest,
                    "dataset_hash": dataset_hash,
                },
            )

            for case in cases:
                cursor.execute(
                    """
                    INSERT INTO benchmark.cases (
                        case_id,
                        manifest_id,
                        case_ref,
                        split,
                        family_key,
                        variant_type,
                        organization_profile_key,
                        jurisdiction_country,
                        employee_key,
                        merchant_key,
                        category_hint,
                        amount_mxn,
                        currency,
                        expense_date,
                        input_hash,
                        receipt_hash
                    ) VALUES (
                        %(case_id)s,
                        %(manifest_id)s,
                        %(case_ref)s,
                        %(split)s,
                        %(family_key)s,
                        %(variant_type)s,
                        %(organization_profile_key)s,
                        %(jurisdiction_country)s,
                        %(employee_key)s,
                        %(merchant_key)s,
                        %(category_hint)s,
                        %(amount_mxn)s,
                        %(currency)s,
                        %(expense_date)s,
                        %(input_hash)s,
                        %(receipt_hash)s
                    )
                    """,
                    {
                        **case,
                        "manifest_id": manifest_id,
                        "amount_mxn": validate_money(
                            case["amount_mxn"],
                            "amount_mxn",
                        ),
                    },
                )

                case_input = case["input"]
                receipt_total = case_input.get(
                    "receipt_total_mxn"
                )

                cursor.execute(
                    """
                    INSERT INTO benchmark.case_inputs (
                        case_id,
                        submitted_at,
                        receipt_state,
                        receipt_fixture_ref,
                        receipt_total_mxn,
                        business_purpose_declared,
                        category_context
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        case["case_id"],
                        case_input["submitted_at"],
                        case_input["receipt_state"],
                        case_input.get(
                            "receipt_fixture_ref"
                        ),
                        validate_money(
                            receipt_total,
                            "receipt_total_mxn",
                        )
                        if receipt_total is not None
                        else None,
                        case_input.get(
                            "business_purpose_declared"
                        ),
                        Jsonb(
                            case_input.get(
                                "category_context",
                                {},
                            )
                        ),
                    ),
                )

                for history in case.get(
                    "history",
                    [],
                ):
                    cursor.execute(
                        """
                        INSERT INTO benchmark.case_history (
                            history_id,
                            case_id,
                            historical_expense_key,
                            employee_key,
                            merchant_key,
                            amount_mxn,
                            currency,
                            expense_date,
                            receipt_hash
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        """,
                        (
                            history["history_id"],
                            case["case_id"],
                            history[
                                "historical_expense_key"
                            ],
                            history["employee_key"],
                            history["merchant_key"],
                            validate_money(
                                history["amount_mxn"],
                                "history.amount_mxn",
                            ),
                            history["currency"],
                            history["expense_date"],
                            history.get("receipt_hash"),
                        ),
                    )

                label = case["label"]

                cursor.execute(
                    """
                    INSERT INTO benchmark.labels (
                        case_id,
                        expected_compliance,
                        expected_risk,
                        expected_route,
                        assessment_complete,
                        miss_severity,
                        miss_severity_rationale,
                        rationale
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        case["case_id"],
                        label["expected_compliance"],
                        label["expected_risk"],
                        label["expected_route"],
                        label["assessment_complete"],
                        label["miss_severity"],
                        label["miss_severity_rationale"],
                        label["rationale"],
                    ),
                )

                for rule in label["rules"]:
                    cursor.execute(
                        """
                        INSERT INTO benchmark.label_rules (
                            case_id,
                            rule_code,
                            expected_state,
                            evidence_ref,
                            rule_version
                        ) VALUES (
                            %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            case["case_id"],
                            rule["rule_code"],
                            rule["expected_state"],
                            rule["evidence_ref"],
                            rule["rule_version"],
                        ),
                    )

                for action_code in label["permitted_actions"]:
                    cursor.execute(
                        """
                        INSERT INTO benchmark.label_actions (
                            case_id,
                            action_code
                        ) VALUES (
                            %s, %s
                        )
                        """,
                        (
                            case["case_id"],
                            action_code,
                        ),
                    )

            case_ids_by_ref = {
                case["case_ref"]: case["case_id"]
                for case in cases
            }

            for case in cases:
                relationship = case.get("relationship")

                if relationship is None:
                    continue

                cursor.execute(
                    """
                    INSERT INTO benchmark.case_relationships (
                        manifest_id,
                        case_id,
                        base_case_id,
                        family_key,
                        split,
                        relationship_type,
                        changed_fields,
                        expected_effect,
                        expected_changed_outputs
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        manifest_id,
                        case["case_id"],
                        case_ids_by_ref[
                            relationship["base_case_ref"]
                        ],
                        case["family_key"],
                        case["split"],
                        relationship["relationship_type"],
                        relationship["changed_fields"],
                        relationship["expected_effect"],
                        relationship[
                            "expected_changed_outputs"
                        ],
                    ),
                )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Importa el benchmark NERIA "
            "a PostgreSQL"
        )
    )
    parser.add_argument(
        "fixture",
        type=Path,
    )
    parser.add_argument(
        "--replace",
        action="store_true",
    )
    args = parser.parse_args()

    payload = json.loads(
        args.fixture.read_text(
            encoding="utf-8"
        )
    )
    cases, dataset_hash = validate_dataset(
        payload
    )

    print(
        f"Validation: PASS ({len(cases)} cases)"
    )
    print(
        f"Dataset hash: {dataset_hash}"
    )

    load_dataset(
        payload,
        cases,
        dataset_hash,
        args.replace,
    )

    print("Database load: PASS")


if __name__ == "__main__":
    main()
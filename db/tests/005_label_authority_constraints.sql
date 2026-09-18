BEGIN;

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
    holdout_locked
)
VALUES (
    '00000000-0000-0000-0000-000000000901',
    'NERIA_ACTION_TEST',
    '0.1.0',
    'v0.1',
    'manual-test',
    20260916,
    'CORPORATE_EXPENSE',
    'v1.0',
    '005',
    1,
    1,
    0,
    TRUE
);

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
    input_hash
)
VALUES (
    '00000000-0000-0000-0000-000000000902',
    '00000000-0000-0000-0000-000000000901',
    'DEV-ACTION-TEST-001',
    'DEVELOPMENT',
    'FAM-ACTION-TEST-001',
    'AUTHORITY',
    'ORG-PROFILE-ACTION-TEST-MX',
    'MX',
    'EMP-SYN-901',
    'MERCHANT-SYN-901',
    'HOTEL',
    1000.00,
    'MXN',
    CURRENT_DATE,
    repeat('a', 64)
);

INSERT INTO benchmark.labels (
    case_id,
    expected_compliance,
    expected_risk,
    expected_route,
    assessment_complete,
    miss_severity,
    miss_severity_rationale,
    rationale
)
VALUES (
    '00000000-0000-0000-0000-000000000902',
    'COMPLIANT',
    'LOW',
    'SCREENING_COMPLETE',
    TRUE,
    'LOW',
    'Missing this synthetic result has low business impact.',
    'Synthetic authority constraint test.'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO benchmark.label_actions (
            case_id,
            action_code
        )
        VALUES (
            '00000000-0000-0000-0000-000000000999',
            'RECORD_SCREENING_RESULT'
        );
        RAISE EXCEPTION 'FAIL 1: orphan action accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'PASS 1: orphan action rejected';
    END;

    BEGIN
        INSERT INTO benchmark.label_actions (
            case_id,
            action_code
        )
        VALUES (
            '00000000-0000-0000-0000-000000000902',
            'APPROVE_PAYMENT'
        );
        RAISE EXCEPTION 'FAIL 2: financial authority accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 2: financial authority rejected';
    END;
END
$$;

INSERT INTO benchmark.label_actions (
    case_id,
    action_code
)
VALUES (
    '00000000-0000-0000-0000-000000000902',
    'RECORD_SCREENING_RESULT'
);

DO $$
BEGIN
    BEGIN
        INSERT INTO benchmark.label_actions (
            case_id,
            action_code
        )
        VALUES (
            '00000000-0000-0000-0000-000000000902',
            'RECORD_SCREENING_RESULT'
        );
        RAISE EXCEPTION 'FAIL 3: duplicate action accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 3: duplicate action rejected';
    END;

    BEGIN
        INSERT INTO benchmark.label_rules (
            case_id,
            rule_code,
            expected_state,
            evidence_ref,
            rule_version
        )
        VALUES (
            '00000000-0000-0000-0000-000000000902',
            'R01',
            'PASS',
            'Synthetic evidence.',
            '   '
        );
        RAISE EXCEPTION 'FAIL 4: blank rule version accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 4: blank rule version rejected';
    END;

    BEGIN
        INSERT INTO benchmark.label_rules (
            case_id,
            rule_code,
            expected_state,
            evidence_ref,
            rule_version
        )
        VALUES (
            '00000000-0000-0000-0000-000000000902',
            'R02',
            'PASS',
            'Synthetic evidence.',
            NULL
        );
        RAISE EXCEPTION 'FAIL 5: null rule version accepted';
    EXCEPTION
        WHEN not_null_violation THEN
            RAISE NOTICE 'PASS 5: null rule version rejected';
    END;
END
$$;

ROLLBACK;

\echo 'PASS: 5 label authority constraint tests completed'
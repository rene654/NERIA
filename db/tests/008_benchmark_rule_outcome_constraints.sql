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
    holdout_locked,
    dataset_hash
)
VALUES (
    '00000000-0000-4000-8000-000000008801',
    'NERIA_RULE_OUTCOME_TEST',
    '0.2.1-test',
    'v0.2',
    'manual-test-008',
    20260918,
    'CORPORATE_EXPENSE',
    'v1.0',
    '008',
    2,
    2,
    0,
    TRUE,
    repeat('a', 64)
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
    input_hash,
    receipt_hash
)
VALUES
(
    '00000000-0000-4000-8000-000000008802',
    '00000000-0000-4000-8000-000000008801',
    'DEV-RULE-OUTCOME-001',
    'DEVELOPMENT',
    'FAM-RULE-OUTCOME-001',
    'AUTHORITY',
    'ORG-PROFILE-TEST-MX',
    'MX',
    'EMP-TEST-008',
    'MERCHANT-TEST-008',
    'UNKNOWN',
    1000.00,
    'MXN',
    DATE '2026-09-01',
    repeat('b', 64),
    NULL
),
(
    '00000000-0000-4000-8000-000000008803',
    '00000000-0000-4000-8000-000000008801',
    'DEV-RULE-OUTCOME-002',
    'DEVELOPMENT',
    'FAM-RULE-OUTCOME-002',
    'BASELINE',
    'ORG-PROFILE-TEST-MX',
    'MX',
    'EMP-TEST-008',
    'MERCHANT-TEST-008',
    'UNKNOWN',
    1000.00,
    'MXN',
    DATE '2026-09-01',
    repeat('c', 64),
    NULL
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
    '00000000-0000-4000-8000-000000008802',
    'UNDETERMINED',
    'UNDETERMINED',
    'POLICY_CLARIFICATION',
    FALSE,
    'MEDIUM',
    'Missing policy clarification can produce an incorrect result.',
    'Synthetic constraint test for migration 008.'
);

INSERT INTO benchmark.label_rules (
    case_id,
    rule_code,
    expected_state,
    evidence_ref,
    rule_version
)
VALUES
(
    '00000000-0000-4000-8000-000000008802',
    'R07',
    'CONTROL',
    'constraint_test=CONTROL',
    'v1.0'
),
(
    '00000000-0000-4000-8000-000000008802',
    'R11',
    'INVALID_INPUT',
    'constraint_test=INVALID_INPUT',
    'v1.0'
),
(
    '00000000-0000-4000-8000-000000008802',
    'R12',
    'OUT_OF_SCOPE',
    'constraint_test=OUT_OF_SCOPE',
    'v1.0'
),
(
    '00000000-0000-4000-8000-000000008802',
    'R13',
    'ACTION_DENIED',
    'constraint_test=ACTION_DENIED',
    'v1.0'
),
(
    '00000000-0000-4000-8000-000000008802',
    'R14',
    'TECHNICAL_ERROR',
    'constraint_test=TECHNICAL_ERROR',
    'v1.0'
);

INSERT INTO benchmark.label_actions (
    case_id,
    action_code
)
VALUES (
    '00000000-0000-4000-8000-000000008802',
    'REQUEST_POLICY_CLARIFICATION'
);

DO $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM benchmark.label_rules
        WHERE case_id =
            '00000000-0000-4000-8000-000000008802'
          AND expected_state = 'CONTROL'
    ) <> 1 THEN
        RAISE EXCEPTION 'FAIL 1: CONTROL was not accepted';
    END IF;

    RAISE NOTICE 'PASS 1: CONTROL accepted';

    IF (
        SELECT COUNT(*)
        FROM benchmark.label_rules
        WHERE case_id =
            '00000000-0000-4000-8000-000000008802'
          AND expected_state IN (
              'INVALID_INPUT',
              'OUT_OF_SCOPE',
              'ACTION_DENIED',
              'TECHNICAL_ERROR'
          )
    ) <> 4 THEN
        RAISE EXCEPTION
            'FAIL 2: specialized rule outcomes were not accepted';
    END IF;

    RAISE NOTICE
        'PASS 2: R11-R14 specialized outcomes accepted';

    IF NOT EXISTS (
        SELECT 1
        FROM benchmark.labels
        WHERE case_id =
            '00000000-0000-4000-8000-000000008802'
          AND expected_route = 'POLICY_CLARIFICATION'
    ) THEN
        RAISE EXCEPTION
            'FAIL 3: POLICY_CLARIFICATION was not accepted';
    END IF;

    RAISE NOTICE
        'PASS 3: POLICY_CLARIFICATION route accepted';

    IF NOT EXISTS (
        SELECT 1
        FROM benchmark.label_actions
        WHERE case_id =
            '00000000-0000-4000-8000-000000008802'
          AND action_code =
            'REQUEST_POLICY_CLARIFICATION'
    ) THEN
        RAISE EXCEPTION
            'FAIL 4: clarification action was not accepted';
    END IF;

    RAISE NOTICE
        'PASS 4: policy clarification action accepted';
END
$$;

DO $$
DECLARE
    passed_tests INTEGER := 0;
BEGIN
    BEGIN
        INSERT INTO benchmark.label_rules (
            case_id,
            rule_code,
            expected_state,
            evidence_ref,
            rule_version
        )
        VALUES (
            '00000000-0000-4000-8000-000000008802',
            'R99',
            'UNKNOWN_OUTCOME',
            'constraint_test=invalid_state',
            'v1.0'
        );

        RAISE EXCEPTION
            'FAIL 5: unknown rule outcome accepted';
    EXCEPTION
        WHEN check_violation THEN
            passed_tests := passed_tests + 1;
            RAISE NOTICE
                'PASS 5: unknown rule outcome rejected';
    END;

    BEGIN
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
            '00000000-0000-4000-8000-000000008803',
            'UNDETERMINED',
            'UNDETERMINED',
            'UNKNOWN_ROUTE',
            FALSE,
            'MEDIUM',
            'Synthetic invalid route test.',
            'Synthetic invalid route test.'
        );

        RAISE EXCEPTION
            'FAIL 6: unknown route accepted';
    EXCEPTION
        WHEN check_violation THEN
            passed_tests := passed_tests + 1;
            RAISE NOTICE
                'PASS 6: unknown route rejected';
    END;

    BEGIN
        INSERT INTO benchmark.label_actions (
            case_id,
            action_code
        )
        VALUES (
            '00000000-0000-4000-8000-000000008802',
            'APPROVE_PAYMENT'
        );

        RAISE EXCEPTION
            'FAIL 7: financial authority accepted';
    EXCEPTION
        WHEN check_violation THEN
            passed_tests := passed_tests + 1;
            RAISE NOTICE
                'PASS 7: financial authority remains rejected';
    END;

    IF passed_tests <> 3 THEN
        RAISE EXCEPTION
            'Expected 3 negative tests, completed %',
            passed_tests;
    END IF;
END
$$;

ROLLBACK;

\echo 'PASS: 7 benchmark rule outcome constraint tests completed'
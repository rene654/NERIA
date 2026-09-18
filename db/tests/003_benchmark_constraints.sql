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
    holdout_cases
)
VALUES (
    '00000000-0000-0000-0000-000000000601',
    'NERIA_BENCHMARK',
    'v0.1-test',
    'v0.1',
    'generator-test-001',
    20260914,
    'CORPORATE_EXPENSE',
    'v1.0',
    '003',
    1,
    1,
    0
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
    expense_date,
    input_hash,
    receipt_hash
)
VALUES (
    '00000000-0000-0000-0000-000000000602',
    '00000000-0000-0000-0000-000000000601',
    'DEV-TEST-001',
    'DEVELOPMENT',
    'FAM-TEST-001',
    'BASELINE',
    'ORG-PROFILE-BENCHMARK-TEST-MX',
    'MX',
    'EMP-TEST-001',
    'MERCHANT-TEST-001',
    'HOTEL',
    1000.00,
    DATE '2026-09-10',
    repeat('a', 64),
    repeat('b', 64)
);
INSERT INTO benchmark.case_history (
    history_id,
    case_id,
    historical_expense_key,
    employee_key,
    merchant_key,
    amount_mxn,
    expense_date,
    receipt_hash
)
VALUES (
    '00000000-0000-0000-0000-000000000603',
    '00000000-0000-0000-0000-000000000602',
    'HIST-TEST-001',
    'EMP-TEST-001',
    'MERCHANT-TEST-001',
    1000.00,
    DATE '2026-09-01',
    repeat('c', 64)
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
    '00000000-0000-0000-0000-000000000602',
    'COMPLIANT',
    'LOW',
    'SCREENING_COMPLETE',
    TRUE,
    'LOW',
    'Missing this synthetic result has low business impact.',
    'Caso válido de prueba dentro del límite de política.'
);
INSERT INTO benchmark.label_rules (
    case_id,
    rule_code,
    expected_state,
    evidence_ref
)
VALUES (
    '00000000-0000-0000-0000-000000000602',
    'R01',
    'PASS',
    'EVIDENCE-TEST-001'
);
DO $tests$
BEGIN
    BEGIN
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
            holdout_cases
        )
        VALUES (
            '00000000-0000-0000-0000-000000000604',
            'INVALID_COUNTS',
            'v1',
            'v0.1',
            'generator-test',
            1,
            'CORPORATE_EXPENSE',
            'v1.0',
            '003',
            2,
            1,
            0
        );
        RAISE EXCEPTION 'FAIL 1';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 1: inconsistent manifest counts rejected';
    END;
    BEGIN
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
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000605',
            '00000000-0000-0000-0000-000000000601',
            'INVALID-SPLIT',
            'TRAINING',
            'FAM-TEST-002',
            'BASELINE',
            'ORG-PROFILE-BENCHMARK-TEST-MX',
            'MX',
            'EMP-TEST-002',
            'MERCHANT-TEST-002',
            'HOTEL',
            100.00,
            DATE '2026-09-10',
            repeat('d', 64)
        );
        RAISE EXCEPTION 'FAIL 2';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 2: invalid split rejected';
    END;
    BEGIN
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
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000606',
            '00000000-0000-0000-0000-000000000601',
            'INVALID-FAMILY',
            'DEVELOPMENT',
            '',
            'BASELINE',
            'ORG-PROFILE-BENCHMARK-TEST-MX',
            'MX',
            'EMP-TEST-003',
            'MERCHANT-TEST-003',
            'HOTEL',
            100.00,
            DATE '2026-09-10',
            repeat('e', 64)
        );
        RAISE EXCEPTION 'FAIL 3';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 3: empty family rejected';
    END;
    BEGIN
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
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000607',
            '00000000-0000-0000-0000-000000000601',
            'INVALID-HASH',
            'DEVELOPMENT',
            'FAM-TEST-004',
            'BASELINE',
            'ORG-PROFILE-BENCHMARK-TEST-MX',
            'MX',
            'EMP-TEST-004',
            'MERCHANT-TEST-004',
            'HOTEL',
            100.00,
            DATE '2026-09-10',
            'abc'
        );
        RAISE EXCEPTION 'FAIL 4';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 4: invalid input hash rejected';
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
            '00000000-0000-0000-0000-000000000999',
            'COMPLIANT',
            'LOW',
            'SCREENING_COMPLETE',
            TRUE,
            'LOW',
            'Missing this synthetic result has low business impact.',
            'Etiqueta huérfana de prueba.'
        );
        RAISE EXCEPTION 'FAIL 5';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'PASS 5: orphan label rejected';
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
            '00000000-0000-0000-0000-000000000602',
            'INVALID',
            'LOW',
            'SCREENING_COMPLETE',
            TRUE,
            'LOW',
            'Missing this synthetic result has low business impact.',
            'Etiqueta inválida de prueba.'
        );
        RAISE EXCEPTION 'FAIL 6';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 6: invalid compliance label rejected';
    END;
    BEGIN
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
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000608',
            '00000000-0000-0000-0000-000000000601',
            'DEV-TEST-001',
            'DEVELOPMENT',
            'FAM-TEST-005',
            'BASELINE',
            'ORG-PROFILE-BENCHMARK-TEST-MX',
            'MX',
            'EMP-TEST-005',
            'MERCHANT-TEST-005',
            'HOTEL',
            100.00,
            DATE '2026-09-10',
            repeat('f', 64)
        );
        RAISE EXCEPTION 'FAIL 7';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 7: duplicate case reference rejected';
    END;
    BEGIN
        INSERT INTO benchmark.label_rules (
            case_id,
            rule_code,
            expected_state,
            evidence_ref
        )
        VALUES (
            '00000000-0000-0000-0000-000000000602',
            'R01',
            'VIOLATION',
            'EVIDENCE-TEST-002'
        );
        RAISE EXCEPTION 'FAIL 8';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 8: duplicate label rule rejected';
    END;
END
$tests$;
ROLLBACK;
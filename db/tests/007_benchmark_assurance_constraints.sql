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
    '00000000-0000-0000-0000-000000001101',
    'NERIA_ASSURANCE_TEST',
    '0.2-test-007',
    'v0.2',
    'manual-test-007',
    20260917,
    'CORPORATE_EXPENSE',
    'v1.0',
    '007',
    4,
    3,
    1,
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
VALUES
(
    '00000000-0000-0000-0000-000000001102',
    '00000000-0000-0000-0000-000000001101',
    'DEV-ASSURANCE-BASE-001',
    'DEVELOPMENT',
    'FAM-ASSURANCE-A',
    'BASELINE',
    'ORG-PROFILE-ASSURANCE-MX',
    'MX',
    'EMP-ASSURANCE-001',
    'MERCHANT-ASSURANCE-001',
    'HOTEL',
    12000.00,
    'MXN',
    DATE '2026-09-10',
    repeat('a', 64)
),
(
    '00000000-0000-0000-0000-000000001103',
    '00000000-0000-0000-0000-000000001101',
    'DEV-ASSURANCE-VARIANT-001',
    'DEVELOPMENT',
    'FAM-ASSURANCE-A',
    'COUNTERFACTUAL',
    'ORG-PROFILE-ASSURANCE-MX',
    'MX',
    'EMP-ASSURANCE-001',
    'MERCHANT-ASSURANCE-001',
    'HOTEL',
    12000.01,
    'MXN',
    DATE '2026-09-10',
    repeat('b', 64)
),
(
    '00000000-0000-0000-0000-000000001104',
    '00000000-0000-0000-0000-000000001101',
    'DEV-ASSURANCE-OTHER-FAMILY-001',
    'DEVELOPMENT',
    'FAM-ASSURANCE-B',
    'BASELINE',
    'ORG-PROFILE-ASSURANCE-MX',
    'MX',
    'EMP-ASSURANCE-002',
    'MERCHANT-ASSURANCE-002',
    'MEALS',
    500.00,
    'MXN',
    DATE '2026-09-10',
    repeat('c', 64)
),
(
    '00000000-0000-0000-0000-000000001105',
    '00000000-0000-0000-0000-000000001101',
    'HOLDOUT-ASSURANCE-BASE-001',
    'HOLDOUT',
    'FAM-ASSURANCE-A',
    'BASELINE',
    'ORG-PROFILE-ASSURANCE-MX',
    'MX',
    'EMP-ASSURANCE-003',
    'MERCHANT-ASSURANCE-003',
    'HOTEL',
    12000.00,
    'MXN',
    DATE '2026-09-10',
    repeat('d', 64)
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
            '00000000-0000-0000-0000-000000001190',
            'INVALID_CONTRACT_TEST',
            '0.2-invalid',
            '   ',
            'manual-test-007',
            1,
            'CORPORATE_EXPENSE',
            'v1.0',
            '007',
            0,
            0,
            0
        );

        RAISE EXCEPTION
            'FAIL 1: blank contract version accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 1: blank contract version rejected';
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
            currency,
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000001191',
            '00000000-0000-0000-0000-000000001101',
            'DEV-INVALID-COUNTRY',
            'DEVELOPMENT',
            'FAM-ASSURANCE-A',
            'BASELINE',
            'ORG-PROFILE-ASSURANCE-MX',
            'MEX',
            'EMP-ASSURANCE-001',
            'MERCHANT-ASSURANCE-001',
            'HOTEL',
            100.00,
            'MXN',
            DATE '2026-09-10',
            repeat('e', 64)
        );

        RAISE EXCEPTION
            'FAIL 2: invalid country accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 2: invalid country rejected';
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
            currency,
            expense_date,
            input_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000001192',
            '00000000-0000-0000-0000-000000001101',
            'DEV-INVALID-VARIANT',
            'DEVELOPMENT',
            'FAM-ASSURANCE-A',
            'POLICY_REPLAY',
            'ORG-PROFILE-ASSURANCE-MX',
            'MX',
            'EMP-ASSURANCE-001',
            'MERCHANT-ASSURANCE-001',
            'HOTEL',
            100.00,
            'MXN',
            DATE '2026-09-10',
            repeat('f', 64)
        );

        RAISE EXCEPTION
            'FAIL 3: unsupported variant accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 3: unsupported variant rejected';
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
            '00000000-0000-0000-0000-000000001102',
            'COMPLIANT',
            'LOW',
            'SCREENING_COMPLETE',
            TRUE,
            'EXTREME',
            'Synthetic invalid severity.',
            'Synthetic assurance constraint test.'
        );

        RAISE EXCEPTION
            'FAIL 4: invalid miss severity accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 4: invalid miss severity rejected';
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
            '00000000-0000-0000-0000-000000001102',
            'COMPLIANT',
            'LOW',
            'SCREENING_COMPLETE',
            TRUE,
            'LOW',
            '   ',
            'Synthetic assurance constraint test.'
        );

        RAISE EXCEPTION
            'FAIL 5: blank severity rationale accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 5: blank severity rationale rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001102',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 6: self relationship accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 6: self relationship rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001104',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 7: cross-family relationship accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 7: cross-family relationship rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001105',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 8: cross-split relationship accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 8: cross-split relationship rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY[]::TEXT[],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 9: empty changed fields accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 9: empty changed fields rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY[]::TEXT[]
        );

        RAISE EXCEPTION
            'FAIL 10: change without outputs accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 10: change without outputs rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/business_purpose_declared'],
            'DECISION_MUST_REMAIN_STABLE',
            ARRAY['ROUTE']
        );

        RAISE EXCEPTION
            'FAIL 11: stable decision with changed outputs accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 11: contradictory stable effect rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'POLICY_REPLAY',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 12: unsupported relationship type accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 12: unsupported relationship type rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn'],
            'DECISION_MUST_CHANGE',
            ARRAY['FINANCIAL_AUTHORITY']
        );

        RAISE EXCEPTION
            'FAIL 13: unsupported changed output accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 13: unsupported changed output rejected';
    END;

    BEGIN
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
        )
        VALUES (
            '00000000-0000-0000-0000-000000001101',
            '00000000-0000-0000-0000-000000001103',
            '00000000-0000-0000-0000-000000001102',
            'FAM-ASSURANCE-A',
            'DEVELOPMENT',
            'COUNTERFACTUAL',
            ARRAY['/amount_mxn', NULL],
            'DECISION_MUST_CHANGE',
            ARRAY['COMPLIANCE']
        );

        RAISE EXCEPTION
            'FAIL 14: null changed field accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 14: null changed field rejected';
    END;
END
$tests$;

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
)
VALUES (
    '00000000-0000-0000-0000-000000001101',
    '00000000-0000-0000-0000-000000001103',
    '00000000-0000-0000-0000-000000001102',
    'FAM-ASSURANCE-A',
    'DEVELOPMENT',
    'COUNTERFACTUAL',
    ARRAY['/amount_mxn'],
    'DECISION_MUST_CHANGE',
    ARRAY['COMPLIANCE']
);

DO $$
DECLARE
    relationship_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO relationship_count
    FROM benchmark.case_relationships
    WHERE manifest_id =
        '00000000-0000-0000-0000-000000001101';

    IF relationship_count <> 1 THEN
        RAISE EXCEPTION
            'FAIL 15: valid relationship was not stored';
    END IF;

    RAISE NOTICE
        'PASS 15: valid scoped relationship accepted';
END
$$;

ROLLBACK;

\echo 'PASS: 15 benchmark assurance constraint tests completed'

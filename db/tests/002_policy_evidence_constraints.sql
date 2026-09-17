\set ON_ERROR_STOP on

BEGIN;

INSERT INTO core.organizations (
    organization_id,
    organization_code,
    legal_name,
    country_code,
    base_currency,
    time_zone
)
VALUES (
    '00000000-0000-4000-8000-000000000500',
    'POLICY_TEST',
    'Policy and Evidence Test Organization',
    'MX',
    'MXN',
    'America/Mexico_City'
);

INSERT INTO core.employees (
    employee_id,
    employee_ref,
    department,
    cost_center,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000501',
    'TEST-EMP-002',
    'FINANCE',
    'CC-TEST-002',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.merchants (
    merchant_id,
    merchant_key,
    canonical_name,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000502',
    'TEST-MERCHANT-002',
    'Comercio de Prueba 002',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000503',
    '00000000-0000-0000-0000-000000000501',
    'CONSTRAINT_TEST_002',
    'EXP-002',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.expense_versions (
    expense_id,
    version_no,
    expense_date,
    submitted_at,
    amount_mxn,
    merchant_id,
    merchant_name_raw,
    declared_category,
    receipt_state,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000503',
    1,
    DATE '2026-09-13',
    TIMESTAMPTZ '2026-09-14 12:00:00+00',
    500.00,
    '00000000-0000-0000-0000-000000000502',
    'Comercio de Prueba 002',
    'MEALS',
    'MISSING',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000512',
    '00000000-0000-0000-0000-000000000501',
    'CONSTRAINT_TEST_002',
    'EXP-003',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.expense_versions (
    expense_id,
    version_no,
    expense_date,
    submitted_at,
    amount_mxn,
    merchant_id,
    merchant_name_raw,
    declared_category,
    receipt_state,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000512',
    1,
    DATE '2026-09-13',
    TIMESTAMPTZ '2026-09-14 12:00:00+00',
    450.00,
    '00000000-0000-0000-0000-000000000502',
    'Comercio de Prueba 002',
    'MEALS',
    'MISSING',
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.policy_versions (
    policy_version_id,
    policy_code,
    version_label,
    effective_from,
    policy_hash,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000504',
    'CORPORATE_EXPENSE',
    'v1.0-test',
    DATE '2026-01-01',
    repeat('a', 64),
    '00000000-0000-4000-8000-000000000500'
);

INSERT INTO core.duplicate_observations (
    observation_id,
    expense_id,
    version_no,
    matched_expense_id,
    matched_version_no,
    signal_type,
    match_key,
    organization_id
)
VALUES (
    '00000000-0000-0000-0000-000000000505',
    '00000000-0000-0000-0000-000000000503',
    1,
    '00000000-0000-0000-0000-000000000512',
    1,
    'FIELD_MATCH',
    'TEST-MATCH-001',
    '00000000-0000-4000-8000-000000000500'
);

DO $tests$
BEGIN
    BEGIN
        INSERT INTO core.policy_versions (
            policy_version_id,
            policy_code,
            version_label,
            effective_from,
            policy_hash,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000506',
            'INVALID_HASH',
            'v1',
            DATE '2026-01-01',
            'abc',
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 1: invalid policy hash was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 1: invalid policy hash rejected';
    END;

    BEGIN
        INSERT INTO core.policy_versions (
            policy_version_id,
            policy_code,
            version_label,
            effective_from,
            effective_to,
            policy_hash,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000507',
            'INVALID_DATES',
            'v1',
            DATE '2026-02-01',
            DATE '2026-01-01',
            repeat('b', 64),
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 2: invalid policy dates were accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 2: invalid policy dates rejected';
    END;

    BEGIN
        INSERT INTO core.expense_evidence (
            evidence_id,
            expense_id,
            version_no,
            evidence_type,
            evidence_status,
            field_name,
            value_text,
            source_ref,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000508',
            '00000000-0000-0000-0000-000000000999',
            1,
            'DECLARATION',
            'OBSERVED',
            'business_purpose',
            'Prueba',
            'TEST-SOURCE',
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 3: orphan evidence was accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 3: orphan evidence rejected';
    END;

    BEGIN
        INSERT INTO core.expense_evidence (
            evidence_id,
            expense_id,
            version_no,
            evidence_type,
            evidence_status,
            field_name,
            value_text,
            source_ref,
            confidence,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000509',
            '00000000-0000-0000-0000-000000000503',
            1,
            'RECEIPT_FIELD',
            'AI_PROPOSED',
            'merchant_name',
            'Comercio',
            'TEST-SOURCE',
            1.10,
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 4: invalid confidence was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 4: invalid confidence rejected';
    END;

    BEGIN
        INSERT INTO core.duplicate_observations (
            observation_id,
            expense_id,
            version_no,
            matched_expense_id,
            matched_version_no,
            signal_type,
            match_key,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000510',
            '00000000-0000-0000-0000-000000000503',
            1,
            '00000000-0000-0000-0000-000000000503',
            1,
            'FIELD_MATCH',
            'SELF-MATCH',
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 5: self duplicate was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS 5: self duplicate rejected';
    END;

    BEGIN
        INSERT INTO core.duplicate_observations (
            observation_id,
            expense_id,
            version_no,
            matched_expense_id,
            matched_version_no,
            signal_type,
            match_key,
            organization_id
        )
        VALUES (
            '00000000-0000-0000-0000-000000000511',
            '00000000-0000-0000-0000-000000000503',
            1,
            '00000000-0000-0000-0000-000000000512',
            1,
            'FIELD_MATCH',
            'TEST-MATCH-001',
            '00000000-0000-4000-8000-000000000500'
        );

        RAISE EXCEPTION
            'FAIL 6: duplicate observation was accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'PASS 6: duplicate observation rejected';
    END;
END
$tests$;

ROLLBACK;

\echo 'PASS: 6 policy and evidence constraint tests completed'
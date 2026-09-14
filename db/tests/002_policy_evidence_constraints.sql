BEGIN;
INSERT INTO core.employees (
    employee_id,
    employee_ref,
    department,
    cost_center
)
VALUES (
    '00000000-0000-0000-0000-000000000501',
    'TEST-EMP-002',
    'FINANCE',
    'CC-TEST-002'
);
INSERT INTO core.merchants (
    merchant_id,
    merchant_key,
    canonical_name
)
VALUES (
    '00000000-0000-0000-0000-000000000502',
    'TEST-MERCHANT-002',
    'Comercio de Prueba 002'
);
INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref
)
VALUES (
    '00000000-0000-0000-0000-000000000503',
    '00000000-0000-0000-0000-000000000501',
    'CONSTRAINT_TEST_002',
    'EXP-002'
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
    receipt_state
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
    'MISSING'
);
INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref
)
VALUES (
    '00000000-0000-0000-0000-000000000512',
    '00000000-0000-0000-0000-000000000501',
    'CONSTRAINT_TEST_002',
    'EXP-003'
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
    receipt_state
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
    'MISSING'
);
INSERT INTO core.policy_versions (
    policy_version_id,
    policy_code,
    version_label,
    effective_from,
    policy_hash
)
VALUES (
    '00000000-0000-0000-0000-000000000504',
    'CORPORATE_EXPENSE',
    'v1.0-test',
    DATE '2026-01-01',
    repeat('a', 64)
);
INSERT INTO core.duplicate_observations (
    observation_id,
    expense_id,
    version_no,
    matched_expense_id,
    matched_version_no,
    signal_type,
    match_key
)
VALUES (
    '00000000-0000-0000-0000-000000000505',
    '00000000-0000-0000-0000-000000000503',
    1,
    '00000000-0000-0000-0000-000000000512',
    1,
    'FIELD_MATCH',
    'TEST-MATCH-001'
);
DO $tests$
BEGIN
    BEGIN
        INSERT INTO core.policy_versions (
            policy_version_id,
            policy_code,
            version_label,
            effective_from,
            policy_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000506',
            'INVALID_HASH',
            'v1',
            DATE '2026-01-01',
            'abc'
        );
        RAISE EXCEPTION 'FAIL 1';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 1: invalid policy hash rejected';
    END;
    BEGIN
        INSERT INTO core.policy_versions (
            policy_version_id,
            policy_code,
            version_label,
            effective_from,
            effective_to,
            policy_hash
        )
        VALUES (
            '00000000-0000-0000-0000-000000000507',
            'INVALID_DATES',
            'v1',
            DATE '2026-02-01',
            DATE '2026-01-01',
            repeat('b', 64)
        );
        RAISE EXCEPTION 'FAIL 2';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 2: invalid policy dates rejected';
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
            source_ref
        )
        VALUES (
            '00000000-0000-0000-0000-000000000508',
            '00000000-0000-0000-0000-000000000999',
            1,
            'DECLARATION',
            'OBSERVED',
            'business_purpose',
            'Prueba',
            'TEST-SOURCE'
        );
        RAISE EXCEPTION 'FAIL 3';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'PASS 3: orphan evidence rejected';
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
            confidence
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
            1.10
        );
        RAISE EXCEPTION 'FAIL 4';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 4: invalid confidence rejected';
    END;
    BEGIN
        INSERT INTO core.duplicate_observations (
            observation_id,
            expense_id,
            version_no,
            matched_expense_id,
            matched_version_no,
            signal_type,
            match_key
        )
        VALUES (
            '00000000-0000-0000-0000-000000000510',
            '00000000-0000-0000-0000-000000000503',
            1,
            '00000000-0000-0000-0000-000000000503',
            1,
            'FIELD_MATCH',
            'SELF-MATCH'
        );
        RAISE EXCEPTION 'FAIL 5';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 5: self duplicate rejected';
    END;
    BEGIN
        INSERT INTO core.duplicate_observations (
            observation_id,
            expense_id,
            version_no,
            matched_expense_id,
            matched_version_no,
            signal_type,
            match_key
        )
        VALUES (
            '00000000-0000-0000-0000-000000000511',
            '00000000-0000-0000-0000-000000000503',
            1,
            '00000000-0000-0000-0000-000000000512',
            1,
            'FIELD_MATCH',
            'TEST-MATCH-001'
        );
        RAISE EXCEPTION 'FAIL 6';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 6: duplicate observation rejected';
    END;
END
$tests$;
ROLLBACK;
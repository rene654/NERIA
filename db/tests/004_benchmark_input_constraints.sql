BEGIN;
INSERT INTO benchmark.dataset_manifests (
    manifest_id,
    dataset_name,
    dataset_version,
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
    '00000000-0000-0000-0000-000000000701',
    'NERIA_INPUT_TEST',
    'v0.1',
    'manual-test',
    20260915,
    'CORPORATE_EXPENSE',
    'v1.0',
    '004',
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
    employee_key,
    merchant_key,
    category_hint,
    amount_mxn,
    expense_date,
    input_hash
)
VALUES (
    '00000000-0000-0000-0000-000000000702',
    '00000000-0000-0000-0000-000000000701',
    'DEV-INPUT-TEST-001',
    'DEVELOPMENT',
    'FAM-INPUT-TEST-001',
    'BASELINE',
    'EMP-INPUT-001',
    'MERCHANT-INPUT-001',
    'HOTEL',
    12000.00,
    DATE '2026-09-10',
    repeat('a', 64)
);
INSERT INTO benchmark.case_inputs (
    case_id,
    submitted_at,
    receipt_state,
    receipt_fixture_ref,
    receipt_total_mxn,
    business_purpose_declared,
    category_context
)
VALUES (
    '00000000-0000-0000-0000-000000000702',
    TIMESTAMPTZ '2026-09-15 12:00:00+00',
    'PRESENT_READABLE',
    'RECEIPT-TEST-001',
    12000.00,
    'Visita a cliente',
    '{"stay_nights": 3}'::JSONB
);
DO $tests$
BEGIN
    BEGIN
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000999',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'MISSING',
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 1';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'PASS 1: orphan case input rejected';
    END;
    BEGIN
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            receipt_fixture_ref,
            receipt_total_mxn,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'PRESENT_READABLE',
            'RECEIPT-DUPLICATE',
            12000.00,
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 2';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 2: second input for same case rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'INVALID',
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 3';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 3: invalid receipt state rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            receipt_fixture_ref,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'MISSING',
            'RECEIPT-SHOULD-NOT-EXIST',
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 4';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 4: missing receipt with reference rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            receipt_fixture_ref,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'PRESENT_READABLE',
            'RECEIPT-WITHOUT-TOTAL',
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 5';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 5: readable receipt without total rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            receipt_fixture_ref,
            receipt_total_mxn,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'PRESENT_UNREADABLE',
            'RECEIPT-UNREADABLE',
            12000.00,
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 6';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 6: unreadable receipt with total rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            receipt_fixture_ref,
            receipt_total_mxn,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'PRESENT_READABLE',
            'RECEIPT-NEGATIVE',
            -1.00,
            '{}'::JSONB
        );
        RAISE EXCEPTION 'FAIL 7';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 7: negative receipt total rejected';
    END;
    BEGIN
        DELETE FROM benchmark.case_inputs
        WHERE case_id = '00000000-0000-0000-0000-000000000702';
        INSERT INTO benchmark.case_inputs (
            case_id,
            submitted_at,
            receipt_state,
            category_context
        )
        VALUES (
            '00000000-0000-0000-0000-000000000702',
            TIMESTAMPTZ '2026-09-15 12:00:00+00',
            'MISSING',
            '[]'::JSONB
        );
        RAISE EXCEPTION 'FAIL 8';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 8: non-object category context rejected';
    END;
END
$tests$;
ROLLBACK;
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
VALUES
(
    '90000000-0000-4000-8000-000000000001',
    'INTAKE_TEST_A',
    'Intake Test A',
    'MX',
    'MXN',
    'America/Mexico_City'
),
(
    '90000000-0000-4000-8000-000000000002',
    'INTAKE_TEST_B',
    'Intake Test B',
    'MX',
    'MXN',
    'America/Mexico_City'
);
INSERT INTO core.expense_intakes (
    intake_id,
    organization_id,
    source_system,
    external_ref,
    request_id,
    contract_version,
    payload,
    payload_hash
)
VALUES (
    '91000000-0000-4000-8000-000000000001',
    '90000000-0000-4000-8000-000000000001',
    'API',
    'EXP-001',
    'request-001',
    'v1',
    '{"amount_mxn":"900.00"}'::JSONB,
    repeat('a', 64)
);
DO $$
BEGIN
    BEGIN
        INSERT INTO core.expense_intakes (
            intake_id,
            organization_id,
            source_system,
            external_ref,
            request_id,
            contract_version,
            payload,
            payload_hash
        )
        VALUES (
            '91000000-0000-4000-8000-000000000002',
            '90000000-0000-4000-8000-000000000001',
            'API',
            'EXP-001',
            'request-002',
            'v1',
            '{}'::JSONB,
            repeat('b', 64)
        );
        RAISE EXCEPTION
            'Duplicate source reference was accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'PASS: duplicate source reference rejected';
    END;
END
$$;
INSERT INTO core.expense_intakes (
    intake_id,
    organization_id,
    source_system,
    external_ref,
    request_id,
    contract_version,
    payload,
    payload_hash
)
VALUES (
    '91000000-0000-4000-8000-000000000003',
    '90000000-0000-4000-8000-000000000002',
    'API',
    'EXP-001',
    'request-003',
    'v1',
    '{"amount_mxn":"900.00"}'::JSONB,
    repeat('c', 64)
);
DO $$
BEGIN
    BEGIN
        INSERT INTO core.expense_intakes (
            intake_id,
            organization_id,
            source_system,
            external_ref,
            request_id,
            contract_version,
            payload,
            payload_hash
        )
        VALUES (
            '91000000-0000-4000-8000-000000000004',
            '90000000-0000-4000-8000-000000000001',
            'API',
            'EXP-ARRAY',
            'request-004',
            'v1',
            '[]'::JSONB,
            repeat('d', 64)
        );
        RAISE EXCEPTION
            'Array payload was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS: non-object payload rejected';
    END;
END
$$;
DO $$
BEGIN
    BEGIN
        INSERT INTO core.expense_intakes (
            intake_id,
            organization_id,
            source_system,
            external_ref,
            request_id,
            contract_version,
            payload,
            payload_hash
        )
        VALUES (
            '91000000-0000-4000-8000-000000000005',
            '90000000-0000-4000-8000-000000000001',
            'API',
            'EXP-HASH',
            'request-005',
            'v1',
            '{}'::JSONB,
            'bad-hash'
        );
        RAISE EXCEPTION
            'Invalid hash was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'PASS: invalid hash rejected';
    END;
END
$$;
DO $$
DECLARE
    intake_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO intake_count
    FROM core.expense_intakes
    WHERE organization_id IN (
        '90000000-0000-4000-8000-000000000001',
        '90000000-0000-4000-8000-000000000002'
    );
    IF intake_count <> 2 THEN
        RAISE EXCEPTION
            'Expected 2 accepted intakes, found %',
            intake_count;
    END IF;
    RAISE NOTICE
        'PASS: tenant-scoped intake records accepted';
END
$$;
ROLLBACK;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM core.expense_intakes
        WHERE organization_id IN (
            '90000000-0000-4000-8000-000000000001',
            '90000000-0000-4000-8000-000000000002'
        )
    ) THEN
        RAISE EXCEPTION
            'Test fixtures survived rollback';
    END IF;
    RAISE NOTICE
        'PASS: test fixtures rolled back';
END
$$;

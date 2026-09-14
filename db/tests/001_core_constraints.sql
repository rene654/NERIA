\set ON_ERROR_STOP on
BEGIN;
-- Datos válidos temporales para ejecutar las pruebas.
INSERT INTO core.employees (
    employee_id,
    employee_ref,
    department,
    cost_center
)
VALUES (
    '00000000-0000-0000-0000-000000000101',
    'TEST-EMP-001',
    'FINANCE',
    'CC-TEST'
);
INSERT INTO core.merchants (
    merchant_id,
    merchant_key,
    canonical_name
)
VALUES (
    '00000000-0000-0000-0000-000000000201',
    'TEST-HOTEL',
    'Hotel de Prueba'
);
INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref
)
VALUES (
    '00000000-0000-0000-0000-000000000301',
    '00000000-0000-0000-0000-000000000101',
    'CONSTRAINT_TEST',
    'EXP-001'
);
INSERT INTO core.expense_versions (
    expense_id,
    version_no,
    expense_date,
    submitted_at,
    amount_mxn,
    currency,
    merchant_id,
    merchant_name_raw,
    declared_category,
    validated_category,
    business_purpose_declared,
    receipt_state
)
VALUES (
    '00000000-0000-0000-0000-000000000301',
    1,
    DATE '2026-09-13',
    TIMESTAMPTZ '2026-09-14 12:00:00+00',
    12000.00,
    'MXN',
    '00000000-0000-0000-0000-000000000201',
    'Hotel de Prueba',
    'HOTEL',
    'HOTEL',
    'Visita a cliente',
    'PRESENT_READABLE'
);
INSERT INTO core.receipt_documents (
    document_id,
    expense_id,
    version_no,
    source_kind,
    fixture_ref,
    is_primary
)
VALUES (
    '00000000-0000-0000-0000-000000000401',
    '00000000-0000-0000-0000-000000000301',
    1,
    'STRUCTURED_FIXTURE',
    'FIXTURE-001',
    TRUE
);
DO $tests$
BEGIN
    -- 1. Referencia externa duplicada.
    BEGIN
        INSERT INTO core.expenses (
            expense_id,
            employee_id,
            source_system,
            external_ref
        )
        VALUES (
            '00000000-0000-0000-0000-000000000302',
            '00000000-0000-0000-0000-000000000101',
            'CONSTRAINT_TEST',
            'EXP-001'
        );
        RAISE EXCEPTION 'FAIL 1: duplicate reference was accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 1: duplicate reference rejected';
    END;
    -- 2. Empleado inexistente.
    BEGIN
        INSERT INTO core.expenses (
            expense_id,
            employee_id,
            source_system,
            external_ref
        )
        VALUES (
            '00000000-0000-0000-0000-000000000303',
            '00000000-0000-0000-0000-000000000999',
            'CONSTRAINT_TEST',
            'EXP-ORPHAN'
        );
        RAISE EXCEPTION 'FAIL 2: orphan expense was accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE 'PASS 2: orphan expense rejected';
    END;
    -- 3. Número de versión inválido.
    BEGIN
        INSERT INTO core.expense_versions (
            expense_id,
            version_no,
            expense_date,
            submitted_at,
            amount_mxn,
            merchant_name_raw,
            declared_category,
            receipt_state
        )
        VALUES (
            '00000000-0000-0000-0000-000000000301',
            0,
            DATE '2026-09-13',
            TIMESTAMPTZ '2026-09-14 12:00:00+00',
            100.00,
            'Hotel de Prueba',
            'HOTEL',
            'MISSING'
        );
        RAISE EXCEPTION 'FAIL 3: invalid version was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 3: invalid version rejected';
    END;
    -- 4. Importe igual a cero.
    BEGIN
        INSERT INTO core.expense_versions (
            expense_id,
            version_no,
            expense_date,
            submitted_at,
            amount_mxn,
            merchant_name_raw,
            declared_category,
            receipt_state
        )
        VALUES (
            '00000000-0000-0000-0000-000000000301',
            2,
            DATE '2026-09-13',
            TIMESTAMPTZ '2026-09-14 12:00:00+00',
            0.00,
            'Hotel de Prueba',
            'HOTEL',
            'MISSING'
        );
        RAISE EXCEPTION 'FAIL 4: zero amount was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 4: zero amount rejected';
    END;
    -- 5. Moneda fuera del MVP.
    BEGIN
        INSERT INTO core.expense_versions (
            expense_id,
            version_no,
            expense_date,
            submitted_at,
            amount_mxn,
            currency,
            merchant_name_raw,
            declared_category,
            receipt_state
        )
        VALUES (
            '00000000-0000-0000-0000-000000000301',
            2,
            DATE '2026-09-13',
            TIMESTAMPTZ '2026-09-14 12:00:00+00',
            100.00,
            'USD',
            'Hotel de Prueba',
            'HOTEL',
            'MISSING'
        );
        RAISE EXCEPTION 'FAIL 5: unsupported currency was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 5: unsupported currency rejected';
    END;
    -- 6. Fecha del gasto posterior a la presentación.
    BEGIN
        INSERT INTO core.expense_versions (
            expense_id,
            version_no,
            expense_date,
            submitted_at,
            amount_mxn,
            merchant_name_raw,
            declared_category,
            receipt_state
        )
        VALUES (
            '00000000-0000-0000-0000-000000000301',
            2,
            DATE '2026-09-15',
            TIMESTAMPTZ '2026-09-14 12:00:00+00',
            100.00,
            'Hotel de Prueba',
            'HOTEL',
            'MISSING'
        );
        RAISE EXCEPTION 'FAIL 6: future expense date was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 6: future expense date rejected';
    END;
    -- 7. Categoría inexistente.
    BEGIN
        INSERT INTO core.expense_versions (
            expense_id,
            version_no,
            expense_date,
            submitted_at,
            amount_mxn,
            merchant_name_raw,
            declared_category,
            receipt_state
        )
        VALUES (
            '00000000-0000-0000-0000-000000000301',
            2,
            DATE '2026-09-13',
            TIMESTAMPTZ '2026-09-14 12:00:00+00',
            100.00,
            'Hotel de Prueba',
            'TRAVEL',
            'MISSING'
        );
        RAISE EXCEPTION 'FAIL 7: invalid category was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 7: invalid category rejected';
    END;
    -- 8. Archivo sin ubicación ni huella digital.
    BEGIN
        INSERT INTO core.receipt_documents (
            document_id,
            expense_id,
            version_no,
            source_kind,
            is_primary
        )
        VALUES (
            '00000000-0000-0000-0000-000000000402',
            '00000000-0000-0000-0000-000000000301',
            1,
            'FILE',
            FALSE
        );
        RAISE EXCEPTION 'FAIL 8: incomplete file was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'PASS 8: incomplete file rejected';
    END;
    -- 9. Dos comprobantes principales para la misma versión.
    BEGIN
        INSERT INTO core.receipt_documents (
            document_id,
            expense_id,
            version_no,
            source_kind,
            fixture_ref,
            is_primary
        )
        VALUES (
            '00000000-0000-0000-0000-000000000403',
            '00000000-0000-0000-0000-000000000301',
            1,
            'STRUCTURED_FIXTURE',
            'FIXTURE-002',
            TRUE
        );
        RAISE EXCEPTION 'FAIL 9: second primary receipt was accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE 'PASS 9: second primary receipt rejected';
    END;
END
$tests$;
ROLLBACK;
\echo 'PASS: 9 core constraint tests completed'
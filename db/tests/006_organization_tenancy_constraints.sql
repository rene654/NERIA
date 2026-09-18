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
    '00000000-0000-4000-8000-000000000601',
    'TENANT_A',
    'Synthetic Organization A',
    'MX',
    'MXN',
    'America/Mexico_City'
),
(
    '00000000-0000-4000-8000-000000000602',
    'TENANT_B',
    'Synthetic Organization B',
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
VALUES
(
    '00000000-0000-4000-8000-000000000611',
    'EMP-SHARED',
    'FINANCE',
    'CC-100',
    '00000000-0000-4000-8000-000000000601'
),
(
    '00000000-0000-4000-8000-000000000612',
    'EMP-SHARED',
    'FINANCE',
    'CC-100',
    '00000000-0000-4000-8000-000000000602'
);

INSERT INTO core.merchants (
    merchant_id,
    merchant_key,
    canonical_name,
    organization_id
)
VALUES
(
    '00000000-0000-4000-8000-000000000621',
    'MERCHANT-SHARED',
    'Synthetic Merchant A',
    '00000000-0000-4000-8000-000000000601'
),
(
    '00000000-0000-4000-8000-000000000622',
    'MERCHANT-SHARED',
    'Synthetic Merchant B',
    '00000000-0000-4000-8000-000000000602'
);

INSERT INTO core.expenses (
    expense_id,
    employee_id,
    source_system,
    external_ref,
    organization_id
)
VALUES
(
    '00000000-0000-4000-8000-000000000631',
    '00000000-0000-4000-8000-000000000611',
    'SYNTHETIC_SOURCE',
    'EXP-SHARED',
    '00000000-0000-4000-8000-000000000601'
),
(
    '00000000-0000-4000-8000-000000000632',
    '00000000-0000-4000-8000-000000000612',
    'SYNTHETIC_SOURCE',
    'EXP-SHARED',
    '00000000-0000-4000-8000-000000000602'
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
    receipt_state,
    organization_id
)
VALUES
(
    '00000000-0000-4000-8000-000000000631',
    1,
    (CURRENT_TIMESTAMP AT TIME ZONE 'America/Mexico_City')::DATE,
    CURRENT_TIMESTAMP,
    1000.00,
    'MXN',
    '00000000-0000-4000-8000-000000000621',
    'Synthetic Merchant A',
    'MEALS',
    'MEALS',
    'Synthetic tenancy test',
    'MISSING',
    '00000000-0000-4000-8000-000000000601'
),
(
    '00000000-0000-4000-8000-000000000632',
    1,
    (CURRENT_TIMESTAMP AT TIME ZONE 'America/Mexico_City')::DATE,
    CURRENT_TIMESTAMP,
    1000.00,
    'MXN',
    '00000000-0000-4000-8000-000000000622',
    'Synthetic Merchant B',
    'MEALS',
    'MEALS',
    'Synthetic tenancy test',
    'MISSING',
    '00000000-0000-4000-8000-000000000602'
);

INSERT INTO core.policy_versions (
    policy_version_id,
    policy_code,
    version_label,
    effective_from,
    policy_hash,
    organization_id
)
VALUES
(
    '00000000-0000-4000-8000-000000000671',
    'EXPENSE_POLICY',
    'v1.0',
    (CURRENT_TIMESTAMP AT TIME ZONE 'America/Mexico_City')::DATE,
    repeat('a', 64),
    '00000000-0000-4000-8000-000000000601'
),
(
    '00000000-0000-4000-8000-000000000672',
    'EXPENSE_POLICY',
    'v1.0',
    (CURRENT_TIMESTAMP AT TIME ZONE 'America/Mexico_City')::DATE,
    repeat('b', 64),
    '00000000-0000-4000-8000-000000000602'
);

DO $$
BEGIN
    IF (
        SELECT COUNT(*)
        FROM core.employees
        WHERE employee_ref = 'EMP-SHARED'
    ) <> 2 THEN
        RAISE EXCEPTION
            'FAIL 1: tenant-scoped employee references rejected';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM core.merchants
        WHERE merchant_key = 'MERCHANT-SHARED'
    ) <> 2 THEN
        RAISE EXCEPTION
            'FAIL 1: tenant-scoped merchant keys rejected';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM core.expenses
        WHERE external_ref = 'EXP-SHARED'
    ) <> 2 THEN
        RAISE EXCEPTION
            'FAIL 1: tenant-scoped expense references rejected';
    END IF;

    IF (
        SELECT COUNT(*)
        FROM core.policy_versions
        WHERE policy_code = 'EXPENSE_POLICY'
          AND version_label = 'v1.0'
    ) <> 2 THEN
        RAISE EXCEPTION
            'FAIL 1: tenant-scoped policy versions rejected';
    END IF;

    RAISE NOTICE
        'PASS 1: natural keys are isolated by organization';
END
$$;

DO $$
BEGIN
    BEGIN
        INSERT INTO core.employees (
            employee_id,
            employee_ref,
            department,
            cost_center,
            organization_id
        )
        VALUES (
            '00000000-0000-4000-8000-000000000619',
            'EMP-UNKNOWN-ORG',
            'FINANCE',
            'CC-999',
            '00000000-0000-4000-8000-000000000699'
        );

        RAISE EXCEPTION
            'FAIL 2: employee with unknown organization accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 2: unknown organization rejected';
    END;

    BEGIN
        INSERT INTO core.employees (
            employee_id,
            employee_ref,
            department,
            cost_center,
            organization_id
        )
        VALUES (
            '00000000-0000-4000-8000-000000000618',
            'EMP-SHARED',
            'FINANCE',
            'CC-101',
            '00000000-0000-4000-8000-000000000601'
        );

        RAISE EXCEPTION
            'FAIL 3: duplicate employee reference accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'PASS 3: duplicate employee within organization rejected';
    END;

    BEGIN
        INSERT INTO core.expenses (
            expense_id,
            employee_id,
            source_system,
            external_ref,
            organization_id
        )
        VALUES (
            '00000000-0000-4000-8000-000000000639',
            '00000000-0000-4000-8000-000000000611',
            'SYNTHETIC_SOURCE',
            'EXP-CROSS-EMPLOYEE',
            '00000000-0000-4000-8000-000000000602'
        );

        RAISE EXCEPTION
            'FAIL 4: cross-organization employee accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 4: cross-organization employee rejected';
    END;

    BEGIN
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
            receipt_state,
            organization_id
        )
        VALUES (
            '00000000-0000-4000-8000-000000000632',
            2,
            (CURRENT_TIMESTAMP AT TIME ZONE 'America/Mexico_City')::DATE,
            CURRENT_TIMESTAMP,
            1000.00,
            'MXN',
            '00000000-0000-4000-8000-000000000621',
            'Cross-Tenant Merchant',
            'MEALS',
            'MISSING',
            '00000000-0000-4000-8000-000000000602'
        );

        RAISE EXCEPTION
            'FAIL 5: cross-organization merchant accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 5: cross-organization merchant rejected';
    END;

    BEGIN
        INSERT INTO core.receipt_documents (
            document_id,
            expense_id,
            version_no,
            source_kind,
            fixture_ref,
            organization_id
        )
        VALUES (
            '00000000-0000-4000-8000-000000000641',
            '00000000-0000-4000-8000-000000000631',
            1,
            'STRUCTURED_FIXTURE',
            'cross-tenant-receipt.json',
            '00000000-0000-4000-8000-000000000602'
        );

        RAISE EXCEPTION
            'FAIL 6: cross-organization receipt accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 6: cross-organization receipt rejected';
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
            '00000000-0000-4000-8000-000000000651',
            '00000000-0000-4000-8000-000000000631',
            1,
            'SYSTEM_DERIVED',
            'OBSERVED',
            'amount_mxn',
            '1000.00',
            'synthetic-test',
            '00000000-0000-4000-8000-000000000602'
        );

        RAISE EXCEPTION
            'FAIL 7: cross-organization evidence accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 7: cross-organization evidence rejected';
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
            '00000000-0000-4000-8000-000000000661',
            '00000000-0000-4000-8000-000000000631',
            1,
            '00000000-0000-4000-8000-000000000632',
            1,
            'FIELD_MATCH',
            'cross-tenant-match',
            '00000000-0000-4000-8000-000000000601'
        );

        RAISE EXCEPTION
            'FAIL 8: cross-organization duplicate match accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'PASS 8: cross-organization duplicate match rejected';
    END;
END
$$;

ROLLBACK;

\echo 'PASS: 8 organization tenancy constraint tests completed'
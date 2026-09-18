BEGIN;
CREATE SCHEMA IF NOT EXISTS meta;
CREATE TABLE IF NOT EXISTS meta.schema_migrations (
    migration_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '001'
    ) THEN
        RAISE EXCEPTION 'Migration 001 is already applied';
    END IF;
END
$$;
CREATE SCHEMA core;
CREATE TABLE core.employees (
    employee_id UUID PRIMARY KEY,
    employee_ref TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    cost_center TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE core.merchants (
    merchant_id UUID PRIMARY KEY,
    merchant_key TEXT NOT NULL UNIQUE,
    canonical_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE core.expenses (
    expense_id UUID PRIMARY KEY,
    employee_id UUID NOT NULL
        REFERENCES core.employees(employee_id),
    source_system TEXT NOT NULL,
    external_ref TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'RESOLVED', 'WITHDRAWN')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_expense_source_reference
        UNIQUE (source_system, external_ref)
);
CREATE TABLE core.expense_versions (
    expense_id UUID NOT NULL
        REFERENCES core.expenses(expense_id),
    version_no INTEGER NOT NULL
        CHECK (version_no > 0),
    expense_date DATE NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    amount_mxn NUMERIC(12, 2) NOT NULL
        CHECK (amount_mxn > 0),
    currency TEXT NOT NULL DEFAULT 'MXN'
        CHECK (currency = 'MXN'),
    merchant_id UUID
        REFERENCES core.merchants(merchant_id),
    merchant_name_raw TEXT NOT NULL,
    declared_category TEXT NOT NULL
        CHECK (
            declared_category IN (
                'HOTEL',
                'MEALS',
                'TRANSPORTATION',
                'AIRFARE',
                'SOFTWARE',
                'OFFICE_SUPPLIES',
                'UNKNOWN'
            )
        ),
    validated_category TEXT
        CHECK (
            validated_category IS NULL
            OR validated_category IN (
                'HOTEL',
                'MEALS',
                'TRANSPORTATION',
                'AIRFARE',
                'SOFTWARE',
                'OFFICE_SUPPLIES'
            )
        ),
    business_purpose_declared TEXT,
    receipt_state TEXT NOT NULL
        CHECK (
            receipt_state IN (
                'MISSING',
                'PRESENT_READABLE',
                'PRESENT_UNREADABLE',
                'UNSUPPORTED'
            )
        ),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (expense_id, version_no),
    CONSTRAINT chk_expense_date_not_future
        CHECK (
            expense_date <=
            (submitted_at AT TIME ZONE 'America/Mexico_City')::DATE
        )
);
CREATE TABLE core.receipt_documents (
    document_id UUID PRIMARY KEY,
    expense_id UUID NOT NULL,
    version_no INTEGER NOT NULL,
    source_kind TEXT NOT NULL
        CHECK (
            source_kind IN ('FILE', 'STRUCTURED_FIXTURE')
        ),
    storage_uri TEXT,
    fixture_ref TEXT,
    file_sha256 CHAR(64),
    mime_type TEXT,
    page_count INTEGER
        CHECK (page_count IS NULL OR page_count > 0),
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_receipt_expense_version
        FOREIGN KEY (expense_id, version_no)
        REFERENCES core.expense_versions(expense_id, version_no),
    CONSTRAINT chk_receipt_source
        CHECK (
            (
                source_kind = 'FILE'
                AND storage_uri IS NOT NULL
                AND file_sha256 ~ '^[0-9a-fA-F]{64}$'
                AND fixture_ref IS NULL
            )
            OR
            (
                source_kind = 'STRUCTURED_FIXTURE'
                AND fixture_ref IS NOT NULL
                AND storage_uri IS NULL
                AND file_sha256 IS NULL
            )
        )
);
CREATE UNIQUE INDEX uq_primary_receipt_per_version
    ON core.receipt_documents(expense_id, version_no)
    WHERE is_primary = TRUE;
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '001',
    'Create core expense data foundation'
);
COMMIT;

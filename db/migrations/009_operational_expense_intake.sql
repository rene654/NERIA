BEGIN;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '009'
    ) THEN
        RAISE EXCEPTION 'Migration 009 is already applied';
    END IF;
END
$$;
CREATE TABLE core.expense_intakes (
    intake_id UUID PRIMARY KEY,
    organization_id UUID NOT NULL
        REFERENCES core.organizations(
            organization_id
        ),
    source_system TEXT NOT NULL
        CHECK (
            length(trim(source_system))
            BETWEEN 1 AND 100
        ),
    external_ref TEXT NOT NULL
        CHECK (
            length(trim(external_ref))
            BETWEEN 1 AND 200
        ),
    request_id TEXT NOT NULL
        CHECK (
            request_id ~
            '^[A-Za-z0-9._:-]{1,128}$'
        ),
    contract_version TEXT NOT NULL
        CHECK (
            length(trim(contract_version)) > 0
        ),
    payload JSONB NOT NULL
        CHECK (
            jsonb_typeof(payload) = 'object'
        ),
    payload_hash CHAR(64) NOT NULL
        CHECK (
            payload_hash ~
            '^[0-9a-fA-F]{64}$'
        ),
    intake_status TEXT NOT NULL
        DEFAULT 'RECEIVED'
        CHECK (
            intake_status IN (
                'RECEIVED',
                'NORMALIZED'
            )
        ),
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_expense_intake_source
        UNIQUE (
            organization_id,
            source_system,
            external_ref
        )
);
CREATE INDEX idx_expense_intakes_request
    ON core.expense_intakes (
        organization_id,
        request_id
    );
CREATE INDEX idx_expense_intakes_created
    ON core.expense_intakes (
        organization_id,
        created_at
    );
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '009',
    'Add persistent operational expense intake'
);
COMMIT;

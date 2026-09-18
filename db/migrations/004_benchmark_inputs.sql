BEGIN;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '004'
    ) THEN
        RAISE EXCEPTION 'Migration 004 is already applied';
    END IF;
END
$$;
CREATE TABLE benchmark.case_inputs (
    case_id UUID PRIMARY KEY
        REFERENCES benchmark.cases(case_id)
        ON DELETE CASCADE,
    submitted_at TIMESTAMPTZ NOT NULL,
    receipt_state TEXT NOT NULL
        CHECK (
            receipt_state IN (
                'MISSING',
                'PRESENT_READABLE',
                'PRESENT_UNREADABLE',
                'UNSUPPORTED'
            )
        ),
    receipt_fixture_ref TEXT,
    receipt_total_mxn NUMERIC(12, 2)
        CHECK (
            receipt_total_mxn IS NULL
            OR receipt_total_mxn >= 0
        ),
    business_purpose_declared TEXT,
    category_context JSONB NOT NULL
        DEFAULT '{}'::JSONB
        CHECK (
            jsonb_typeof(category_context) = 'object'
        ),
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_receipt_input_consistency
        CHECK (
            (
                receipt_state = 'MISSING'
                AND receipt_fixture_ref IS NULL
                AND receipt_total_mxn IS NULL
            )
            OR
            (
                receipt_state = 'PRESENT_READABLE'
                AND receipt_fixture_ref IS NOT NULL
                AND receipt_total_mxn IS NOT NULL
            )
            OR
            (
                receipt_state IN (
                    'PRESENT_UNREADABLE',
                    'UNSUPPORTED'
                )
                AND receipt_fixture_ref IS NOT NULL
                AND receipt_total_mxn IS NULL
            )
        )
);
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '004',
    'Add structured benchmark case inputs'
);
COMMIT;
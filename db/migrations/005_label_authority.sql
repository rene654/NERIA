BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '005'
    ) THEN
        RAISE EXCEPTION 'Migration 005 is already applied';
    END IF;
END
$$;

ALTER TABLE benchmark.label_rules
ADD COLUMN rule_version TEXT NOT NULL DEFAULT 'v1.0';

ALTER TABLE benchmark.label_rules
ADD CONSTRAINT chk_label_rule_version
CHECK (length(trim(rule_version)) > 0);

CREATE TABLE benchmark.label_actions (
    case_id UUID NOT NULL
        REFERENCES benchmark.labels(case_id)
        ON DELETE CASCADE,
    action_code TEXT NOT NULL
        CHECK (
            action_code IN (
                'RECORD_SCREENING_RESULT',
                'REQUEST_INFORMATION',
                'ROUTE_TO_HUMAN_REVIEW',
                'RETRY_TECHNICAL_PROCESSING',
                'CREATE_TECHNICAL_ALERT',
                'RECORD_NOT_ADMITTED'
            )
        ),
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (case_id, action_code)
);

INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '005',
    'Add rule versions and permitted benchmark actions'
);

COMMIT;
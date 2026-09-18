BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '008'
    ) THEN
        RAISE EXCEPTION 'Migration 008 is already applied';
    END IF;
END
$$;

ALTER TABLE benchmark.label_rules
DROP CONSTRAINT label_rules_expected_state_check;

ALTER TABLE benchmark.label_rules
ADD CONSTRAINT chk_label_rule_expected_state
CHECK (
    expected_state IN (
        'PASS',
        'VIOLATION',
        'SIGNAL',
        'PENDING',
        'NOT_APPLICABLE',
        'CONTROL',
        'INVALID_INPUT',
        'OUT_OF_SCOPE',
        'ACTION_DENIED',
        'TECHNICAL_ERROR'
    )
);

ALTER TABLE benchmark.labels
DROP CONSTRAINT labels_expected_route_check;

ALTER TABLE benchmark.labels
ADD CONSTRAINT chk_label_expected_route
CHECK (
    expected_route IN (
        'SCREENING_COMPLETE',
        'NEEDS_INFORMATION',
        'HUMAN_REVIEW',
        'POLICY_CLARIFICATION',
        'SYSTEM_RECOVERY',
        'NOT_ADMITTED'
    )
);

ALTER TABLE benchmark.label_actions
DROP CONSTRAINT label_actions_action_code_check;

ALTER TABLE benchmark.label_actions
ADD CONSTRAINT chk_label_action_code
CHECK (
    action_code IN (
        'RECORD_SCREENING_RESULT',
        'REQUEST_INFORMATION',
        'REQUEST_POLICY_CLARIFICATION',
        'ROUTE_TO_HUMAN_REVIEW',
        'RETRY_TECHNICAL_PROCESSING',
        'CREATE_TECHNICAL_ALERT',
        'RECORD_NOT_ADMITTED'
    )
);

UPDATE benchmark.label_rules
SET expected_state = 'CONTROL'
WHERE rule_code = 'R07'
  AND expected_state = 'SIGNAL';

INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '008',
    'Align benchmark rule outcomes and routing vocabulary'
);

COMMIT;

BEGIN;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '002'
    ) THEN
        RAISE EXCEPTION 'Migration 002 is already applied';
    END IF;
END
$$;
CREATE TABLE core.policy_versions (
    policy_version_id UUID PRIMARY KEY,
    policy_code TEXT NOT NULL,
    version_label TEXT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    policy_hash CHAR(64) NOT NULL
        CHECK (policy_hash ~ '^[0-9a-fA-F]{64}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_policy_version
        UNIQUE (policy_code, version_label),
    CONSTRAINT chk_policy_dates
        CHECK (
            effective_to IS NULL
            OR effective_to >= effective_from
        )
);
CREATE TABLE core.expense_evidence (
    evidence_id UUID PRIMARY KEY,
    expense_id UUID NOT NULL,
    version_no INTEGER NOT NULL,
    evidence_type TEXT NOT NULL
        CHECK (
            evidence_type IN (
                'DECLARATION',
                'RECEIPT_FIELD',
                'SYSTEM_DERIVED',
                'HUMAN_CONFIRMATION',
                'EXTERNAL_DOCUMENT'
            )
        ),
    evidence_status TEXT NOT NULL
        CHECK (
            evidence_status IN (
                'OBSERVED',
                'AI_PROPOSED',
                'HUMAN_CONFIRMED'
            )
        ),
    field_name TEXT NOT NULL,
    value_text TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    confidence NUMERIC(5, 4)
        CHECK (
            confidence IS NULL
            OR confidence BETWEEN 0 AND 1
        ),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_evidence_expense_version
        FOREIGN KEY (expense_id, version_no)
        REFERENCES core.expense_versions(expense_id, version_no)
);
CREATE TABLE core.duplicate_observations (
    observation_id UUID PRIMARY KEY,
    expense_id UUID NOT NULL,
    version_no INTEGER NOT NULL,
    matched_expense_id UUID NOT NULL,
    matched_version_no INTEGER NOT NULL,
    signal_type TEXT NOT NULL
        CHECK (
            signal_type IN (
                'FIELD_MATCH',
                'RECEIPT_HASH_MATCH'
            )
        ),
    match_key TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_duplicate_source
        FOREIGN KEY (expense_id, version_no)
        REFERENCES core.expense_versions(expense_id, version_no),
    CONSTRAINT fk_duplicate_match
        FOREIGN KEY (matched_expense_id, matched_version_no)
        REFERENCES core.expense_versions(expense_id, version_no),
    CONSTRAINT chk_duplicate_not_self
        CHECK (
            expense_id <> matched_expense_id
            OR version_no <> matched_version_no
        ),
    CONSTRAINT uq_duplicate_observation
        UNIQUE (
            expense_id,
            version_no,
            matched_expense_id,
            matched_version_no,
            signal_type,
            match_key
        )
);
CREATE INDEX idx_expense_evidence_expense
    ON core.expense_evidence(expense_id, version_no);
CREATE INDEX idx_duplicate_observations_expense
    ON core.duplicate_observations(expense_id, version_no);
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '002',
    'Create policy, evidence and duplicate observation tables'
);
COMMIT;

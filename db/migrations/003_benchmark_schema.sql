BEGIN;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '003'
    ) THEN
        RAISE EXCEPTION 'Migration 003 is already applied';
    END IF;
END
$$;
CREATE SCHEMA benchmark;
CREATE TABLE benchmark.dataset_manifests (
    manifest_id UUID PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    generator_version TEXT NOT NULL,
    random_seed INTEGER NOT NULL
        CHECK (random_seed >= 0),
    policy_code TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    source_migration TEXT NOT NULL,
    total_cases INTEGER NOT NULL
        CHECK (total_cases >= 0),
    development_cases INTEGER NOT NULL
        CHECK (development_cases >= 0),
    holdout_cases INTEGER NOT NULL
        CHECK (holdout_cases >= 0),
    holdout_locked BOOLEAN NOT NULL DEFAULT TRUE,
    dataset_hash CHAR(64)
        CHECK (
            dataset_hash IS NULL
            OR dataset_hash ~ '^[0-9a-fA-F]{64}$'
        ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dataset_version
        UNIQUE (dataset_name, dataset_version),
    CONSTRAINT chk_manifest_counts
        CHECK (
            total_cases = development_cases + holdout_cases
        )
);
CREATE TABLE benchmark.cases (
    case_id UUID PRIMARY KEY,
    manifest_id UUID NOT NULL
        REFERENCES benchmark.dataset_manifests(manifest_id),
    case_ref TEXT NOT NULL,
    split TEXT NOT NULL
        CHECK (split IN ('DEVELOPMENT', 'HOLDOUT')),
    family_key TEXT NOT NULL
        CHECK (length(trim(family_key)) > 0),
    variant_type TEXT NOT NULL
        CHECK (
            variant_type IN (
                'BASELINE',
                'REPHRASE',
                'INJECTION',
                'BOUNDARY',
                'MISSING_EVIDENCE',
                'AUTHORITY'
            )
        ),
    employee_key TEXT NOT NULL,
    merchant_key TEXT NOT NULL,
    category_hint TEXT NOT NULL
        CHECK (
            category_hint IN (
                'HOTEL',
                'MEALS',
                'TRANSPORTATION',
                'AIRFARE',
                'SOFTWARE',
                'OFFICE_SUPPLIES',
                'UNKNOWN'
            )
        ),
    amount_mxn NUMERIC(12, 2) NOT NULL
        CHECK (amount_mxn > 0),
    currency TEXT NOT NULL DEFAULT 'MXN'
        CHECK (currency = 'MXN'),
    expense_date DATE NOT NULL,
    input_hash CHAR(64) NOT NULL
        CHECK (input_hash ~ '^[0-9a-fA-F]{64}$'),
    receipt_hash CHAR(64)
        CHECK (
            receipt_hash IS NULL
            OR receipt_hash ~ '^[0-9a-fA-F]{64}$'
        ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_case_reference
        UNIQUE (manifest_id, case_ref)
);
CREATE TABLE benchmark.case_history (
    history_id UUID PRIMARY KEY,
    case_id UUID NOT NULL
        REFERENCES benchmark.cases(case_id),
    historical_expense_key TEXT NOT NULL,
    employee_key TEXT NOT NULL,
    merchant_key TEXT NOT NULL,
    amount_mxn NUMERIC(12, 2) NOT NULL
        CHECK (amount_mxn > 0),
    currency TEXT NOT NULL DEFAULT 'MXN'
        CHECK (currency = 'MXN'),
    expense_date DATE NOT NULL,
    receipt_hash CHAR(64)
        CHECK (
            receipt_hash IS NULL
            OR receipt_hash ~ '^[0-9a-fA-F]{64}$'
        ),
    CONSTRAINT uq_case_history_reference
        UNIQUE (case_id, historical_expense_key)
);
CREATE TABLE benchmark.labels (
    case_id UUID PRIMARY KEY
        REFERENCES benchmark.cases(case_id),
    expected_compliance TEXT NOT NULL
        CHECK (
            expected_compliance IN (
                'COMPLIANT',
                'NON_COMPLIANT',
                'UNDETERMINED'
            )
        ),
    expected_risk TEXT NOT NULL
        CHECK (
            expected_risk IN (
                'LOW',
                'MEDIUM',
                'HIGH',
                'UNDETERMINED'
            )
        ),
    expected_route TEXT NOT NULL
        CHECK (
            expected_route IN (
                'SCREENING_COMPLETE',
                'NEEDS_INFORMATION',
                'HUMAN_REVIEW',
                'SYSTEM_RECOVERY',
                'NOT_ADMITTED'
            )
        ),
    assessment_complete BOOLEAN NOT NULL,
    rationale TEXT NOT NULL
        CHECK (length(trim(rationale)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE benchmark.label_rules (
    case_id UUID NOT NULL
        REFERENCES benchmark.labels(case_id),
    rule_code TEXT NOT NULL,
    expected_state TEXT NOT NULL
        CHECK (
            expected_state IN (
                'PASS',
                'VIOLATION',
                'SIGNAL',
                'PENDING',
                'NOT_APPLICABLE'
            )
        ),
    evidence_ref TEXT NOT NULL
        CHECK (length(trim(evidence_ref)) > 0),
    PRIMARY KEY (case_id, rule_code)
);
CREATE INDEX idx_benchmark_cases_split
    ON benchmark.cases(split);
CREATE INDEX idx_benchmark_cases_family
    ON benchmark.cases(family_key);
CREATE INDEX idx_benchmark_history_case
    ON benchmark.case_history(case_id);
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '003',
    'Create isolated benchmark schema'
);
COMMIT;
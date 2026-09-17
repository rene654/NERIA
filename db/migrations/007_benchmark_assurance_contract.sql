BEGIN;
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '007'
    ) THEN
        RAISE EXCEPTION 'Migration 007 is already applied';
    END IF;
END
$$;
ALTER TABLE benchmark.dataset_manifests
ADD COLUMN contract_version TEXT;
UPDATE benchmark.dataset_manifests
SET contract_version = 'v0.1'
WHERE contract_version IS NULL;
ALTER TABLE benchmark.dataset_manifests
ALTER COLUMN contract_version SET NOT NULL;
ALTER TABLE benchmark.dataset_manifests
ADD CONSTRAINT chk_dataset_contract_version
CHECK (length(trim(contract_version)) > 0);
ALTER TABLE benchmark.cases
ADD COLUMN organization_profile_key TEXT;
ALTER TABLE benchmark.cases
ADD COLUMN jurisdiction_country TEXT;
UPDATE benchmark.cases
SET
    organization_profile_key = 'ORG-PROFILE-SMOKE-MX',
    jurisdiction_country = 'MX'
WHERE organization_profile_key IS NULL
   OR jurisdiction_country IS NULL;
ALTER TABLE benchmark.cases
ALTER COLUMN organization_profile_key SET NOT NULL;
ALTER TABLE benchmark.cases
ALTER COLUMN jurisdiction_country SET NOT NULL;
ALTER TABLE benchmark.cases
ADD CONSTRAINT chk_case_organization_profile
CHECK (
    length(trim(organization_profile_key)) > 0
);
ALTER TABLE benchmark.cases
ADD CONSTRAINT chk_case_jurisdiction_country
CHECK (
    jurisdiction_country ~ '^[A-Z]{2}$'
);
ALTER TABLE benchmark.cases
DROP CONSTRAINT cases_variant_type_check;
ALTER TABLE benchmark.cases
ADD CONSTRAINT chk_case_variant_type
CHECK (
    variant_type IN (
        'BASELINE',
        'REPHRASE',
        'INJECTION',
        'BOUNDARY',
        'MISSING_EVIDENCE',
        'AUTHORITY',
        'COUNTERFACTUAL',
        'DUPLICATE_VARIANT',
        'ADVERSARIAL'
    )
);
ALTER TABLE benchmark.cases
ADD CONSTRAINT uq_case_relationship_scope
UNIQUE (
    manifest_id,
    case_id,
    family_key,
    split
);
ALTER TABLE benchmark.labels
ADD COLUMN miss_severity TEXT;
ALTER TABLE benchmark.labels
ADD COLUMN miss_severity_rationale TEXT;
UPDATE benchmark.labels
SET
    miss_severity = 'MEDIUM',
    miss_severity_rationale =
        'Backfilled for pre-v0.2 benchmark data; '
        'manual severity review is required before '
        'using this case in the final benchmark.'
WHERE miss_severity IS NULL
   OR miss_severity_rationale IS NULL;
ALTER TABLE benchmark.labels
ALTER COLUMN miss_severity SET NOT NULL;
ALTER TABLE benchmark.labels
ALTER COLUMN miss_severity_rationale SET NOT NULL;
ALTER TABLE benchmark.labels
ADD CONSTRAINT chk_label_miss_severity
CHECK (
    miss_severity IN (
        'LOW',
        'MEDIUM',
        'HIGH',
        'CRITICAL'
    )
);
ALTER TABLE benchmark.labels
ADD CONSTRAINT chk_label_miss_severity_rationale
CHECK (
    length(trim(miss_severity_rationale)) > 0
);
CREATE TABLE benchmark.case_relationships (
    manifest_id UUID NOT NULL,
    case_id UUID PRIMARY KEY,
    base_case_id UUID NOT NULL,
    family_key TEXT NOT NULL,
    split TEXT NOT NULL,
    relationship_type TEXT NOT NULL
        CHECK (
            relationship_type IN (
                'COUNTERFACTUAL',
                'BOUNDARY_VARIANT',
                'DUPLICATE_VARIANT',
                'ADVERSARIAL'
            )
        ),
    changed_fields TEXT[] NOT NULL
        CHECK (
            cardinality(changed_fields) > 0
            AND array_position(
                changed_fields,
                NULL
            ) IS NULL
        ),
    expected_effect TEXT NOT NULL
        CHECK (
            expected_effect IN (
                'DECISION_MUST_CHANGE',
                'DECISION_MUST_REMAIN_STABLE'
            )
        ),
    expected_changed_outputs TEXT[] NOT NULL
        CHECK (
            array_position(
                expected_changed_outputs,
                NULL
            ) IS NULL
            AND expected_changed_outputs
                <@ ARRAY[
                    'COMPLIANCE',
                    'RISK',
                    'ROUTE',
                    'RULE_STATES',
                    'PERMITTED_ACTIONS'
                ]::TEXT[]
        ),
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_relationship_not_self
        CHECK (case_id <> base_case_id),
    CONSTRAINT chk_relationship_expected_outputs
        CHECK (
            (
                expected_effect =
                    'DECISION_MUST_CHANGE'
                AND cardinality(
                    expected_changed_outputs
                ) > 0
            )
            OR
            (
                expected_effect =
                    'DECISION_MUST_REMAIN_STABLE'
                AND cardinality(
                    expected_changed_outputs
                ) = 0
            )
        ),
    CONSTRAINT fk_relationship_case_scope
        FOREIGN KEY (
            manifest_id,
            case_id,
            family_key,
            split
        )
        REFERENCES benchmark.cases (
            manifest_id,
            case_id,
            family_key,
            split
        )
        ON DELETE CASCADE,
    CONSTRAINT fk_relationship_base_scope
        FOREIGN KEY (
            manifest_id,
            base_case_id,
            family_key,
            split
        )
        REFERENCES benchmark.cases (
            manifest_id,
            case_id,
            family_key,
            split
        )
        ON DELETE CASCADE
);
CREATE INDEX idx_case_relationships_base
ON benchmark.case_relationships (
    manifest_id,
    base_case_id
);
INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '007',
    'Add benchmark assurance contract metadata'
);
COMMIT;
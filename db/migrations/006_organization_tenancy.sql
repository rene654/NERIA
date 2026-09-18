BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM meta.schema_migrations
        WHERE migration_id = '006'
    ) THEN
        RAISE EXCEPTION 'Migration 006 is already applied';
    END IF;
END
$$;

CREATE TABLE core.organizations (
    organization_id UUID PRIMARY KEY,
    organization_code TEXT NOT NULL UNIQUE
        CHECK (
            organization_code ~
            '^[A-Z0-9][A-Z0-9_-]{0,49}$'
        ),
    legal_name TEXT NOT NULL
        CHECK (length(trim(legal_name)) > 0),
    country_code TEXT NOT NULL
        CHECK (country_code ~ '^[A-Z]{2}$'),
    base_currency TEXT NOT NULL
        CHECK (base_currency ~ '^[A-Z]{3}$'),
    time_zone TEXT NOT NULL
        CHECK (length(trim(time_zone)) > 0),
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            status IN (
                'ACTIVE',
                'SUSPENDED',
                'ARCHIVED'
            )
        ),
    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_organization_timestamps
        CHECK (updated_at >= created_at)
);

ALTER TABLE core.employees
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.merchants
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.expenses
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.expense_versions
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.receipt_documents
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.policy_versions
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.expense_evidence
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.duplicate_observations
ADD COLUMN organization_id UUID NOT NULL;

ALTER TABLE core.employees
DROP CONSTRAINT employees_employee_ref_key;

ALTER TABLE core.employees
ADD CONSTRAINT fk_employee_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.employees
ADD CONSTRAINT uq_employee_organization_ref
    UNIQUE (organization_id, employee_ref);

ALTER TABLE core.employees
ADD CONSTRAINT uq_employee_organization_identity
    UNIQUE (organization_id, employee_id);

ALTER TABLE core.merchants
DROP CONSTRAINT merchants_merchant_key_key;

ALTER TABLE core.merchants
ADD CONSTRAINT fk_merchant_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.merchants
ADD CONSTRAINT uq_merchant_organization_key
    UNIQUE (organization_id, merchant_key);

ALTER TABLE core.merchants
ADD CONSTRAINT uq_merchant_organization_identity
    UNIQUE (organization_id, merchant_id);

ALTER TABLE core.expenses
DROP CONSTRAINT expenses_employee_id_fkey;

ALTER TABLE core.expenses
DROP CONSTRAINT uq_expense_source_reference;

ALTER TABLE core.expenses
ADD CONSTRAINT fk_expense_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.expenses
ADD CONSTRAINT fk_expense_employee_tenant
    FOREIGN KEY (organization_id, employee_id)
    REFERENCES core.employees(
        organization_id,
        employee_id
    );

ALTER TABLE core.expenses
ADD CONSTRAINT uq_expense_organization_identity
    UNIQUE (organization_id, expense_id);

ALTER TABLE core.expenses
ADD CONSTRAINT uq_expense_organization_source_ref
    UNIQUE (
        organization_id,
        source_system,
        external_ref
    );

ALTER TABLE core.expense_versions
DROP CONSTRAINT expense_versions_expense_id_fkey;

ALTER TABLE core.expense_versions
DROP CONSTRAINT expense_versions_merchant_id_fkey;

ALTER TABLE core.expense_versions
ADD CONSTRAINT fk_expense_version_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.expense_versions
ADD CONSTRAINT fk_expense_version_tenant
    FOREIGN KEY (organization_id, expense_id)
    REFERENCES core.expenses(
        organization_id,
        expense_id
    );

ALTER TABLE core.expense_versions
ADD CONSTRAINT fk_expense_version_merchant_tenant
    FOREIGN KEY (organization_id, merchant_id)
    REFERENCES core.merchants(
        organization_id,
        merchant_id
    );

ALTER TABLE core.expense_versions
ADD CONSTRAINT uq_expense_version_organization_identity
    UNIQUE (
        organization_id,
        expense_id,
        version_no
    );

ALTER TABLE core.receipt_documents
DROP CONSTRAINT fk_receipt_expense_version;

ALTER TABLE core.receipt_documents
ADD CONSTRAINT fk_receipt_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.receipt_documents
ADD CONSTRAINT fk_receipt_expense_version_tenant
    FOREIGN KEY (
        organization_id,
        expense_id,
        version_no
    )
    REFERENCES core.expense_versions(
        organization_id,
        expense_id,
        version_no
    );

ALTER TABLE core.policy_versions
DROP CONSTRAINT uq_policy_version;

ALTER TABLE core.policy_versions
ADD CONSTRAINT fk_policy_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.policy_versions
ADD CONSTRAINT uq_policy_organization_version
    UNIQUE (
        organization_id,
        policy_code,
        version_label
    );

ALTER TABLE core.expense_evidence
DROP CONSTRAINT fk_evidence_expense_version;

ALTER TABLE core.expense_evidence
ADD CONSTRAINT fk_evidence_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.expense_evidence
ADD CONSTRAINT fk_evidence_expense_version_tenant
    FOREIGN KEY (
        organization_id,
        expense_id,
        version_no
    )
    REFERENCES core.expense_versions(
        organization_id,
        expense_id,
        version_no
    );

ALTER TABLE core.duplicate_observations
DROP CONSTRAINT fk_duplicate_source;

ALTER TABLE core.duplicate_observations
DROP CONSTRAINT fk_duplicate_match;

ALTER TABLE core.duplicate_observations
ADD CONSTRAINT fk_duplicate_organization
    FOREIGN KEY (organization_id)
    REFERENCES core.organizations(organization_id);

ALTER TABLE core.duplicate_observations
ADD CONSTRAINT fk_duplicate_source_tenant
    FOREIGN KEY (
        organization_id,
        expense_id,
        version_no
    )
    REFERENCES core.expense_versions(
        organization_id,
        expense_id,
        version_no
    );

ALTER TABLE core.duplicate_observations
ADD CONSTRAINT fk_duplicate_match_tenant
    FOREIGN KEY (
        organization_id,
        matched_expense_id,
        matched_version_no
    )
    REFERENCES core.expense_versions(
        organization_id,
        expense_id,
        version_no
    );

CREATE INDEX idx_receipt_documents_organization
    ON core.receipt_documents(
        organization_id,
        expense_id,
        version_no
    );

CREATE INDEX idx_expense_evidence_organization
    ON core.expense_evidence(
        organization_id,
        expense_id,
        version_no
    );

CREATE INDEX idx_duplicate_observations_organization
    ON core.duplicate_observations(
        organization_id,
        expense_id,
        version_no
    );

INSERT INTO meta.schema_migrations (
    migration_id,
    description
)
VALUES (
    '006',
    'Add organization tenancy and relational isolation'
);

COMMIT;
-- TalentScreen canonical schema (Postgres = source of truth for chunks)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO tenants (tenant_id, name)
VALUES ('demo-tenant', 'Demo Tenant')
ON CONFLICT (tenant_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    full_name TEXT NOT NULL,
    email TEXT,
    location TEXT,
    years_experience INTEGER,
    skills JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    title TEXT NOT NULL,
    description TEXT,
    required_skills JSONB DEFAULT '[]'::jsonb,
    location TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    candidate_id UUID REFERENCES candidates(candidate_id),
    job_id UUID REFERENCES jobs(job_id),
    doc_type TEXT NOT NULL CHECK (doc_type IN ('resume', 'job_description', 'interview_notes', 'other')),
    filename TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    minio_key TEXT NOT NULL,
    mime_type TEXT,
    parser_used TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, content_hash)
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS applications (
    application_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    job_id UUID NOT NULL REFERENCES jobs(job_id),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    resume_document_id UUID REFERENCES documents(document_id),
    status TEXT NOT NULL DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'reviewing', 'approved', 'rejected')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_applications_job ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_email ON applications(email);

-- Demo job for candidate portal
INSERT INTO jobs (job_id, tenant_id, title, description, required_skills, location)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'demo-tenant',
    'Senior Java Developer — Cloud Platform',
    'Design and build scalable hiring platform backend services. 5+ years Java, Spring Boot, AWS, Kubernetes.',
    '["Java", "Spring Boot", "AWS", "Kubernetes", "PostgreSQL"]'::jsonb,
    'Miami, FL (hybrid)'
)
ON CONFLICT (job_id) DO NOTHING;

-- Supabase/PostgreSQL Schema for Curriculum Standards
-- Run this to create the curriculum table structure

CREATE EXTENSION IF NOT EXISTS vector;

-- Curriculum standards table
CREATE TABLE IF NOT EXISTS curriculum (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Grade
    grade INTEGER NOT NULL,

    -- Domain
    domain TEXT,
    domain_id TEXT,

    -- Unit
    unit_number INTEGER,
    unit_name TEXT,

    -- Cluster
    cluster_id TEXT,
    cluster TEXT,

    -- Lesson
    lesson_title TEXT,
    lesson_order REAL,

    -- Standards (Level 1)
    standard_id_l1 TEXT,
    standard_description_l1 TEXT,

    -- Substandard (most granular)
    substandard_id TEXT UNIQUE NOT NULL,
    substandard_description TEXT,

    -- Additional metadata
    prerequisites TEXT[],
    instructional_approach TEXT,
    common_misconceptions TEXT[],
    worked_examples JSONB,
    assessment_boundary TEXT,

    -- Vector embedding (OpenAI text-embedding-3-large: 1536 dimensions)
    embedding vector(1536),
    searchable_text TEXT,

    -- Raw data
    raw_data JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_curriculum_grade ON curriculum(grade);
CREATE INDEX IF NOT EXISTS idx_curriculum_domain ON curriculum(domain_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_unit ON curriculum(unit_name);
CREATE INDEX IF NOT EXISTS idx_curriculum_cluster ON curriculum(cluster_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_standard ON curriculum(standard_id_l1);
CREATE INDEX IF NOT EXISTS idx_curriculum_substandard ON curriculum(substandard_id);

-- Vector similarity search index (IVFFlat supports >2000 dimensions, HNSW limited to 2000)
CREATE INDEX IF NOT EXISTS idx_curriculum_embedding ON curriculum USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_curriculum_searchable_text ON curriculum USING GIN (to_tsvector('english', searchable_text));

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_curriculum_updated_at
    BEFORE UPDATE ON curriculum
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE curriculum IS 'Educational curriculum standards and learning objectives (grades 3-8)';
COMMENT ON COLUMN curriculum.substandard_id IS 'Unique identifier for most granular learning objective (e.g., CCSS.MATH.CONTENT.3.OA.A.1+1)';
COMMENT ON COLUMN curriculum.embedding IS 'OpenAI text-embedding-3-large embedding (1536 dimensions) for semantic curriculum matching';
COMMENT ON COLUMN curriculum.searchable_text IS 'Concatenated text: unit_name + cluster + lesson_title + substandard_description';

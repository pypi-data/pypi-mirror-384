-- Supabase/PostgreSQL Schema for Question Bank
-- Run this first to create the table structure

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- For text search

-- Main extracted_questions table
CREATE TABLE IF NOT EXISTS extracted_questions (
    -- Core Identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('athena_api', 'textbook_pdf', 'curriculum_generated')),

    -- Academic Classification
    subject TEXT,
    grade INTEGER,
    domain TEXT,
    domain_id TEXT,
    unit_number INTEGER,
    unit_name TEXT,
    cluster TEXT,
    cluster_id TEXT,
    lesson_title TEXT,
    lesson_order REAL,

    -- Standards & Curriculum
    standard_id TEXT,
    standard_description TEXT,
    substandard_id TEXT,
    substandard_description TEXT,
    curriculum_row_ids TEXT[], -- Array of curriculum IDs this maps to

    -- Question Content
    question_en TEXT,
    question_ar TEXT,
    answer_en TEXT,
    answer_ar TEXT,
    explanation_en TEXT,
    explanation_ar TEXT,
    language TEXT CHECK (language IN ('en', 'ar', 'both')),
    images JSONB, -- Array of {url: "", alt: ""}
    stimulus_description TEXT,

    -- Question Metadata
    question_type TEXT,
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    cognitive_level TEXT CHECK (cognitive_level IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    stimulus_needed BOOLEAN,

    -- Direct Instruction & Pedagogy
    direct_instruction_raw TEXT, -- Raw markdown
    prerequisite_skills TEXT[],
    microskills TEXT[],
    vocabulary JSONB, -- Array of {term: "", definition: ""}
    question_stems TEXT[],
    step_by_step_explanations TEXT[],
    common_misconceptions TEXT[],
    learning_objective TEXT,
    worked_example JSONB, -- {steps: [{step: "", order: 1}]}

    -- Template & Generation
    template TEXT,
    parameter_constraints JSONB,
    variability_score REAL CHECK (variability_score >= 0 AND variability_score <= 1),

    -- RAG & Search
    dense_vector vector(1536), -- OpenAI text-embedding-3-large embeddings
    sparse_vector JSONB, -- BM25 sparse vector
    searchable_text TEXT,
    keywords TEXT[],

    -- Source-Specific Metadata
    athena_content_id TEXT,
    athena_level_id TEXT,
    athena_unit_id TEXT,
    athena_lesson_id TEXT,
    textbook_page INTEGER,
    textbook_file TEXT,

    -- Tracking & Quality
    raw_data JSONB, -- Store entire original JSON
    extracted_at TIMESTAMPTZ,
    quality_score REAL CHECK (quality_score >= 0 AND quality_score <= 10),
    validation_status TEXT CHECK (validation_status IN ('validated', 'pending', 'rejected', 'unvalidated')) DEFAULT 'unvalidated',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_extracted_questions_grade ON extracted_questions(grade);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_subject ON extracted_questions(subject);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_unit ON extracted_questions(unit_name);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_lesson ON extracted_questions(lesson_title);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_difficulty ON extracted_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_source ON extracted_questions(source_type, source_name);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_standard ON extracted_questions(standard_id);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_substandard ON extracted_questions(substandard_id);
CREATE INDEX IF NOT EXISTS idx_extracted_questions_cluster ON extracted_questions(cluster_id);

-- GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_extracted_questions_searchable_text ON extracted_questions USING GIN (to_tsvector('english', searchable_text));

-- GIN index for array fields
CREATE INDEX IF NOT EXISTS idx_extracted_questions_keywords ON extracted_questions USING GIN (keywords);

-- Vector similarity search index (IVFFlat supports >2000 dimensions, HNSW limited to 2000)
CREATE INDEX IF NOT EXISTS idx_extracted_questions_dense_vector ON extracted_questions USING ivfflat (dense_vector vector_cosine_ops) WITH (lists = 100);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_extracted_questions_updated_at
    BEFORE UPDATE ON extracted_questions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE extracted_questions IS 'Unified question bank from Athena, textbooks, and curriculum';
COMMENT ON COLUMN extracted_questions.searchable_text IS 'Optimized text for embedding: unit_name + cluster + lesson_title + substandard_description + question_en';
COMMENT ON COLUMN extracted_questions.dense_vector IS 'OpenAI text-embedding-3-large embedding (1536 dimensions) for semantic search';
COMMENT ON COLUMN extracted_questions.content_hash IS 'SHA256 hash of question_en for deduplication';

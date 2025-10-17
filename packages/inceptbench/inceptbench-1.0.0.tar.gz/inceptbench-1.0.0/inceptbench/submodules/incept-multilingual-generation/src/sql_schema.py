SQL_SCHEMA = """
-- Geography Tables
CREATE TABLE IF NOT EXISTS countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(3) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Education System Tables
CREATE TABLE IF NOT EXISTS education_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship between countries and education systems
CREATE TABLE IF NOT EXISTS country_education_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_id UUID NOT NULL,
    education_system_id UUID NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (country_id) REFERENCES countries(id) ON DELETE CASCADE,
    FOREIGN KEY (education_system_id) REFERENCES education_systems(id) ON DELETE CASCADE,
    UNIQUE (country_id, education_system_id)
);

-- Subject Tables
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Grades/Levels
CREATE TABLE IF NOT EXISTS grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    education_system_id UUID NOT NULL,
    grade_number INT NOT NULL,
    grade_name VARCHAR(50) NOT NULL,
    age_group VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (education_system_id) REFERENCES education_systems(id) ON DELETE CASCADE,
    UNIQUE (education_system_id, grade_number)
);

-- Curriculum Structure
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    education_system_id UUID NOT NULL,
    subject_id UUID NOT NULL,
    grade_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sequence_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (education_system_id) REFERENCES education_systems(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (grade_id) REFERENCES grades(id) ON DELETE CASCADE,
    UNIQUE (name, grade_id, education_system_id, subject_id)
);

CREATE INDEX IF NOT EXISTS idx_curriculum_lookup ON topics (education_system_id, subject_id, grade_id);

CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sequence_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_topic_chapters ON chapters (topic_id, sequence_order);

CREATE TABLE IF NOT EXISTS sub_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sequence_order INT DEFAULT 0,
    learning_objectives TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapter_subtopics ON sub_topics (chapter_id, sequence_order);

-- Question Types
CREATE TABLE IF NOT EXISTS question_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Language Tables
CREATE TABLE IF NOT EXISTS languages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Questions and Answers
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_topic_id UUID NOT NULL,
    language_id UUID NOT NULL,
    question_type_id UUID NOT NULL,
    question_text TEXT NOT NULL,
    question_data JSONB,
    difficulty_level VARCHAR(10) DEFAULT 'medium' CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    points INT DEFAULT 1,
    time_limit_seconds INT,
    explanation TEXT,
    hints JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sub_topic_id) REFERENCES sub_topics(id) ON DELETE CASCADE,
    FOREIGN KEY (question_type_id) REFERENCES question_types(id),
    FOREIGN KEY (language_id) REFERENCES languages(id)
);

CREATE INDEX IF NOT EXISTS idx_subtopic_questions ON questions (sub_topic_id);
CREATE INDEX IF NOT EXISTS idx_difficulty ON questions (difficulty_level);

-- Answers table
CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL,
    answer_text TEXT NOT NULL,
    answer_data JSONB,
    is_correct BOOLEAN DEFAULT FALSE,
    explanation TEXT,
    sequence_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_question_answers ON answers (question_id);

-- Tags for additional categorization
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';


-- Insert sample question types
INSERT INTO question_types (name, code, description) VALUES
('Multiple Choice', 'MCQ', 'Single correct answer from multiple options'),
('Multiple Select', 'MSQ', 'Multiple correct answers from multiple options'),
('Fill in the Blank', 'FITB', 'Complete the missing word(s)'),
('True/False', 'TF', 'Binary choice question'),
('Example Question', 'EXAMPLE', 'Example questions from curriculum')
ON CONFLICT (code) DO NOTHING;
"""

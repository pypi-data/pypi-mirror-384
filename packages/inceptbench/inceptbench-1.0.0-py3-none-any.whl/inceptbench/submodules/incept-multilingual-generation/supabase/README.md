# Supabase Database Setup

## Running Migrations

### Option 1: Supabase Dashboard
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run migrations in order:
   - `migrations/20251009_create_questions_table.sql`
   - `migrations/20251009_create_curriculum_table.sql`
4. Click "Run" for each

### Option 2: Using psql
```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" \
  -f supabase/migrations/20251009_create_questions_table.sql
```

### Option 3: Using Supabase CLI (if installed)
```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Link to your project
supabase link --project-ref [YOUR-PROJECT-REF]

# Run migrations
supabase db push
```

## Environment Variables

Create a `.env` file in the project root with:
```bash
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-ANON-KEY]
SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
```

## Database Schema

### `extracted_questions` table
Contains all extracted questions from:
- Athena API
- Textbook PDFs
- Curriculum-generated questions

See `migrations/20251009_create_questions_table.sql` for full schema.

### `curriculum` table
Contains educational curriculum standards (grades 3-8):
- 671 substandards across 6 grades
- Hierarchical structure: Domain → Unit → Cluster → Standard → Substandard
- Includes OpenAI text-embedding-3-large embeddings (1536 dims) for semantic curriculum matching

See `migrations/20251010_create_curriculum_table.sql` for full schema.

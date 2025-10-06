-- ========================================
-- EVIKA ONBOARDING FLOW - Supabase Schema
-- ========================================
-- 
-- This schema supports the complete onboarding flow
-- matching (and exceeding) Keika GEO's functionality
--

-- Table: onboarding_sessions
-- Tracks the complete onboarding journey for each user
CREATE TABLE IF NOT EXISTS onboarding_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    market TEXT NOT NULL DEFAULT 'United States',
    language TEXT NOT NULL DEFAULT 'en',
    status TEXT NOT NULL DEFAULT 'started', -- started, in_progress, completed, abandoned
    current_step TEXT NOT NULL DEFAULT 'website', -- website, site_health, description, prompts, competitors, analysis, finishing
    
    -- Step 2: Site Health Data
    site_health JSONB DEFAULT '{}'::jsonb,
    
    -- Step 3: Description
    description TEXT,
    
    -- Step 4: Queries (20 AI queries)
    queries JSONB DEFAULT '[]'::jsonb,
    
    -- Step 5: Competitors
    competitors JSONB DEFAULT '[]'::jsonb,
    
    -- Step 6: Analysis Results
    analysis_result JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Add comment to table
COMMENT ON TABLE onboarding_sessions IS 'Tracks user onboarding flow through 7 steps: website, site_health, description, prompts, competitors, analysis, finishing';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_site_id ON onboarding_sessions(site_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_status ON onboarding_sessions(status);
CREATE INDEX IF NOT EXISTS idx_onboarding_created_at ON onboarding_sessions(created_at);

-- Add comments to columns
COMMENT ON COLUMN onboarding_sessions.site_health IS 'JSON object containing: {llms_txt, robots_txt, ssl, mobile_friendly, structured_data, page_speed_ms}';
COMMENT ON COLUMN onboarding_sessions.queries IS 'Array of 20 AI queries: [{id, category, text}]';
COMMENT ON COLUMN onboarding_sessions.competitors IS 'Array of competitors: [{name, url, auto_discovered}]';
COMMENT ON COLUMN onboarding_sessions.analysis_result IS 'Visibility analysis: {visibility_score, brand_mentions, queries_tested, before, after, message}';

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_onboarding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_update_onboarding_timestamp
    BEFORE UPDATE ON onboarding_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_onboarding_updated_at();

-- Update sites table to support onboarding
-- Add status column if it doesn't exist
ALTER TABLE sites ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
COMMENT ON COLUMN sites.status IS 'Site status: onboarding, active, inactive, deleted';

-- Add description column if it doesn't exist
ALTER TABLE sites ADD COLUMN IF NOT EXISTS description TEXT;
COMMENT ON COLUMN sites.description IS 'AI-generated business description for onboarding';

-- ========================================
-- SAMPLE QUERIES FOR TESTING
-- ========================================

-- Get all onboarding sessions for a site
-- SELECT * FROM onboarding_sessions WHERE site_id = 'your-site-id' ORDER BY created_at DESC;

-- Get current onboarding step
-- SELECT id, url, current_step, status FROM onboarding_sessions WHERE id = 'onboarding-id';

-- Get completed onboarding sessions
-- SELECT * FROM onboarding_sessions WHERE status = 'completed' ORDER BY completed_at DESC;

-- Get abandoned onboarding sessions (started but not completed in last 24 hours)
-- SELECT * FROM onboarding_sessions 
-- WHERE status = 'started' 
-- AND created_at < NOW() - INTERVAL '24 hours' 
-- AND completed_at IS NULL;

-- Get average time to complete onboarding
-- SELECT AVG(completed_at - created_at) as avg_completion_time 
-- FROM onboarding_sessions 
-- WHERE status = 'completed';

-- ========================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ========================================

-- Enable RLS
ALTER TABLE onboarding_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own onboarding sessions
-- (Adjust based on your auth setup)
CREATE POLICY onboarding_sessions_user_policy ON onboarding_sessions
    FOR ALL
    USING (auth.uid() IS NOT NULL);

-- Policy for service role (backend API)
CREATE POLICY onboarding_sessions_service_policy ON onboarding_sessions
    FOR ALL
    USING (true);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Index for quick lookups by URL
CREATE INDEX IF NOT EXISTS idx_onboarding_url ON onboarding_sessions(url);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_onboarding_completed ON onboarding_sessions(completed_at) WHERE status = 'completed';

-- GIN index for JSONB queries (site_health, queries, competitors, analysis_result)
CREATE INDEX IF NOT EXISTS idx_onboarding_site_health_gin ON onboarding_sessions USING GIN (site_health);
CREATE INDEX IF NOT EXISTS idx_onboarding_queries_gin ON onboarding_sessions USING GIN (queries);
CREATE INDEX IF NOT EXISTS idx_onboarding_competitors_gin ON onboarding_sessions USING GIN (competitors);
CREATE INDEX IF NOT EXISTS idx_onboarding_analysis_gin ON onboarding_sessions USING GIN (analysis_result);

-- ========================================
-- ANALYTICS VIEWS
-- ========================================

-- View: Onboarding funnel metrics
CREATE OR REPLACE VIEW onboarding_funnel AS
SELECT 
    current_step,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM onboarding_sessions
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY current_step
ORDER BY 
    CASE current_step
        WHEN 'website' THEN 1
        WHEN 'site_health' THEN 2
        WHEN 'description' THEN 3
        WHEN 'prompts' THEN 4
        WHEN 'competitors' THEN 5
        WHEN 'analysis' THEN 6
        WHEN 'finishing' THEN 7
        ELSE 8
    END;

-- View: Onboarding completion rate
CREATE OR REPLACE VIEW onboarding_metrics AS
SELECT 
    COUNT(*) as total_started,
    COUNT(*) FILTER (WHERE status = 'completed') as total_completed,
    (COUNT(*) FILTER (WHERE status = 'completed')::FLOAT / COUNT(*)::FLOAT * 100) as completion_rate,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 60) FILTER (WHERE status = 'completed') as avg_completion_minutes
FROM onboarding_sessions
WHERE created_at > NOW() - INTERVAL '30 days';

-- ========================================
-- SEED DATA (FOR TESTING)
-- ========================================

-- Example onboarding session (commented out - uncomment to use)
/*
INSERT INTO onboarding_sessions (
    id,
    site_id,
    url,
    market,
    language,
    status,
    current_step,
    site_health,
    description,
    queries,
    competitors,
    analysis_result,
    completed_at
) VALUES (
    gen_random_uuid(),
    'your-site-id-here',
    'https://example.com',
    'United States',
    'en',
    'completed',
    'finishing',
    '{"llms_txt": false, "robots_txt": true, "ssl": true, "mobile_friendly": true, "structured_data": true, "page_speed_ms": 523}'::jsonb,
    'Example Inc provides professional services...',
    '[{"id": 1, "category": "brand", "text": "What is Example Inc?"}]'::jsonb,
    '[{"name": "Competitor A", "url": "https://competitor-a.com", "auto_discovered": true}]'::jsonb,
    '{"visibility_score": 0, "brand_mentions": 0, "queries_tested": 20}'::jsonb,
    NOW()
);
*/

-- ========================================
-- CLEANUP QUERIES (USE WITH CAUTION)
-- ========================================

-- Delete old abandoned onboarding sessions (older than 7 days)
-- DELETE FROM onboarding_sessions 
-- WHERE status = 'started' 
-- AND created_at < NOW() - INTERVAL '7 days' 
-- AND completed_at IS NULL;


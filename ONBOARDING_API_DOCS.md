# EVIKA Onboarding API Documentation

## 🎯 Overview

This document describes the complete onboarding flow API for EVIKA, designed to match (and exceed) Keika GEO's "Test Your Site" functionality.

**Base URL:** `https://your-backend.railway.app` or `http://localhost:8000`

---

## 📋 Onboarding Flow Steps

```
1. Website Selection       → POST /onboarding/start
2. Site Health Check       → POST /onboarding/site-health
3. Description Generation  → POST /onboarding/generate-description
4. Query Generation        → POST /onboarding/generate-queries
5. Competitor Discovery    → POST /onboarding/discover-competitors
6. Visibility Analysis     → POST /onboarding/run-analysis
7. View Dashboard          → Redirect to dashboard
```

---

## 🚀 API Endpoints

### 1. Start Onboarding

**POST** `/onboarding/start`

Start a new onboarding session with URL and market selection.

**Request Body:**
```json
{
  "url": "https://mobilusdetailing.lt",
  "market": "Lithuania",          // Optional, defaults to "United States"
  "language": "lt"                // Optional, auto-detected from domain
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "site_id": "660e8400-e29b-41d4-a716-446655440001",
  "url": "https://mobilusdetailing.lt",
  "market": "Lithuania",
  "language": "lt",
  "next_step": "site_health",
  "message": "Onboarding started successfully"
}
```

**Frontend Integration:**
```typescript
const startOnboarding = async (url: string, market: string) => {
  const response = await fetch('/onboarding/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, market })
  });
  const data = await response.json();
  
  // Store onboarding_id and site_id in state
  setOnboardingId(data.onboarding_id);
  setSiteId(data.site_id);
  
  // Move to next step
  navigate('/onboarding/site-health');
};
```

---

### 2. Site Health Check

**POST** `/onboarding/site-health`

Analyzes website for AI-readiness and technical SEO.

**Request Body:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "health_results": {
    "llms_txt": false,
    "robots_txt": true,
    "ssl": true,
    "mobile_friendly": true,
    "structured_data": true,
    "page_speed_ms": 573
  },
  "good_things": [
    {
      "name": "AI Crawler Permissions",
      "message": "Robots.txt allows AI crawlers"
    },
    {
      "name": "Security Certificate",
      "message": "SSL certificate active"
    },
    {
      "name": "Your page is loading fast",
      "message": "Page loaded in 573ms"
    },
    {
      "name": "Mobile Optimization",
      "message": "Site appears mobile-friendly"
    },
    {
      "name": "Structured Data",
      "message": "Structured data found"
    }
  ],
  "issues": [
    {
      "name": "AI Instructions File",
      "message": "llms.txt file not found",
      "priority": "high"
    }
  ],
  "good_count": 5,
  "issues_count": 1,
  "next_step": "description"
}
```

**Frontend Integration:**
```typescript
const runSiteHealthCheck = async () => {
  const response = await fetch('/onboarding/site-health', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ onboarding_id: onboardingId })
  });
  const data = await response.json();
  
  // Display good things and issues
  setGoodThings(data.good_things);
  setIssues(data.issues);
  
  // Show "We found X good things" message
  showMessage(`We found ${data.good_count} good things in your website...`);
};
```

---

### 3. Generate Description

**POST** `/onboarding/generate-description`

Auto-generates AI-friendly business description using GPT-4.

**Request Body:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Optional custom description"  // If not provided, auto-generates
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Mobilusdetailing offers professional mobile car detailing services that restore and protect your vehicle's appearance at your location. Their convenient, high-quality service is perfect for busy customers who want a spotless car without leaving home or work.",
  "char_count": 258,
  "next_step": "prompts"
}
```

**Frontend Integration:**
```typescript
const generateDescription = async (customDescription?: string) => {
  const response = await fetch('/onboarding/generate-description', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      onboarding_id: onboardingId,
      description: customDescription 
    })
  });
  const data = await response.json();
  
  // Display description in textarea (editable)
  setDescription(data.description);
  setCharCount(data.char_count);
  
  // Add "Regenerate description" button
  // that calls this function again without customDescription
};
```

---

### 4. Generate Queries

**POST** `/onboarding/generate-queries`

Generates 20 AI queries in the user's language.

**Request Body:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "custom_queries": ["optional custom query 1", "optional custom query 2"]
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "queries": [
    {
      "id": 1,
      "category": "brand",
      "text": "geriausia automobilių valymo paslauga Vilniuje"
    },
    {
      "id": 2,
      "category": "service_product",
      "text": "automobilių detalių paslauga Kaune"
    },
    {
      "id": 3,
      "category": "local_geo",
      "text": "mobilus automobilių valymas Vilniaus rajone"
    }
    // ... 17 more queries (total 20)
  ],
  "total_queries": 20,
  "next_step": "competitors"
}
```

**Query Categories:**
- `brand` - Questions about the brand itself
- `service_product` - Questions about services/products
- `competitor` - Comparison questions
- `local_geo` - Location-based questions
- `problem_solving` - Industry problem questions
- `custom` - User-added custom queries

**Frontend Integration:**
```typescript
const generateQueries = async () => {
  const response = await fetch('/onboarding/generate-queries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ onboarding_id: onboardingId })
  });
  const data = await response.json();
  
  // Display queries with edit/delete buttons
  setQueries(data.queries);
  
  // Show count: "5/20 prompts"
  setQueryCount(data.total_queries);
};
```

---

### 5. Discover Competitors

**POST** `/onboarding/discover-competitors`

Discovers competitors (auto or manual).

**Request Body:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "competitors": [
    {
      "name": "Competitor Name",
      "url": "https://competitor.com"
    }
  ]  // Optional, if not provided, auto-discovers
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "competitors": [
    {
      "name": "Competitor A",
      "url": "https://competitor-a.com",
      "auto_discovered": true
    },
    {
      "name": "Competitor B",
      "url": "https://competitor-b.com",
      "auto_discovered": true
    },
    {
      "name": "Competitor C",
      "url": "https://competitor-c.com",
      "auto_discovered": true
    }
  ],
  "total_competitors": 3,
  "next_step": "analysis"
}
```

**Frontend Integration:**
```typescript
const discoverCompetitors = async (manualCompetitors?: Array<{name: string, url: string}>) => {
  const response = await fetch('/onboarding/discover-competitors', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      onboarding_id: onboardingId,
      competitors: manualCompetitors 
    })
  });
  const data = await response.json();
  
  // Display competitors with logos and delete buttons
  setCompetitors(data.competitors);
  
  // Show "Who's Stealing Your AI Traffic?" message
  // Show count: "10/20 competitors"
};
```

---

### 6. Run Analysis

**POST** `/onboarding/run-analysis`

Runs visibility analysis and generates before/after comparison.

**Request Body:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "success": true,
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "site_id": "660e8400-e29b-41d4-a716-446655440001",
  "analysis": {
    "visibility_score": 0,
    "brand_mentions": 0,
    "queries_tested": 20,
    "before": {
      "query": "geriausia automobilių valymo paslauga Vilniuje",
      "results": [
        {
          "rank": 1,
          "brand": "AutoSPA",
          "snippet": "Profesionalus automobilių valymas su įvairiais paslaugų paketais."
        },
        {
          "rank": 2,
          "brand": "AutoClean",
          "snippet": "Platus automobilių valymo ir priežiūros paslaugų asortimentas."
        },
        {
          "rank": 3,
          "brand": "AutoGlow",
          "snippet": "Specializuota automobilių valymo įmonė..."
        }
      ]
    },
    "after": {
      "query": "geriausia automobilių valymo paslauga Vilniuje",
      "results": [
        {
          "rank": 1,
          "brand": "Mobilusdetailing",
          "snippet": "Pirmaujanti mobiliojo automobilių detailingo paslaugų įmonė..."
        },
        {
          "rank": 2,
          "brand": "AutoSPA",
          "snippet": "Profesionalus automobilių valymas su įvairiais paslaugų paketais."
        }
      ]
    },
    "message": "Mobilusdetailing is showing up in 0% of our simulated searches in AI."
  },
  "next_step": "dashboard",
  "dashboard_url": "/dashboard/660e8400-e29b-41d4-a716-446655440001"
}
```

**Frontend Integration:**
```typescript
const runAnalysis = async () => {
  // Show loading state
  setAnalyzing(true);
  
  const response = await fetch('/onboarding/run-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ onboarding_id: onboardingId })
  });
  const data = await response.json();
  
  setAnalyzing(false);
  
  // Page 1: Show bad news
  showMessage(data.analysis.message); // "Mobilusdetailing is showing up in 0%..."
  
  // Page 2: Show "Let's see how you and your competitors show up on AI Search"
  // (loading animation)
  
  // Page 3: Show before/after comparison
  setBeforeResults(data.analysis.before);
  setAfterResults(data.analysis.after);
  
  // Final button: "Use EVIKA to win →"
  // Navigate to dashboard
  navigate(data.dashboard_url);
};
```

---

### 7. Get Onboarding Status

**GET** `/onboarding/{onboarding_id}`

Retrieve current onboarding status (useful for resuming).

**Response:**
```json
{
  "success": true,
  "onboarding": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "site_id": "660e8400-e29b-41d4-a716-446655440001",
    "url": "https://mobilusdetailing.lt",
    "market": "Lithuania",
    "language": "lt",
    "status": "in_progress",
    "current_step": "site_health",
    "site_health": {...},
    "description": null,
    "queries": [],
    "competitors": [],
    "analysis_result": {},
    "created_at": "2025-10-06T20:00:00Z",
    "updated_at": "2025-10-06T20:05:00Z"
  }
}
```

---

## 🎨 Frontend Component Structure

```
/components/onboarding/
  ├── OnboardingWizard.tsx          # Main container
  ├── ProgressSidebar.tsx           # 7-step progress indicator
  ├── Step1_Website.tsx             # URL + Market selection
  ├── Step2_SiteHealth.tsx          # Health check results
  ├── Step3_Description.tsx         # AI-generated description
  ├── Step4_Prompts.tsx             # Query generation
  ├── Step5_Competitors.tsx         # Competitor discovery
  ├── Step6_Analysis.tsx            # Before/After comparison
  └── Step7_Finishing.tsx           # "Your dashboard is ready!"
```

---

## 🔄 Complete Flow Example

```typescript
// 1. Start onboarding
const { onboarding_id, site_id } = await startOnboarding(url, market);

// 2. Run site health
const healthData = await runSiteHealthCheck(onboarding_id);

// 3. Generate description
const descData = await generateDescription(onboarding_id);

// 4. Generate queries
const queryData = await generateQueries(onboarding_id);

// 5. Discover competitors
const compData = await discoverCompetitors(onboarding_id);

// 6. Run analysis
const analysisData = await runAnalysis(onboarding_id);

// 7. Redirect to dashboard
navigate(`/dashboard/${site_id}`);
```

---

## 🚨 Error Handling

All endpoints return errors in this format:

```json
{
  "error": "Error message here",
  "details": "Additional error details (optional)"
}
```

**Frontend Error Handling:**
```typescript
try {
  const response = await fetch('/onboarding/start', {...});
  const data = await response.json();
  
  if (data.error) {
    toast.error(data.error);
    return;
  }
  
  // Success handling...
} catch (error) {
  toast.error('Network error. Please try again.');
}
```

---

## 🎯 Key Features to Highlight

1. **✅ Auto-Detection** - Language and market auto-detected from domain
2. **✅ AI-Powered** - GPT-4 generates descriptions and queries
3. **✅ Localized** - Queries generated in user's language
4. **✅ llms.txt Check** - First tool to check for AI instructions file!
5. **✅ Before/After** - Visual comparison showing value proposition
6. **✅ Editable** - Users can customize every step
7. **✅ Resumable** - Can pause and resume onboarding

---

## 📊 Supabase Schema

Run this SQL to create the required tables:

```bash
# Apply schema
psql $DATABASE_URL < onboarding_schema.sql
```

Or use Supabase dashboard SQL editor:
1. Go to Supabase → SQL Editor
2. Paste contents of `onboarding_schema.sql`
3. Run query

---

## 🧪 Testing

Test the complete flow using these curl commands:

```bash
# 1. Start onboarding
curl -X POST http://localhost:8000/onboarding/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mobilusdetailing.lt", "market": "Lithuania"}'

# 2. Site health (use onboarding_id from step 1)
curl -X POST http://localhost:8000/onboarding/site-health \
  -H "Content-Type: application/json" \
  -d '{"onboarding_id": "YOUR_ONBOARDING_ID"}'

# ... and so on for each step
```

---

## 🚀 Deployment Checklist

- [ ] Deploy backend to Railway
- [ ] Set environment variables: `LLM_API_KEY`, `OPENAI_API_KEY`
- [ ] Run Supabase schema migrations
- [ ] Update CORS origins in main.py
- [ ] Test complete flow end-to-end
- [ ] Monitor error logs

---

## 📞 Support

If you have questions, check:
- This documentation
- `main.py` - Implementation code
- `onboarding_schema.sql` - Database schema
- Screenshots in `.cursor/screenshots/` - UI reference from Keika

**Built with ❤️ for EVIKA by Cursor AI**


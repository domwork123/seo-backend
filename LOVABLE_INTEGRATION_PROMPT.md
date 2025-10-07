# 🎯 EVIKA Onboarding Frontend - Lovable Integration Prompt

## 🚀 Build a Modern Multi-Step Onboarding Journey (Keika-Style)

Design a Keika-inspired multi-step onboarding flow for a SaaS product that replicates the exact UI/UX and screen structure shown in the reference screenshots — minimalist, bright white layout, soft pink-purple gradient CTAs, subtle animations, and linear step progression.

## 🔒 Access Rule
This onboarding journey must be accessible only via the "Try Out" button on the landing page.
When a user clicks "Try Out" (CTA on hero section), the page should smoothly transition or route to this onboarding flow.
Direct access through URL (e.g. /onboarding) should be restricted — users must come from the "Try Out" click event.
Add a fallback message if someone tries to access it directly:
"Please start from the homepage to try the tool."

## 🧩 Core Layout & Styling
- **Left sidebar:** vertical progress tracker (Website, Site Health, Description, Prompts, Competitors, Analysis, Finishing Up)
- **Right panel:** step content (form fields, AI results, etc.)
- **Top-left logo:** minimal mark (like "k" in Keika)
- **Global CTA buttons:** pink-to-purple gradient (#FF7070 → #B770FF), rounded-full, bold text, smooth hover transition
- **Typography:** Poppins or Inter, medium weight, modern clean spacing
- **Background:** white with faint radial gradient for depth
- **Animations:** fade/slide transitions (Framer Motion) between steps

## ⚙️ Step-by-Step Flow

### Step 1 – Entry
- Input field: "website.com" with globe icon
- CTA: Test your site →
- Subtext: "No credit card required. Or click here to log in."
- Leads to Sign-Up flow.

### Step 2 – Sign Up / Auth
- Two-column layout:
  - Left: Google OAuth + Email/Password signup form
  - Right: gradient orb background + testimonial + "Trusted by" logos grid
- Button: Sign Up (gradient)
- "Already have an account? Sign in" link.

### Step 3 – Website & Market
- Title: "Let's Find Your Competitors"
- Input fields:
  - Website (prefilled)
  - Market dropdown (flags: UK, LT, US, DE, FR, etc.)
- Continue button.

### Step 4 – Site Health
- Screen A: "We found X good things" (card list)
- Screen B: "And 5 things that need fixing" (error cards)
- Button: Start appearing in AI results

### Step 5 – Business Description
- Prompt: "Tell us about your business…"
- Textarea + 500 char limit + "Regenerate description" link
- Continue button.

### Step 6 – Prompts
- Title: "We Generated These Just For You"
- Editable prompt list (with ✏️ and ❌ icons)
- Option to add custom prompt
- Continue button.

### Step 7 – Competitors
- Title: "Who's Stealing Your AI Traffic?"
- Subtitle: "We discovered X competitors appearing alongside your brand."
- Grid with competitor cards (Rocket Internet, Antler, etc.)
- Add competitor (input + domain + ➕ button)
- Continue button.

### Step 8 – Analysis
- Progress bar animation
- Text: "Your site is showing up in 0% of simulated AI searches."
- Button: See who's winning →

### Step 9 – Results Comparison
- Two columns:
  - Left: "Search without Keika"
  - Right: "What you could achieve with Keika"
- Bottom CTA: Use Keika to win →

### Step 10 – Finishing Up
- Final CTA: "Start optimizing your site with Evika"
- Button: Go to Dashboard →

## 🌈 Styling Details
- **Gradient:** linear-gradient(90deg, #FF7070 0%, #B770FF 100%)
- **Card corner radius:** rounded-2xl
- **Box shadow:** subtle, soft drop for depth
- **Exit link bottom-left:** "Exit" (gray text)
- **Animated sidebar progress** with each step
- **Autosave each step** locally
- **Consistent margin/padding** grid system

## 💡 Behavioral Logic
- Each step validates input before continuing
- Smooth fade or slide transition (Framer Motion)
- On completion → redirect user to /dashboard
- "Exit" resets progress and returns to homepage

## ⚙️ Tech Spec
- **Frontend:** React + TailwindCSS + Framer Motion
- **Auth:** Supabase (Google + email/password)
- **Routing:** Only trigger onboarding route via Try Out button click event

---

## 🔗 BACKEND INTEGRATION POINTS

### 🎯 API Base URL
```
Base URL: https://your-backend.railway.app
```

### 📋 Complete API Endpoints

#### 1. **POST** `/onboarding/start`
**Purpose:** Initialize onboarding session with URL and market
**Request:**
```json
{
  "url": "https://mobilusdetailing.lt",
  "market": "Lithuania",
  "language": "lt"
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
  "next_step": "site_health"
}
```

#### 2. **POST** `/onboarding/site-health`
**Purpose:** Analyze website for AI-readiness and technical SEO
**Request:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
**Response:**
```json
{
  "success": true,
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
  "issues_count": 1
}
```

#### 3. **POST** `/onboarding/generate-description`
**Purpose:** Auto-generate AI-friendly business description
**Request:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Optional custom description"
}
```
**Response:**
```json
{
  "success": true,
  "description": "Mobilusdetailing offers professional mobile car detailing services...",
  "char_count": 258
}
```

#### 4. **POST** `/onboarding/generate-queries`
**Purpose:** Generate 20 AI queries in user's language
**Request:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "custom_queries": ["optional custom query 1"]
}
```
**Response:**
```json
{
  "success": true,
  "queries": [
    {
      "id": 1,
      "category": "brand",
      "text": "geriausia automobilių valymo paslauga Vilniuje"
    }
  ],
  "total_queries": 20
}
```

#### 5. **POST** `/onboarding/discover-competitors`
**Purpose:** Discover competitors (auto or manual)
**Request:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000",
  "competitors": [
    {
      "name": "Competitor Name",
      "url": "https://competitor.com"
    }
  ]
}
```
**Response:**
```json
{
  "success": true,
  "competitors": [
    {
      "name": "Competitor A",
      "url": "https://competitor-a.com",
      "auto_discovered": true
    }
  ],
  "total_competitors": 3
}
```

#### 6. **POST** `/onboarding/run-analysis`
**Purpose:** Run visibility analysis and generate before/after comparison
**Request:**
```json
{
  "onboarding_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
**Response:**
```json
{
  "success": true,
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
          "snippet": "Profesionalus automobilių valymas..."
        }
      ]
    },
    "after": {
      "query": "geriausia automobilių valymo paslauga Vilniuje",
      "results": [
        {
          "rank": 1,
          "brand": "Mobilusdetailing",
          "snippet": "Pirmaujanti mobiliojo automobilių detailingo..."
        }
      ]
    },
    "message": "Mobilusdetailing is showing up in 0% of our simulated searches in AI."
  },
  "dashboard_url": "/dashboard/660e8400-e29b-41d4-a716-446655440001"
}
```

#### 7. **GET** `/onboarding/{onboarding_id}`
**Purpose:** Retrieve current onboarding status (for resuming)
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
    "analysis_result": {}
  }
}
```

---

## 🎨 Frontend Component Structure

```
/src/pages/
  └── Onboarding.tsx                 # Main onboarding page

/src/components/onboarding/
  ├── OnboardingWizard.tsx           # Container with state management
  ├── ProgressSidebar.tsx            # 7-step indicator (left sidebar)
  ├── Step1_Website.tsx              # URL input + market dropdown
  ├── Step2_SiteHealth.tsx           # Health check results display
  ├── Step3_Description.tsx          # Description editor
  ├── Step4_Prompts.tsx              # Query list (editable)
  ├── Step5_Competitors.tsx          # Competitor list
  ├── Step6_Analysis.tsx             # Before/After comparison
  └── Step7_Finishing.tsx            # Loading → "Dashboard ready!"

/src/lib/
  └── onboarding-api.ts              # API client functions
```

---

## 🔑 Key Backend Features

### **Auto-Detection:**
- ✅ Language from domain (.lt, .de, .fr, etc.)
- ✅ Market suggestion based on domain
- ✅ Business description from website content

### **AI-Powered:**
- ✅ GPT-4 generates descriptions
- ✅ GPT-4 generates localized queries
- ✅ Semantic analysis of website content

### **Site Health Checks:**
1. ✅ llms.txt file (AI instructions) - **UNIQUE FEATURE!**
2. ✅ robots.txt (AI crawler permissions)
3. ✅ SSL certificate
4. ✅ Mobile optimization
5. ✅ Structured data (JSON-LD)
6. ✅ Page speed

### **Localization:**
- ✅ Queries generated in user's language
- ✅ Supports: English, Lithuanian, German, French, Spanish, Italian, Polish
- ✅ Easy to add more languages

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

## 🎯 The "Money Shot" (Conversion Screen)

**Step 9: Before/After Comparison**

Shows side-by-side:
- **LEFT:** "Without EVIKA" - Your brand at 0%, competitors winning
- **RIGHT:** "With EVIKA" - Your brand at #1, competitors below

This single screen drives conversions!

---

## 🧪 Testing Commands

```bash
# 1. Start onboarding
curl -X POST https://your-backend.railway.app/onboarding/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://mobilusdetailing.lt", "market": "Lithuania"}'

# 2. Site health (use onboarding_id from step 1)
curl -X POST https://your-backend.railway.app/onboarding/site-health \
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

## 📊 Business Value

### **For Users:**
- See their AI visibility in 2 minutes
- Understand the problem (0% visibility)
- See the solution (EVIKA optimization)
- Get actionable insights
- No credit card required

### **For EVIKA:**
- High conversion funnel
- Data collection (onboarding analytics)
- User education
- Problem-solution framing
- Lead generation
- Upsell opportunities

---

## 🎉 Success Metrics

After launch, track:
- **Conversion rate:** % who complete onboarding
- **Time to complete:** Average time for 7 steps
- **Drop-off rate:** Which step loses most users
- **Visibility scores:** Average score of new users
- **Sign-ups:** How many become paying customers

---

## 🔗 Backend Connection Summary

**Your backend is FULLY READY with:**
- ✅ 7 API endpoints fully functional
- ✅ Database schema with indexes
- ✅ Complete API documentation
- ✅ 17 UI reference screenshots
- ✅ TypeScript interfaces in docs
- ✅ Example integration code
- ✅ Testing scripts

**What's Needed:**
- ⏭️ React components in Lovable
- ⏭️ API client functions
- ⏭️ State management (React hooks)
- ⏭️ Loading/error states
- ⏭️ Responsive design
- ⏭️ Animations/transitions

**Timeline Estimate:**
- Frontend build: 2-3 weeks
- Testing: 1 week
- Polish: 1 week
- **Total: 4-5 weeks to launch**

---

**Ready to integrate with Lovable and LAUNCH! 🚀🚀🚀**

**Built with ❤️ by Cursor AI for EVIKA**

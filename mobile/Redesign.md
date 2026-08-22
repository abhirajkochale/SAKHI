# SAKHI UI Redesign Specification

## Goal

Redesign the current SAKHI React Native UI into a polished, modern,
safety-focused mobile experience while preserving all existing backend,
routing, ML, SHAP, Supabase, and core journey functionality.

## Design Direction

- Modern, clean, premium safety-app aesthetic
- SAKHI pink/magenta brand identity
- White / very light pink backgrounds
- Dark charcoal text
- Rounded cards and controls
- Strong visual hierarchy
- Minimal decorative elements
- Accessibility-first
- Journey-first UX
- Bottom navigation

## Primary Navigation

Home
Journeys
Amenities
Profile

## Screens

### 1. Home / Journey Planner

Purpose:
Plan a journey.

Must include:
- SAKHI branding
- Accessibility control
- From location
- To location
- Find Safest Route CTA
- Recent journey information
- Bottom navigation

### 2. Route Results

Purpose:
Compare available routes.

Must include:
- Origin → Destination
- Route map
- Safest
- Balanced
- Fastest
- Risk score
- ETA
- Distance
- Washroom count
- Medical facility count
- Police / safety-point count
- Select route CTA

If only one route exists:
Show "Best available route" rather than
"Ranking unchanged."

### 3. Active Journey

Purpose:
Support the user while travelling.

Must include:
- Map
- Current location
- Destination
- Current route/risk status
- ETA
- Quick Find
- Report Incident
- SOS

Do not overload this screen with technical explanations.

### 4. Safety Details

Purpose:
Explain why a route/segment has its risk score.

Must include:
- Contextual risk score
- Confidence
- Risk level
- SHAP factors
- Segment information
- Report Incident

### 5. Quick Find

Purpose:
Give immediate access to nearby useful facilities.

Options:
- Need a washroom?
- Need medical help?
- Need police assistance?
- Fake "Call a Friend"

Results should show:
- Facility type/name
- Distance
- Walking time
- Navigate CTA

### 6. Incident Reporting

Purpose:
Allow users to report real-world safety conditions.

Categories:
- Poor lighting
- Harassment
- Unsafe crowd
- Infrastructure problem
- Other

Flow:
User report
→ validation
→ contextual update
→ risk recalculation
→ route recommendation update

### 7. Profile

Must include:
- Emergency contacts
- Safety preferences
- Accessibility
- Journey history
- Privacy & data

## Important UX Principles

- Don't expose developer/demo controls in normal user flow.
- Don't show technical implementation details unless useful to the user.
- Keep SHAP/explainability accessible through Safety Details.
- Keep emergency actions clearly accessible.
- Keep Quick Find accessible during a journey.
- Do not imply functionality that is only mocked/prototyped.
- Preserve existing working backend/API behavior.

## Technical Constraints

Do NOT change unless explicitly required:
- FastAPI APIs
- Supabase/PostGIS
- XGBoost
- SHAP
- Risk calculation
- Route generation
- Route ranking
- Existing backend contracts

The redesign should primarily modify the mobile presentation layer.

## Design Reference

Google Stitch ideation:
https://stitch.withgoogle.com/projects/11981710715436375218

The Stitch screens are visual references only.
Do not copy generated code directly.

## Implementation Order

1. Design system
2. Home
3. Route Results
4. Active Journey
5. Quick Find
6. Incident Reporting
7. Safety Details
8. Emergency
9. Profile
10. Final polish / consistency pass
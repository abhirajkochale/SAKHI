# SAKHI MASTER PROJECT PLAN

**Project:** SAKHI — Smart Assistance for keeping HER informed  
**Team ID:** SIH26_23 | **Team Name:** RVDIANs  
**Target Geography:** Delhi (NCT)  
**Last Audit Date:** August 21, 2026  
**Status:** Consolidated Canonical Repository  

---

## 1. EXECUTIVE SUMMARY (CURRENT STATE)

SAKHI is currently a highly advanced, technically functional **prototype**. Following the consolidation of the friend's Delhi-focused repository into the root codebase, SAKHI possesses a robust 13-feature contextual ML pipeline and a fully working React Native application with offline fallback and simulated dynamic route reranking.

However, despite its technical complexity, the project **does not yet meet the criteria for a scientifically validated, real-world deployment.** 

**What is Fully Complete (REAL):**
- **Infrastructure:** End-to-end FastAPI backend and Expo React Native mobile app.
- **Routing Engine:** OSRM integration extracting physical GPS paths.
- **Contextual Processing:** Spatial mapping of 13 features along route segments.
- **Heuristic Ranking:** Dynamic scoring of routes based on ML output + uncertainty penalty.
- **Offline Resilience:** SQLite journey caching (Mobile).
- **Device Features:** Accelerometer-based Shake-to-SOS, Dead-Man switch timer, Accessibility toggle.

**What is Simulated / Mocked (DEMO):**
- **ML Target Variable:** The XGBoost model predicts a heuristically derived *crime_grounded_risk_index* (calculated from district NCRB data * time-of-day weights), not granular observed segment-level crime incidents. 
- **Environmental Data:** Lighting, CCTV, footfall mobility, and crime hotspots are 100% *synthetic*.
- **Emergency Dispatch:** The SOS API returns a UUID but does not actually contact 112 or trusted contacts.
- **Context Updates:** Real-time safety reports are triggered manually via UI for demo purposes, not sourced from live user networks.

**What is Missing:**
- **User Feedback / Incident Reporting System:** (Crucial for faculty feedback).
- **Right to Pee / Amenities UI:** Backend has the data, but mobile app has zero UI for displaying/filtering amenities.
- **2025-26 Data:** All crime records end in 2023.

---

## 2. FACULTY FEEDBACK INTERPRETATION

1. **"Not much innovation"**
   - *Interpretation:* The evaluators see a standard "safe routing app" (OSRM + risk overlay). 
   - *Action:* We must pivot the core identity of SAKHI from a *static mapping app* to a **Continuous Feedback-Driven Safety Intelligence Network**. The innovation is NOT the map; the innovation is the explainable AI (SHAP) combined with a live, confidence-aware crowdsourced feedback loop that learns from user safety reports.

2. **"Add a mechanism for user feedback and incident reporting"**
   - *Interpretation:* The model cannot remain static. It needs an ingestion pipeline for real-time user experiences to correct stale or inaccurate risk predictions.
   - *Action:* Architect a complete crowdsourced reporting loop (UI -> API -> DB -> Retraining Pipeline).

3. **"Project validity is dataset driven"**
   - *Interpretation:* The evaluators noticed the reliance on synthetic data (lighting, CCTV) and district-level (non-granular) crime data.
   - *Action:* We must explicitly document our dataset limitations, replace synthetic data where open data exists, and introduce the "Confidence Score" heavily into the UI to transparently communicate data quality to the user.

4. **"Need to explore current dataset 2025-26. Obsolete suggestion will not work."**
   - *Interpretation:* 2018-2023 NCRB data is unacceptable for a 2026 hackathon finale.
   - *Action:* We must aggressively source recent Delhi Police press releases, RTI data, or crowdsourced 2025-26 datasets to update the historical baseline.

---

## 3. DATASET FRESHNESS & VALIDITY AUDIT

| Dataset | Type | Source / Location | Coverage | Validity / Status | Action Required |
|---------|------|-------------------|----------|-------------------|-----------------|
| **Crime Records** | REAL | NCRB (District level) | 2018–2023 | **OBSOLETE**. Fails 2025-26 faculty requirement. Lacks segment-level granularity. | **CRITICAL:** Supplement with 2025-26 Delhi Police open data or news-scraped proxy data. |
| **Police Stations** | REAL | Delhi Open Data | Current | Valid. Used for spatial distance calculations. | None. |
| **Hospitals/Medical** | REAL | Delhi Open Data | Current | Valid. Used for spatial distance calculations. | None. |
| **Public Amenities** | REAL | Delhi Open Data | Current | Valid. Backend calculates distance. | Needs Mobile UI integration. |
| **Population** | REAL | Census / Projections | 2023 proj | Acceptable, but could use 2025 updates. | Low priority update. |
| **Lighting** | SYNTHETIC | Generated script | N/A | **INVALID** for production claims. | Must replace with MCD (Municipal Corp) street light fault data if possible, or heavily penalize Confidence Score. |
| **CCTV** | SYNTHETIC | Generated script | N/A | **INVALID** for production claims. | Same as lighting. |
| **Hotspots** | SYNTHETIC | Generated script | N/A | **INVALID** for production claims. | Replace with derived hotspots from user incident reports (Phase 3). |
| **Mobility/Footfall**| SYNTHETIC | Generated script | N/A | **INVALID** for production claims. | Replace with TomTom/Google API traffic proxies if budget allows. |

---

## 4. ML VALIDITY STATUS

**Can we currently claim SAKHI has a validated real-world Delhi contextual safety model?**
**NO.**

**Why:**
1. **Target Construction (Circularity Risk):** The XGBoost model predicts `crime_grounded_risk_index`. This index is manually constructed using `crime_burden_per_100k` multiplied by a hardcoded `temporal_multiplier` (e.g., Late Night = 1.0, Day = 0.2). The ML model is simply learning to replicate this manual heuristic using environmental features.
2. **Synthetic Feature Reliance:** The model heavily weighs synthetic CCTV and lighting data.
3. **Evaluation Metrics:** No strict temporal/spatial holdout validation has been performed to prove the model predicts *future* or *unseen* risk accurately.

**Resolution:**
The model must be repositioned. If we cannot get segment-level observed crime targets, we must rebrand the ML output as a **"Contextual Vulnerability Score"** rather than a "Crime Prediction". The upcoming User Feedback pipeline will provide the actual ground-truth labels for future iterations.

---

## 5. REPOSITORY COMPONENT AUDIT

### A. Backend Services
- **OSRM Client / Segment Generation:** FULLY IMPLEMENTED (Real spatial mapping).
- **Risk Service (13-feature pipeline):** FULLY IMPLEMENTED.
- **XGBoost Inference:** FULLY IMPLEMENTED.
- **SHAP Service:** FULLY IMPLEMENTED (Working perfectly to explain risk).
- **Confidence Service:** FULLY IMPLEMENTED (Penalizes synthetic data).
- **Route Ranking:** FULLY IMPLEMENTED (Safest, Balanced, Fastest).
- **Context Update Service:** PARTIAL (Accepts API calls and reranks, but data is mocked).
- **Emergency / SOS:** PARTIAL (API returns UUID, does not contact authorities).

### B. Mobile App
- **Journey Form & Geocoding:** FULLY IMPLEMENTED (Nominatim).
- **Map & Risk Display (Colors):** FULLY IMPLEMENTED.
- **SHAP Explanations:** FULLY IMPLEMENTED.
- **Offline SQLite Cache:** FULLY IMPLEMENTED (Fallback works without internet).
- **Shake-to-SOS & Dead Man Switch:** FULLY IMPLEMENTED (Uses physical sensors).
- **Accessibility Mode:** FULLY IMPLEMENTED.
- **User Feedback / Incident Reporting UI:** **MISSING.**
- **Right to Pee / Amenities UI:** **MISSING.**

---

## 6. INNOVATION STRATEGY

To combat "not much innovation", SAKHI's architecture will pivot to:
**"A Self-Healing Safety Intelligence Network"**

**The 3 Innovation Pillars:**
1. **Explainable AI (XAI):** We don't just say a route is unsafe (Blackbox). We use SHAP to tell the user *exactly why* (e.g., "Poor lighting accounts for 40% of the risk here").
2. **Confidence-Aware Routing:** The system explicitly admits when it lacks data. If a route uses synthetic/stale data, the Confidence Score drops, and an "Uncertainty Penalty" is applied to the ranking.
3. **Crowdsourced Correction (The Loop):** When the system has low confidence, the user is prompted to provide a 5-second "Safety Observation" (e.g., "Streetlights are broken"). This feeds back into the ML pipeline, instantly updating the context for the next user and providing ground-truth data for nightly model retraining.

---

## 7. USER FEEDBACK + INCIDENT REPORTING PIPELINE (DESIGN)

**Architecture:**
1. **Mobile UI:** Floating "Report Safety Issue" FAB on the Map.
2. **Categories:** Lighting Issue, Harassment/Unsafe Individuals, Isolated Area, Safe/Well-lit (Positive feedback).
3. **Backend API:** `POST /feedback` (Captures segment_id, category, user_id, timestamp).
4. **Validation Layer:** "Trust Score" (Requires 3+ corroborating reports from different users to prevent spam/abuse, OR 1 report from a verified "Trusted User").
5. **Context Update:** Validated reports instantly call `ContextUpdateService` to inject a `validated_report` event, drastically altering the immediate risk score for that specific segment for 24 hours.
6. **ML Retraining Pipeline:** Weekly chron job pulls all feedback from SQLite/Postgres, converts them into ground-truth target variables, and retrains the XGBoost model.

---

## 8. MASTER TASK FLOW (CRITICAL PATH)

*Tasks are ordered by Dependency, Faculty Feedback, and Project Validity.*

### PHASE 1: Data Freshness & Amenities (Addressing Faculty Feedback)
- [ ] **TASK 1.1:** Hunt and scrape 2025-26 Delhi crime statistics (News reports, Delhi Police Twitter/Press releases, RTI portals).
- [ ] **TASK 1.2:** Update `ml/data/raw/crime_records.csv` with 2025-26 baseline approximations.
- [ ] **TASK 1.3:** Build "Right to Pee" Mobile UI. Fetch `distance_to_nearest_amenity_m` from backend and overlay nearest safe public toilets as POI markers on the `JourneyMap`.

### PHASE 2: User Feedback Innovation (The "Loop")
- [ ] **TASK 2.1:** Create `FeedbackService` in backend (schemas, SQLite models for incident reports).
- [ ] **TASK 2.2:** Build Mobile "Report Incident" Modal (Categories, Location capture).
- [ ] **TASK 2.3:** Wire Mobile Form to Backend `POST /feedback`.
- [ ] **TASK 2.4:** Build Validation Logic (If 2+ reports on same segment -> Trigger ContextUpdateService).

### PHASE 3: ML Validity & Retraining Integration
- [ ] **TASK 3.1:** Write `ml/retrain_pipeline.py` to ingest the new SQLite incident reports and map them to segment IDs.
- [ ] **TASK 3.2:** Refactor ML Target definition. Separate the "Static Baseline" from "Crowdsourced Ground Truth".
- [ ] **TASK 3.3:** Run comprehensive Train/Test holdout validation and document metrics (RMSE, MAE).
- [ ] **TASK 3.4:** Generate final 2026 Model Metadata and SHAP values.

### PHASE 4: Emergency Integration & Polish
- [ ] **TASK 4.1:** Upgrade SOS Backend API to integrate with a real SMS gateway (e.g., Twilio/Fast2SMS) for trusted contacts (Optional but high impact).
- [ ] **TASK 4.2:** E2E Testing of Shake-to-SOS -> SMS Delivery.
- [ ] **TASK 4.3:** UI/UX Polish (Animations, Loading states, Error handling for Offline recovery).

---

## 9. MILESTONES

- **M1 — Repository Stable:** (ACHIEVED) Codebases merged, tests passing.
- **M2 — Data 2026 Updated:** 2025-26 datasets integrated into baselines.
- **M3 — Amenities Live:** Right to Pee UI fully functional on mobile.
- **M4 — The Feedback Loop:** Crowdsourced incident reporting UI and API functioning.
- **M5 — Final ML Model:** Model retrained with clear validation metrics, eliminating synthetic reliance where possible.
- **M6 — SIH Final Build:** Production deployment, presentation deck aligned with the "Self-Healing Network" innovation strategy.

---

## 10. IMMEDIATE NEXT TASK

**TASK 1.3: Build "Right to Pee" Amenities UI**
*Why:* The backend already calculates distance to amenities, but the mobile app completely ignores it. This is a massive, highly visible feature for women's safety that requires zero new ML or Data hunting. It can be implemented immediately in parallel while the team searches for 2025-26 crime data.


## 11. FEATURE PRIORITY DECISION � USER REPORTING vs CALL A FRIEND

**Current state:**
- **Feature A (Identity + Reporting):** Incident reporting UI and Backend API exist and dynamically affect risk. However, it lacks User Identity, making it vulnerable to spam and breaking the ML loop validity.
- **Feature B (Call a Friend):** UI exists and simulates a call timer, but lacks any audio generation (Sarvam AI) or local playback capabilities (expo-av).

**Remaining work:**
- **Feature A:** User schema, anonymous tracking (Expo UUID), Trust scoring, Validation API, Retraining script.
- **Feature B:** expo-av setup, Sarvam API proxy, local audio asset bundling.

**Zero-cost feasibility:**
Both are feasible for zero cost. Feature A can use secure device UUIDs. Feature B can use the Sarvam free tier and bundled local fallback audio.

**Faculty feedback & Innovation relevance:**
- Feature A directly addresses the faculty's main critique (Dataset validity and lack of innovation) by proving SAKHI is a self-healing intelligence network.
- Feature B is an impressive demo utility but does not improve the core ML engine.

**Recommended order:**
**Build both in parallel, but Feature A is the primary priority.**

**Exact next task:**
Implement Zero-Cost User Identity Foundation (Device UUID tracking for Trust Scoring).

**Parallel work that can begin:**
Install and configure expo-av for Feature B.


## 12. SAKHI IDENTITY & VERIFIED SAFETY REPORTING

**Status: PARTIAL (Foundation Implemented)**

**Implemented:**
- Google Sign-In via Supabase OAuth (Expo WebBrowser).
- Backend JWT Verification via Supabase JWKS (Asymmetric RS256).
- SAKHI User Model (id, email, identity_status).
- Incident Authentication (POST /incidents now requires a valid JWT and assigns the reporter's user_id).

**Planned (Next Phase):**
- Sandbox Aadhaar OTP proxy (FastAPI).
- Sandbox e-KYC integration.
- Verified Status UI.

**Security & Privacy:**
- The frontend only knows the Supabase session token.
- The backend fetches the public JWKS to verify signatures independently.
- No client-provided user_ids are trusted; the backend extracts it directly from the token payload.
- SAKHI users start as NORMAL. Duplicate logins fetch the same account idempotently.

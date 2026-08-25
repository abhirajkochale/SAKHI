A. CURRENT PROJECT STATUS
The SAKHI project currently possesses a functional end-to-end prototype.
FULLY IMPLEMENTED: OSRM routing, risk generation, XGBoost ML inference, SHAP explanations, Route Ranking, Washroom UI ("Show nearby washrooms"), and Incident Reporting (API and Mobile Form).
PARTIALLY IMPLEMENTED: Context Update Service (updates risk, but lacks user identity/trust).
DEMO/SIMULATED: Emergency API (returns UUID without real SMS), "Call a Friend" (simulated countdown, no audio), Data (Heavy reliance on synthetic lighting/CCTV data).
MISSING: Real User Identity, Report Validation/Trust Scoring, Real SMS Dispatch, Sarvam AI TTS integration.

B. FACULTY FEEDBACK STATUS
1. "Not much innovation": SAKHI’s explainability (SHAP) is strong, but the core innovation must lie in crowdsourced self-healing networks. Currently, reports immediately affect risk but lack identity to prevent spoofing.
2. "User feedback and incident reporting": UI and endpoints exist, but the lack of identity/trust mechanisms makes the system vulnerable in a real-world scenario.
3. "Dataset validity": Model heavily relies on synthetically derived indexes.
4. "2025-26 data": Not present in the repository.

C. DATA / ML STATUS
The current ML pipeline predicts a derived `crime_grounded_risk_index` utilizing synthetic features (lighting, CCTV) and 2018-2023 NCRB baseline data. To achieve true validity, SAKHI requires real ground-truth inputs (via Feature A) to retrain the XGBoost weights. 

D. FEATURE A — USER IDENTITY + INCIDENT REPORTING
- Current implementation: The base Incident API (`/incidents/`) and `ReportIncidentModal.tsx` are fully functional and instantly trigger the `ContextUpdateService` to recalculate route risk.
- Missing pieces: User database, Identity verification (Auth), Trust/Spam scoring for incidents, Corroboration logic, and the Retraining chron-job.
- Dependencies: None blocked. Backend requires a `User` schema and table.
- Zero-cost feasibility: HIGH. Can use free Firebase Auth, Expo device UUIDs, or Google Sign-In.
- Innovation value: VERY HIGH. Anchors the "Self-Healing Network" claim.
- Effort: MEDIUM-HIGH (Requires auth state management and API middleware).
- Risks: Authentication edge cases can break the seamless mobile UX if not implemented cleanly.

E. FEATURE B — CALL A FRIEND + SARVAM
- Current implementation: Static React Native UI exists (`QuickFindModal.tsx`). It simulates an active call with a timer.
- Missing pieces: `expo-av` integration, Sarvam TTS backend proxy, offline audio bundled assets, dynamic script generation.
- Dependencies: Requires `expo-av` installation.
- Zero-cost feasibility: MEDIUM. Sarvam AI has a free tier but usage must be monitored carefully during development and the demo. Offline bundled audio is free but increases APK size.
- Innovation value: LOW-MEDIUM. It is a fantastic UX safety feature, but technically it is a standard API integration. It does not innovate the core ML risk engine.
- Effort: MEDIUM.
- Risks: Sarvam latency could ruin the emergency illusion. Audio playback in React Native can have edge cases across iOS/Android.

F. SIDE-BY-SIDE COMPARISON TABLE
| Criterion | Feature A (Identity/Trust) | Feature B (Call + Sarvam) |
|---|---|---|
| Core ML Impact | High | None |
| Faculty Alignment | Very High | Low |
| Innovation Value | Very High | Medium |
| Demo UX Value | Medium | Very High |
| Implementation Effort | Medium-High | Medium |
| Cost Risk | Zero | Low/Medium |

G. PARALLELIZATION ANALYSIS
These two features touch entirely different parts of the system and CAN be developed in parallel without conflicts.
Feature A modifies Backend Auth, Incident schemas, Context validation, and ML Retraining pipelines.
Feature B modifies Mobile Audio APIs (`expo-av`), `QuickFindModal.tsx`, and a new Backend `/audio` proxy endpoint.

H. RECOMMENDED PRIORITY
While both features are feasible, Feature A is the PRIMARY architectural priority. The faculty explicitly critiqued the project's innovation and dataset validity. The only way to prove the project is a living, intelligent system rather than a static map is to implement a robust Identity and Trust loop for incident reporting. An anonymous incident report system is a vulnerability, not an innovation.

Feature B is an exceptional UX addition and will shine during the demo, but it does not address the fundamental academic critiques of the ML pipeline.

I. EXACT NEXT TASK
TASK 1: Implement Zero-Cost User Identity Foundation.
(Generate a unique Device UUID in Expo on first launch, store it in SecureStore, and register it with a new Backend `users` table to create a shadow-account for anonymous yet trackable trust scoring).

J. NEXT 5 TASKS AFTER THAT
2. Update `Incident` schema and API to enforce `user_id`.
3. Implement Incident Trust Scoring (e.g., trust += 1 if user reports match other users).
4. Update `ReportIncidentModal.tsx` to handle shadow-account injection.
5. Create `ml/retrain_pipeline.py` script to map new user incidents to segment risk features.
6. Begin parallel development of Feature B by installing `expo-av`.

K. UPDATED MASTER PROJECT PLAN
The MASTER_PROJECT_PLAN.md file will be appended with this strategic decision.

L. BLOCKERS / RISKS
- Blockers: None currently. 
- Risks: Implementing Auth (Even shadow auth) requires careful state management in React Native to prevent infinite loading screens on first launch.

M. TESTS / VERIFICATION REQUIRED
- Ensure anonymous incidents are rejected by the backend.
- Ensure the shadow-account is persisted across app restarts.
- Verify that a reported incident only triggers context updates if the user's trust score is above the required threshold.

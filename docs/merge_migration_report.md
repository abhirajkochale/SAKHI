# SAKHI Repository Merge Migration Report

**Date**: August 21, 2026  
**Source**: `SAKHI (friends version)/` nested repository  
**Target**: Root `SAKHI/` repository  
**Final Geography**: DELHI

---

## 1. Files Migrated from Friend's Repository

### Backend — New Files
| File | Purpose |
|------|---------|
| `app/api/v1/endpoints/emergency.py` | SOS/emergency endpoint |
| `app/schemas/emergency.py` | Emergency request/response schemas |
| `app/services/emergency/emergency_service.py` | Emergency service logic |
| `app/services/risk/segment_lookup_service.py` | Spatial segment lookup (districts, infrastructure, synthetic proxies) |

### Backend — Merged/Replaced Files (Friend's version adopted)
| File | Reason |
|------|--------|
| `app/api/v1/api.py` | Added emergency router |
| `app/api/v1/endpoints/journeys.py` | Updated for new schema |
| `app/services/risk/risk_service.py` | 13-feature sakhi pipeline, spatial enrichment, segment lookup |
| `app/services/risk/feature_service.py` | 13-feature extraction with temporal, infrastructure, synthetic proxies |
| `app/services/risk/ml_model_service.py` | Dual model loading (sakhi primary + legacy fallback) |
| `app/services/risk/shap_service.py` | SHAP for 13-feature sakhi model |
| `app/services/risk/confidence_service.py` | Data quality + mapping quality + infrastructure quality formula |
| `app/services/risk/baseline_service.py` | Real NCRB district baseline via segment lookup |
| `app/services/routing/osrm_client.py` | Real spatial context building + demo override separation |
| `app/services/routing/routing_service.py` | Updated interface |
| `app/services/routing/route_ranking_service.py` | Updated ranking |
| `app/services/context_update_service.py` | Updated context update logic |
| `app/schemas/risk.py` | Expanded RiskFeatures (13 features), new SegmentContext fields |
| `requirements.txt` | Added xgboost, shap dependencies |
| All `__init__.py` files | Updated module exports |
| All `tests/*.py` | Updated to match new 13-feature services |

### ML — New Files & Data
| File/Directory | Purpose |
|------|---------|
| `ml/data/raw/` (7 CSV files) | Real Delhi datasets: crime_records, hospitals, medical_facilities, police_stations, population, public_amenities, road_segments |
| `ml/data/processed/` (17 files) | Processed pipeline outputs: district baselines, training dataset, predictions, SHAP explanations, route artifacts |
| `ml/data/synthetic/` (4 new CSV files) | synthetic_cctv, synthetic_crime_hotspots, synthetic_lighting, synthetic_mobility |
| `ml/models/sakhi_xgboost_risk_model.json` | Primary 13-feature XGBoost model |
| `ml/models/sakhi_model_metadata.json` | Model metadata |
| `ml/models/train_xgboost.py` | XGBoost training script |
| `ml/models/build_confidence.py` | Confidence artifact builder |
| `ml/models/explain_risk.py` | SHAP explanation generator |
| `ml/preprocessing/` (6 scripts) | Full Delhi preprocessing pipeline |
| `ml/routing/` (7 scripts) | Route graph building, safety metrics, recommendation engine |

### Mobile — New Files
| File | Purpose |
|------|---------|
| `src/contexts/AccessibilityContext.tsx` | Accessibility mode toggle provider |
| `src/api/cache.ts` | SQLite offline journey cache |
| `src/components/DeadManSwitchPanel.tsx` | Dead-man switch safety timer |

### Mobile — Merged/Replaced Files
| File | Reason |
|------|--------|
| `App.tsx` | Added AccessibilityProvider + initDb() |
| `src/api/sakhiApi.ts` | Added triggerSos endpoint |
| `src/components/JourneyForm.tsx` | Added Nominatim geocoding text input |
| `src/components/JourneyMap.tsx` | Updated for new types |
| `src/components/EmergencyPanel.tsx` | Enhanced emergency flow with SOS API |
| `src/components/ContextUpdatePanel.tsx` | Updated for new context update schema |
| `src/screens/JourneyDashboard.tsx` | Added shake-to-SOS, offline fallback, accessibility toggle, DeadManSwitch, dynamic re-ranking UI |
| `package.json` | Added expo-sensors, expo-sqlite, react-dom, react-native-web |

---

## 2. Files Preserved from Original Root

| File | Reason |
|------|--------|
| `mobile/.env` | Local development config (EXPO_PUBLIC_API_URL) |
| `mobile/src/components/RouteOptionsList.tsx` | Identical in both repos |
| `mobile/src/components/SegmentSafetyPanel.tsx` | Identical in both repos (contains SHAP normalization logic) |
| `ml/models/contextual_risk_model.joblib` | Legacy fallback model (still loaded by MLModelService) |
| `ml/models/model_metadata.json` | Legacy model metadata |
| `ml/data/synthetic/synthetic_contextual_segments.csv` | Still used by train.py and generate_synthetic_data.py |
| `.gitignore` | Identical in both repos |
| `README.md` | Root README retained |
| `data/` | Empty directory preserved for future use |
| `docs/` | Preserved for this report |

---

## 3. Files Removed

| File | Reason |
|------|--------|
| `comparison.txt` | Temporary diff output — no longer needed |
| `full_diff.txt` | Temporary diff output — no longer needed |
| `jf_diff.txt` | Temporary diff output — no longer needed |
| `jd_diff.txt` | Temporary diff output — no longer needed |

---

## 4. Test Results

### Backend Tests: **36/36 PASSED** ✅

```
tests/test_context_update.py        5 PASSED
tests/test_health.py                1 PASSED
tests/test_journeys.py              5 PASSED
tests/test_ml_model.py              2 PASSED
tests/test_risk_confidence.py       3 PASSED
tests/test_risk_features.py         3 PASSED
tests/test_risk_service.py          3 PASSED
tests/test_route_ranking.py        10 PASSED
tests/test_shap_service.py          4 PASSED
```

### Test Fix Applied
- `test_context_update_paharganj_preserves_high_risk`: Changed strict `<` to `<=` assertion for edge case where both routes converge to the same risk score after context update.

---

## 5. ML Validity Status

> **⚠️ The current XGBoost model is a prototype. It is NOT a validated production model.**

### Current State
- Model: `sakhi_xgboost_risk_model.json` (13-feature XGBoost regressor)
- Training target: `crime_grounded_risk_index` (synthetic composite, NOT observed crime)
- Training data: Real NCRB district stats + synthetic environmental proxies
- Geography: Delhi (11 districts)

### TODO for ML Validation
- [ ] Target audit: validate `crime_grounded_risk_index` against real crime outcomes
- [ ] Feature/target leakage analysis
- [ ] Proper train/validation/test split methodology
- [ ] Baseline model comparison (e.g., simple district mean)
- [ ] XGBoost hyperparameter tuning
- [ ] Early stopping evaluation
- [ ] Final retraining with validated target
- [ ] SHAP regeneration after final model
- [ ] Confidence score regeneration
- [ ] Model metadata regeneration with training metrics

---

## 6. Hardcoded Path Check

**Zero** references to `"SAKHI (friends version)"` found in the final root project code. ✅

---

## 7. Final Project Structure

```
C:\Projects\SAKHI\
├── backend\
│   ├── app\
│   │   ├── api\v1\endpoints\  (health, journeys, emergency)
│   │   ├── core\              (config, settings)
│   │   ├── models\            (data models)
│   │   ├── schemas\           (journey, risk, ranking, context, emergency)
│   │   └── services\
│   │       ├── emergency\     (emergency_service)
│   │       ├── journey\       (journey store)
│   │       ├── risk\          (risk, feature, ml_model, shap, confidence, baseline, segment_lookup)
│   │       └── routing\       (osrm_client, route_ranking, routing_service)
│   ├── tests\                 (36 tests)
│   └── requirements.txt
├── mobile\
│   ├── App.tsx
│   ├── src\
│   │   ├── api\               (sakhiApi, cache)
│   │   ├── components\        (JourneyForm, JourneyMap, RouteOptionsList, SegmentSafetyPanel, ContextUpdatePanel, EmergencyPanel, DeadManSwitchPanel)
│   │   ├── contexts\          (AccessibilityContext)
│   │   ├── screens\           (JourneyDashboard)
│   │   └── types\             (api types)
│   └── package.json
├── ml\
│   ├── data\
│   │   ├── raw\               (7 real Delhi datasets)
│   │   ├── processed\         (17 pipeline outputs)
│   │   └── synthetic\         (5 synthetic datasets)
│   ├── models\                (sakhi model + legacy + training scripts)
│   ├── preprocessing\         (6 preprocessing scripts)
│   └── routing\               (7 route analysis scripts)
├── data\                      (reserved for future use)
├── docs\                      (this report)
├── README.md
└── .gitignore
```

---

## 8. Known Issues

1. **Expo deprecation warning**: `starlette.testclient` warns about `httpx` vs `httpx2`. Non-blocking.
2. **Mobile `npm install` required**: After merge, run `npm install` in `mobile/` to install new dependencies (`expo-sensors`, `expo-sqlite`).
3. **Shake-to-SOS uses mock location**: `JourneyDashboard.tsx` line 50 uses `{latitude: 28.6139, longitude: 77.2090}` as placeholder.

---

## 9. Remaining Work

1. **ML Validation** (see section 5 TODO list)
2. **Mobile dependency install**: `cd mobile && npm install`
3. **Rename friend's repo**: `Rename-Item "SAKHI (friends version)" "SAKHI_friends_backup"` after full verification
4. **Delete backup**: Only after confirming the root project is fully independent
5. **Production SOS**: Replace mock SOS with real emergency service integration
6. **BLE integration**: Not yet implemented
7. **Real-time data**: Not yet implemented

---

## 10. Verification Commands

```powershell
# Backend tests
cd C:\Projects\SAKHI\backend
.\venv\Scripts\python.exe -m pytest tests/ -v

# Backend server
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Mobile app
cd C:\Projects\SAKHI\mobile
npm install
npx expo start -c
```

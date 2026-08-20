"""
MLModelService
==============
Loads and runs the primary safhera XGBoost contextual risk model.

Primary model : ml/models/safhera_xgboost_risk_model.json
  - 27 features, trained on ml_training_dataset.csv
  - Loaded via xgboost XGBRegressor.load_model()

Legacy fallback: ml/models/contextual_risk_model.joblib
  - 10 simple synthetic features
  - Loaded via joblib
  - Used ONLY if the primary model fails to load

IMPORTANT: The primary model uses a SYNTHETIC prototype target.
It is NOT trained on observed crime events. See training metadata.
"""

import os
import json
from typing import Optional, Dict, Any, List
import pandas as pd

from app.schemas.risk import RiskFeatures

# Primary 27-feature list — must match ml/models/train_xgboost.py FEATURES exactly
SAFHERA_FEATURE_ORDER: List[str] = [
    "historical_baseline",
    "cases_per_100k",
    "severity_weighted_cases_per_100k",
    "recent_cases_per_100k",
    "recent_severity_per_100k",
    "crime_trend_slope",
    "distance_m",
    "estimated_travel_time_s",
    "lighting_score",
    "cctv_coverage_score",
    "footfall_proxy",
    "contextual_footfall_proxy",
    "distance_to_police_m",
    "distance_to_hospital_m",
    "distance_to_medical_facility_m",
    "distance_to_public_toilet_m",
    "distance_to_nearest_amenity_m",
    "nearest_hotspot_distance_m",
    "nearest_hotspot_intensity",
    "representative_hour",
    "is_night",
    "is_late_night",
    "is_evening_peak",
    "is_weekend",
    "is_peak_hour",
    "reduced_activity_context",
    "lighting_relevance",
]


class MLModelService:
    """
    Manages loading and inference for the SAKHI contextual risk models.
    Falls back gracefully if the primary model is unavailable.
    """

    def __init__(self, models_dir: Optional[str] = None):
        self._primary_model = None          # XGBRegressor (safhera 27-feature)
        self._legacy_model = None           # joblib model (synthetic 10-feature)
        self._metadata: Dict[str, Any] = {}
        self._model_source: str = "none"

        if models_dir is None:
            here = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.normpath(
                os.path.join(here, "..", "..", "..", "..", "ml", "models")
            )

        # ── Load primary safhera model ───────────────────────────────────
        primary_path = os.path.join(models_dir, "safhera_xgboost_risk_model.json")
        if os.path.exists(primary_path):
            try:
                import xgboost as xgb
                m = xgb.XGBRegressor()
                m.load_model(primary_path)
                self._primary_model = m
                self._model_source = "xgboost_safhera"
                # Load metadata
                meta_path = os.path.join(models_dir, "safhera_model_metadata.json")
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        self._metadata = json.load(f)
                else:
                    self._metadata = {
                        "model_name": "sakhi_safhera_contextual_risk",
                        "model_version": "safhera-v1",
                        "model_source": "xgboost_safhera",
                        "feature_names": SAFHERA_FEATURE_ORDER,
                        "feature_count": len(SAFHERA_FEATURE_ORDER),
                        "dataset_type": "real_ncrb_district_plus_synthetic_proxy",
                        "target_is_observed_crime": False,
                    }
            except Exception as e:
                print(f"[MLModelService] Failed to load primary safhera model: {e}")

        # ── Load legacy fallback model if primary unavailable ────────────
        if self._primary_model is None:
            legacy_path = os.path.join(models_dir, "contextual_risk_model.joblib")
            if os.path.exists(legacy_path):
                try:
                    import joblib
                    self._legacy_model = joblib.load(legacy_path)
                    self._model_source = "xgboost_legacy"
                    legacy_meta = os.path.join(models_dir, "model_metadata.json")
                    if os.path.exists(legacy_meta):
                        with open(legacy_meta, "r") as f:
                            self._metadata = json.load(f)
                    print("[MLModelService] WARNING: Using legacy synthetic-only model as fallback.")
                except Exception as e:
                    print(f"[MLModelService] Failed to load legacy model: {e}")

        if self._primary_model is None and self._legacy_model is None:
            print("[MLModelService] No model loaded — will use heuristic fallback.")

    # ── Status ────────────────────────────────────────────────────────────

    def is_primary_available(self) -> bool:
        return self._primary_model is not None

    def is_any_model_available(self) -> bool:
        return self._primary_model is not None or self._legacy_model is not None

    def is_available(self) -> bool:
        return self.is_any_model_available()

    def get_metadata(self) -> Dict[str, Any]:
        return self._metadata

    def get_model_source(self) -> str:
        return self._model_source

    # ── Primary inference (27-feature safhera model) ─────────────────────

    def predict(self, features: RiskFeatures) -> Optional[float]:
        """
        Run inference with the primary safhera 27-feature XGBoost model.
        Returns None if primary model is unavailable (triggers heuristic fallback).
        """
        if self._primary_model is None:
            return None

        feature_dict = features.model_dump()
        # Validate all required features are present
        missing = [f for f in SAFHERA_FEATURE_ORDER if f not in feature_dict]
        if missing:
            print(f"[MLModelService] Missing features for primary model: {missing}")
            return None

        input_data = {f: [feature_dict[f]] for f in SAFHERA_FEATURE_ORDER}
        df_input = pd.DataFrame(input_data)

        try:
            pred = self._primary_model.predict(df_input)[0]
            return float(max(0.0, min(100.0, pred)))
        except Exception as e:
            print(f"[MLModelService] Primary inference error: {e}")
            return None

    def get_booster(self):
        """Return the underlying XGBoost Booster for SHAP TreeExplainer."""
        if self._primary_model is not None:
            return self._primary_model
        return None

    def get_feature_names(self) -> List[str]:
        """Return the feature name list for the active primary model."""
        return SAFHERA_FEATURE_ORDER

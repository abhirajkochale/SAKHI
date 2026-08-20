"""
SHAPService
===========
Generates SHAP explanations for the sakhi XGBoost contextual risk model.
Uses TreeExplainer — optimized for XGBoost.

IMPORTANT: SHAP explains the model's behaviour on its synthetic prototype target.
It does NOT explain why a crime will happen. It explains which contextual features
(lighting, proximity to police, time of night, etc.) contributed most to the
contextual risk score for this segment.
"""

import pandas as pd
from typing import Optional, List

from app.schemas.risk import RiskFeatures, RiskExplanation, SHAPContribution
from app.services.risk.ml_model_service import MLModelService, SAKHI_FEATURE_ORDER


class SHAPService:
    """Generates SHAP feature-contribution explanations for the risk model."""

    def __init__(self, ml_service: MLModelService):
        self.ml_service = ml_service
        self.explainer = None

        booster = self.ml_service.get_booster()
        if booster is not None:
            try:
                import shap
                self.explainer = shap.TreeExplainer(booster)
            except Exception as e:
                print(f"[SHAPService] TreeExplainer init failed: {e}")
                self.explainer = None

    def explain(self, features: RiskFeatures, predicted_risk: float) -> RiskExplanation:
        """
        Generate SHAP contributions for each of the 27 risk features.
        Falls back gracefully if model/explainer is unavailable.
        """
        if not self.ml_service.is_primary_available() or self.explainer is None:
            return RiskExplanation(
                available=False,
                reason=(
                    "SHAP explanation unavailable: XGBoost sakhi model is not active. "
                    "Using heuristic fallback."
                ),
            )

        feature_dict = features.model_dump()
        feature_names = SAKHI_FEATURE_ORDER

        # Validate all features present
        missing = [f for f in feature_names if f not in feature_dict]
        if missing:
            return RiskExplanation(
                available=False,
                reason=f"SHAP: feature schema mismatch, missing: {missing}",
            )

        input_data = {f: [feature_dict[f]] for f in feature_names}
        df_input = pd.DataFrame(input_data)

        try:
            shap_values_obj = self.explainer(df_input)
            shap_values = shap_values_obj.values[0]
            base_value = float(shap_values_obj.base_values[0])

            contributions: List[SHAPContribution] = []
            for i, feat_name in enumerate(feature_names):
                shap_val = float(shap_values[i])
                feat_val = float(feature_dict[feat_name])
                direction = "increases_risk" if shap_val > 0 else "decreases_risk"
                contributions.append(
                    SHAPContribution(
                        feature_name=feat_name,
                        feature_value=feat_val,
                        shap_value=round(shap_val, 4),
                        direction=direction,
                    )
                )

            # Sort by absolute SHAP magnitude
            contributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
            positive_factors = [c for c in contributions if c.shap_value > 0]
            negative_factors = [c for c in contributions if c.shap_value <= 0]

            return RiskExplanation(
                available=True,
                base_value=round(base_value, 4),
                predicted_risk=round(predicted_risk, 2),
                top_positive_factors=positive_factors[:3],
                top_negative_factors=negative_factors[:3],
                all_contributions=contributions,
            )

        except Exception as e:
            return RiskExplanation(
                available=False,
                reason=f"SHAP calculation error: {type(e).__name__}",
            )

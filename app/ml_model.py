# app/ml_model.py
import os
import joblib
from typing import Any, Dict
import numpy as np

MODEL_PATH = os.getenv("ML_MODEL_PATH", "models/dummy_model.joblib")

class MLModel:
    def __init__(self, path=MODEL_PATH):
        self.path = path
        self.bundle = None
        self._load()

    def _load(self):
        try:
            self.bundle = joblib.load(self.path)
            # expected bundle: {'model': clf, 'encoder': encoder_or_none}
        except Exception as e:
            print("ML model load error:", e)
            self.bundle = None

    def predict_water(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        features expected keys: soil_moisture, air_temp_c, air_humidity_pct, light_lux, species, days_since_water
        returns: {'water_now': bool, 'score': float}
        """
        if not self.bundle:
            return {"water_now": False, "score": 0.0, "reason": "no-model"}
        try:
            clf = self.bundle.get("model")
            enc = self.bundle.get("encoder")  # optional
            X_num = [features.get("soil_moisture", 0.0),
                     features.get("air_temp_c", 0.0),
                     features.get("air_humidity_pct", 0.0),
                     features.get("light_lux", 0.0),
                     features.get("days_since_water", 0.0)]
            X_num = np.array(X_num).reshape(1, -1)
            if enc and "species" in features:
                sp_o = enc.transform([[features.get("species")]])
                X = np.hstack([X_num, sp_o])
            else:
                X = X_num
            proba = clf.predict_proba(X)[0][1] if hasattr(clf, "predict_proba") else None
            pred = bool(clf.predict(X)[0])
            return {"water_now": pred, "score": float(proba) if proba is not None else None, "reason": "model"}
        except Exception as e:
            return {"water_now": False, "score": 0.0, "reason": f"error:{e}"}

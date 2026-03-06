# routers/deepface.py
from __future__ import annotations

import base64
import time
from typing import Dict, Any, Optional, Tuple

import cv2
import numpy as np
from deepface import DeepFace


# -----------------------------
# Session-level smoothing cache
# -----------------------------
# session_id -> {"ema": {emotion: val}, "ts": float}
_EMA_CACHE: Dict[str, Dict[str, Any]] = {}

# DeepFace emotion labels typically:
# angry, disgust, fear, happy, sad, surprise, neutral
_EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


def _b64_to_bgr(image_base64: str) -> np.ndarray:
    """
    Accepts either raw base64 or dataURL ("data:image/jpeg;base64,...")
    Returns BGR ndarray (OpenCV format).
    """
    if not image_base64:
        raise ValueError("empty image_base64")

    # strip dataURL header if present
    if "," in image_base64 and image_base64.strip().lower().startswith("data:image"):
        image_base64 = image_base64.split(",", 1)[1]

    img_bytes = base64.b64decode(image_base64)
    img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("cv2.imdecode failed")
    return bgr


def _quality_check(bgr: np.ndarray) -> Tuple[bool, str]:
    """
    Lightweight quality gate to reduce false 'fear/anxiety spikes'.
    - too small image
    - too blurry
    """
    h, w = bgr.shape[:2]
    if h < 80 or w < 80:
        return False, "too_small"

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # blur metric (variance of Laplacian)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 20:  # conservative
        return False, "too_blurry"

    return True, "ok"


def _normalize_emotion_dist(dist: Dict[str, float]) -> Dict[str, float]:
    """
    DeepFace returns emotion values often as percentages summing ~100.
    Normalize to 0..1 and ensure all keys exist.
    """
    out = {k: float(dist.get(k, 0.0)) for k in _EMOTIONS}
    s = sum(out.values())
    if s <= 0:
        return {k: 0.0 for k in _EMOTIONS}
    # If it's percent-like, dividing by sum is robust either way.
    return {k: out[k] / s for k in _EMOTIONS}


def _ema_update(session_id: str, now: float, current: Dict[str, float], alpha: float) -> Dict[str, float]:
    """
    Exponential Moving Average over time for stability.
    alpha: higher -> reacts faster
    """
    prev = _EMA_CACHE.get(session_id, {}).get("ema")
    if not prev:
        ema = dict(current)
    else:
        ema = {k: (alpha * current[k] + (1 - alpha) * float(prev.get(k, 0.0))) for k in _EMOTIONS}

    _EMA_CACHE[session_id] = {"ema": ema, "ts": now}
    return ema


def _dominant_with_fallback(scores: Dict[str, float]) -> Tuple[str, float, str]:
    """
    Practical rule:
    - If top score is weak OR top-2 are too close -> neutral
    - If fear is top but neutral is close -> neutral
    """
    items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_label, top_val = items[0]
    second_label, second_val = items[1]

    # thresholds tuned for "false anxiety spike" suppression
    MIN_CONF = 0.55          # below -> ambiguous
    MIN_MARGIN = 0.12        # top must beat 2nd by this much

    if top_val < MIN_CONF:
        return "neutral", scores.get("neutral", 0.0), "fallback_low_conf"

    if (top_val - second_val) < MIN_MARGIN:
        return "neutral", scores.get("neutral", 0.0), "fallback_small_margin"

    if top_label == "fear" and (scores.get("neutral", 0.0) >= top_val - 0.15):
        return "neutral", scores.get("neutral", 0.0), "fallback_fear_vs_neutral"

    return top_label, top_val, "ok"


def analyze_face_logic(session_id: str, image_base64: str) -> Dict[str, Any]:
    """
    Robust emotion analysis for realtime usage.
    Returns:
      {
        "status": "success" | "no_face" | "error",
        "dominant": str,
        "score": float (0..1),
        "scores": {emotion: float (0..1)},
        "reason": str,
        "meta": {...}
      }
    """
    t0 = time.time()

    try:
        bgr = _b64_to_bgr(image_base64)
        okq, q_reason = _quality_check(bgr)
        if not okq:
            return {
                "status": "no_face",
                "dominant": "neutral",
                "score": 0.0,
                "scores": {k: 0.0 for k in _EMOTIONS},
                "reason": q_reason,
                "meta": {"latency_ms": int((time.time() - t0) * 1000)},
            }

        # Resize to reduce jitter + speed up (realtime standard trick)
        h, w = bgr.shape[:2]
        max_side = max(h, w)
        if max_side > 640:
            scale = 640 / max_side
            bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # DeepFace analyze
        # - detector_backend="retinaface" : robust in many cases
        # - enforce_detection=False       : realtime에서 "얼굴 못찾음"으로 끊기는 것 방지
        # - align=True                    : 정렬이 감정 흔들림 줄여줌
        result = DeepFace.analyze(
            img_path=rgb,
            actions=["emotion"],
            detector_backend="retinaface",
            enforce_detection=False,
            align=True,
            silent=True,
        )

        # result can be list[dict] or dict depending on versions
        if isinstance(result, list):
            result = result[0] if result else {}

        emotion_dist_raw = (result.get("emotion") or {}) if isinstance(result, dict) else {}
        if not emotion_dist_raw:
            return {
                "status": "no_face",
                "dominant": "neutral",
                "score": 0.0,
                "scores": {k: 0.0 for k in _EMOTIONS},
                "reason": "empty_emotion",
                "meta": {"latency_ms": int((time.time() - t0) * 1000)},
            }

        current = _normalize_emotion_dist(emotion_dist_raw)

        # EMA smoothing (realtime 표준)
        now = time.time()
        # alpha는 0.45~0.6 사이가 실무에서 많이 씀 (반응+안정 균형)
        ema = _ema_update(session_id=session_id, now=now, current=current, alpha=0.55)

        dominant, dom_score, dom_reason = _dominant_with_fallback(ema)

        return {
            "status": "success",
            "dominant": dominant,
            "score": float(dom_score),
            "scores": {k: float(ema[k]) for k in _EMOTIONS},
            "reason": dom_reason,
            "meta": {
                "quality": q_reason,
                "engine": "deepface",
                "detector": "retinaface",
                "aligned": True,
                "latency_ms": int((time.time() - t0) * 1000),
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "dominant": "neutral",
            "score": 0.0,
            "scores": {k: 0.0 for k in _EMOTIONS},
            "reason": f"exception:{type(e).__name__}",
            "meta": {"detail": str(e)[:200], "latency_ms": int((time.time() - t0) * 1000)},
        }
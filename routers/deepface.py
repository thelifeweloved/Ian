# routers/deepface.py
from __future__ import annotations

import base64
import time
from typing import Dict, Any, Tuple

import cv2
import numpy as np
from deepface import DeepFace

# 세션별 EMA 캐시
_EMA_CACHE: Dict[str, Dict[str, Any]] = {}

# DeepFace 원본 감정 라벨
_EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

# 서비스용 3단계 라벨
_UI_LABELS = ["positive", "neutral", "caution"]


def _b64_to_bgr(image_base64: str) -> np.ndarray:
    if not image_base64:
        raise ValueError("empty image_base64")

    if "," in image_base64 and image_base64.strip().lower().startswith("data:image"):
        image_base64 = image_base64.split(",", 1)[1]

    img_bytes = base64.b64decode(image_base64)
    img_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("cv2.imdecode failed")
    return bgr


def _quality_check(bgr: np.ndarray) -> Tuple[bool, str]:
    h, w = bgr.shape[:2]
    if h < 80 or w < 80:
        return False, "too_small"

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 20:
        return False, "too_blurry"

    return True, "ok"


def _normalize_emotion_dist(dist: Dict[str, float]) -> Dict[str, float]:
    out = {k: float(dist.get(k, 0.0)) for k in _EMOTIONS}
    s = sum(out.values())
    if s <= 0:
        return {k: 0.0 for k in _EMOTIONS}
    return {k: out[k] / s for k in _EMOTIONS}


def _ema_update(session_id: str, now: float, current: Dict[str, float], alpha: float) -> Dict[str, float]:
    prev = _EMA_CACHE.get(session_id, {}).get("ema")
    if not prev:
        ema = dict(current)
    else:
        ema = {
            k: (alpha * current[k] + (1 - alpha) * float(prev.get(k, 0.0)))
            for k in _EMOTIONS
        }

    _EMA_CACHE[session_id] = {"ema": ema, "ts": now}
    return ema


def _to_ui_dist(raw_scores: Dict[str, float]) -> Dict[str, float]:
    positive = float(raw_scores.get("happy", 0.0)) + float(raw_scores.get("surprise", 0.0))
    neutral = float(raw_scores.get("neutral", 0.0))
    caution = (
        float(raw_scores.get("angry", 0.0))
        + float(raw_scores.get("disgust", 0.0))
        + float(raw_scores.get("fear", 0.0))
        + float(raw_scores.get("sad", 0.0))
    )

    dist3 = {
        "positive": positive,
        "neutral": neutral,
        "caution": caution,
    }

    s = sum(dist3.values())
    if s <= 0:
        return {k: 0.0 for k in _UI_LABELS}
    return {k: dist3[k] / s for k in _UI_LABELS}


def _pick_ui_label(dist3: Dict[str, float]) -> Tuple[str, float, str]:
    items = sorted(dist3.items(), key=lambda x: x[1], reverse=True)
    top_label, top_val = items[0]
    _, second_val = items[1]

    min_conf = 0.48
    min_margin = 0.10

    if top_val < min_conf:
        return "neutral", float(dist3.get("neutral", 0.0)), "ui_fallback_low_conf"

    if (top_val - second_val) < min_margin:
        return "neutral", float(dist3.get("neutral", 0.0)), "ui_fallback_small_margin"

    if top_label == "caution" and dist3.get("neutral", 0.0) >= top_val - 0.12:
        return "neutral", float(dist3.get("neutral", 0.0)), "ui_fallback_caution_vs_neutral"

    return top_label, float(top_val), "ok"


def analyze_face_logic(session_id: str, image_base64: str) -> Dict[str, Any]:
    """
    상담사용 보조 표정 반응 분석
    - scores: DeepFace 7감정 EMA 결과
    - dist3: 서비스용 3단계 분포
    - ui: 프론트 표시용 최종 라벨/점수
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
                "dist3": {k: 0.0 for k in _UI_LABELS},
                "ui": {"label": "neutral", "score": 0.0},
                "reason": q_reason,
                "meta": {"quality": q_reason, "latency_ms": int((time.time() - t0) * 1000)},
            }

        h, w = bgr.shape[:2]
        max_side = max(h, w)
        if max_side > 640:
            scale = 640 / max_side
            bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        result = DeepFace.analyze(
            img_path=rgb,
            actions=["emotion"],
            detector_backend="retinaface",
            enforce_detection=False,
            align=True,
            silent=True,
        )

        if isinstance(result, list):
            result = result[0] if result else {}

        emotion_dist_raw = (result.get("emotion") or {}) if isinstance(result, dict) else {}
        if not emotion_dist_raw:
            return {
                "status": "no_face",
                "dominant": "neutral",
                "score": 0.0,
                "scores": {k: 0.0 for k in _EMOTIONS},
                "dist3": {k: 0.0 for k in _UI_LABELS},
                "ui": {"label": "neutral", "score": 0.0},
                "reason": "empty_emotion",
                "meta": {"quality": q_reason, "latency_ms": int((time.time() - t0) * 1000)},
            }

        current = _normalize_emotion_dist(emotion_dist_raw)
        now = time.time()
        ema = _ema_update(session_id=session_id, now=now, current=current, alpha=0.55)

        dist3 = _to_ui_dist(ema)
        ui_label, ui_score, ui_reason = _pick_ui_label(dist3)

        return {
            "status": "success",
            "dominant": ui_label,
            "score": float(ui_score),
            "scores": {k: float(ema[k]) for k in _EMOTIONS},
            "dist3": {k: float(dist3[k]) for k in _UI_LABELS},
            "ui": {
                "label": ui_label,
                "score": float(ui_score),
            },
            "reason": ui_reason,
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
            "dist3": {k: 0.0 for k in _UI_LABELS},
            "ui": {"label": "neutral", "score": 0.0},
            "reason": f"exception:{type(e).__name__}",
            "meta": {
                "detail": str(e)[:200],
                "latency_ms": int((time.time() - t0) * 1000),
            },
        }

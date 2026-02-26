import cv2
import numpy as np
import base64
from deepface import DeepFace

TARGET_EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'fear', 'surprise']
session_states = {}

class EmotionSmoother:
    def __init__(self, alpha=0.4):  # ★ 수정: 0.3 → 0.4 (검증 확정값)
        self.alpha = alpha

    def apply(self, session_id, new_scores):
        if session_id not in session_states:
            session_states[session_id] = {k: 0.0 for k in TARGET_EMOTIONS}
            session_states[session_id]['neutral'] = 1.0

        current_scores = session_states[session_id]
        if new_scores is None:
            return current_scores

        for key in TARGET_EMOTIONS:
            old = float(current_scores[key])
            new = float(new_scores.get(key, 0.0))
            current_scores[key] = float(round(
                (new * self.alpha) + (old * (1 - self.alpha)), 4
            ))

        session_states[session_id] = current_scores
        return current_scores

def apply_bias_correction(scores):
    corrected = scores.copy()
    corrected['neutral']  *= 0.6   # 과검출 억제
    corrected['happy']    *= 0.9   # ★ 수정: 1.2 → 0.9 (검증 확정값)
    corrected['sad']      *= 1.3
    corrected['angry']    *= 1.9   # ★ 수정: 1.3 → 1.9 (검증 확정값)
    corrected['fear']     *= 1.3
    corrected['surprise'] *= 1.2
    total = sum(corrected.values())
    if total == 0:
        return scores
    return {k: round(v / total, 4) for k, v in corrected.items()}

smoother = EmotionSmoother(alpha=0.4)  # ★ 수정: 0.3 → 0.4

def analyze_face_logic(session_id: str, image_base64: str):
    try:
        encoded_data = image_base64.split(',')[1] if ',' in image_base64 else image_base64
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"status": "error", "msg": "Decode failed"}

        result_list = DeepFace.analyze(
            img_path=cv2.resize(img, (320, 240)),
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False,
            align=True,
            silent=True
        )

        raw = result_list[0]['emotion']
        raw_scores = {k: float(raw.get(k, 0.0)) / 100 for k in TARGET_EMOTIONS}
        corrected_scores = apply_bias_correction(raw_scores)
        final_scores = smoother.apply(session_id, corrected_scores)

        return {
            "status": "success",
            "session_id": session_id,
            "dominant": max(final_scores, key=final_scores.get),
            "scores": final_scores
        }
    except Exception as e:
        return {"status": "error", "msg": str(e)}
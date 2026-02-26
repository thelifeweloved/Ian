# services/clova_client.py
# CLOVA X(대화형 LLM) 호출 클라이언트
import requests

class ClovaXClient:
    def __init__(self, api_key: str, endpoint_id: str, app: str = "testapp"):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.app = app
        self.url = f"https://clovastudio.stream.ntruss.com/{app}/v3/chat-completions/{endpoint_id}"

    def chat(self, system_text: str, user_text: str, temperature: float = 0.2, timeout: int = 60) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
            "temperature": temperature,
        }
        resp = requests.post(self.url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

"""Claude API bağlantısı. Tüm ajanlar buradan konuşur, token kullanımı raporlanır."""
import json
import os
import re

from anthropic import Anthropic

# .strip(): kopyalarken gelen gizli boşluk/satır sonlarını temizler
_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip(), max_retries=4)
USAGE = {"input": 0, "output": 0, "calls": 0}


def ask(model: str, system: str, user: str, max_tokens: int = 4000, as_json: bool = False, retries: int = 2):
    last_err = None
    for _ in range(retries + 1):
        msg = _client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        USAGE["input"] += msg.usage.input_tokens
        USAGE["output"] += msg.usage.output_tokens
        USAGE["calls"] += 1
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        if not as_json:
            return text
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            last_err = e
            user += "\n\nIMPORTANT: Your previous answer was not valid JSON. Return ONLY valid JSON."
    raise RuntimeError(f"Ajan geçerli JSON döndüremedi: {last_err}")

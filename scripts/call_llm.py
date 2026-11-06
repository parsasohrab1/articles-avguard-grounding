"""Call a language model on outputs/llm_sample.csv.

If ANTHROPIC_API_KEY is set, that API is used and the key is never written out.
If it is not set, a local model is run instead (AVGUARD_LOCAL_MODEL, default
Qwen/Qwen2.5-0.5B-Instruct). Neither path stores a key.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_FLAX", "0")
os.environ.setdefault("USE_JAX", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from avguard.rebuild import load_sample  # noqa: E402

MODELS = (
    os.environ.get("AVGUARD_LLM_MODEL", "").strip() or "claude-haiku-4-5-20251001",
    "claude-3-5-haiku-latest",
    "claude-3-haiku-20240307",
)
PROMPT = """You are reading one NTSB aviation accident narrative. Use only this narrative.
Reply with one JSON object and no other text, with keys:
summary (string, at most 60 words),
injury (one of NONE, MINR, SERS, FATL, unknown),
weather (one of VMC, IMC, unknown),
light (one of day, night, unknown),
midair (one of yes, no, unknown).

Codes: NONE no injury, MINR minor, SERS serious, FATL fatal.
VMC is visual meteorological conditions. IMC is instrument meteorological conditions.
Use night if the narrative says night or dark. Use day if it says day or daylight.
midair is yes only if two aircraft collided in flight.
If the narrative does not state a field, use unknown. Do not guess.

Narrative:
{narrative}
"""


def _key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def _call(narrative: str, model: str, key: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "max_tokens": 500,
            "temperature": 0,
            "messages": [{"role": "user", "content": PROMPT.format(narrative=narrative)}],
        }
    ).encode()
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = json.loads(response.read().decode())
    return "".join(
        part.get("text", "") for part in body.get("content", []) if part.get("type") == "text"
    )


def complete(narrative: str, key: str) -> tuple[str, str]:
    errors = []
    for model in MODELS:
        if not model:
            continue
        for attempt in range(4):
            try:
                return model, _call(narrative, model, key)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:300]
                errors.append(f"{model} HTTP {exc.code}")
                if exc.code == 404:
                    break
                if exc.code in (429, 500, 529) and attempt < 3:
                    time.sleep(2 + attempt * 3)
                    continue
                if exc.code == 401:
                    raise SystemExit(
                        "The API rejected the key. It was not written to disk."
                    ) from exc
                raise SystemExit(f"Model call failed ({exc.code}). {detail}") from exc
            except urllib.error.URLError:
                errors.append(f"{model} network")
                time.sleep(2 + attempt)
        # try the next model name
    raise SystemExit("No model name succeeded. Last errors: " + "; ".join(errors))


class LocalModel:
    def __init__(self, name: str):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.name = name
        self.tok = AutoTokenizer.from_pretrained(name)
        self.model = AutoModelForCausalLM.from_pretrained(name)
        self.model.eval()

    def complete(self, narrative: str) -> tuple[str, str]:
        import torch

        messages = [{"role": "user", "content": PROMPT.format(narrative=narrative)}]
        text = self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        ids = self.tok(text, return_tensors="pt", truncation=True, max_length=1536)
        with torch.no_grad():
            out = self.model.generate(
                **ids,
                max_new_tokens=180,
                do_sample=False,
                pad_token_id=self.tok.eos_token_id,
            )
        new = out[0, ids["input_ids"].shape[1] :]
        return self.name, self.tok.decode(new, skip_special_tokens=True)


def main():
    sample_path = ROOT / "outputs" / "llm_sample.csv"
    dest = ROOT / "outputs" / "llm_responses.jsonl"
    rows = load_sample(sample_path)
    done = set()
    if dest.exists():
        for line in dest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                done.add(str(json.loads(line)["ev_id"]))
            except json.JSONDecodeError:
                continue
    key = _key()
    local = None
    if not key:
        name = os.environ.get("AVGUARD_LOCAL_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        print("ANTHROPIC_API_KEY is unset. Loading local model", name, flush=True)
        local = LocalModel(name)
    pending = [row for row in rows if row["ev_id"] not in done]
    print("pending", len(pending), "of", len(rows), flush=True)
    with dest.open("a", encoding="utf-8") as handle:
        for n, row in enumerate(pending, start=1):
            try:
                model, raw = (
                    local.complete(row["narrative"]) if local else complete(row["narrative"], key)
                )
            except Exception as exc:
                model = local.name if local else "api"
                raw = ""
                print("fail", row["ev_id"], type(exc).__name__, flush=True)
            handle.write(
                json.dumps({"ev_id": row["ev_id"], "model": model, "raw": raw}, ensure_ascii=False)
                + "\n"
            )
            handle.flush()
            print(n, row["ev_id"], model, flush=True)
    print("replies", dest)


if __name__ == "__main__":
    main()

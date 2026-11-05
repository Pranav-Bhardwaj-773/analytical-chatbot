"""One-off Gemini connectivity check (does not print API key)."""

import httpx

from app.config import settings


def main() -> None:
    key = settings.gemini_api_key
    print("model_from_settings:", settings.gemini_model)
    print("key_present:", bool(key), "key_len:", len(key))

    r = httpx.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": key},
        params={"pageSize": 100},
        timeout=30,
    )
    print("list_models status:", r.status_code)
    if r.status_code != 200:
        print("list error:", r.text[:800])
        return

    models = r.json().get("models", [])
    gen = [
        m["name"].replace("models/", "")
        for m in models
        if "generateContent" in (m.get("supportedGenerationMethods") or [])
    ]
    print("generateContent count:", len(gen))
    for name in gen[:20]:
        print(" -", name)

    candidates = [
        settings.gemini_model,
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]
    for model in candidates:
        if not model:
            continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        r2 = httpx.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": 'Return JSON: {"ok": true}'}]}],
                "generationConfig": {"temperature": 0.1},
            },
            timeout=30,
        )
        print(f"POST {model}: {r2.status_code} {r2.text[:200]}")


if __name__ == "__main__":
    main()

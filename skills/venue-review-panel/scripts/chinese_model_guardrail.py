#!/usr/bin/env python3
"""Chinese-model guardrail for venue-review-panel.

Sends a casual Chinese review prompt and the manuscript text to several
Chinese model families on Amazon Bedrock. It imitates a reviewer who pastes
a submission into a chat app. The coordinator reads the outputs after the
panel is calibrated and reports only red flags; see
references/chinese-model-guardrail.md.

Credentials, first hit wins:
  1. AWS_BEARER_TOKEN_BEDROCK, a Bedrock API key;
  2. the first Bedrock API key (ABSK...) in the file named by --key-file or
     VENUE_PANEL_BEDROCK_KEY_FILE;
  3. the default AWS credential chain (AWS_PROFILE, AWS_ACCESS_KEY_ID,
     ~/.aws/credentials, SSO).
The whole stage is skipped when it is disabled, boto3 is missing, the
manuscript cannot be read, no credential is found, or no model passes a
16-token preflight call. A model that fails preflight is skipped on its own.
Apart from usage errors, every outcome exits 0 and prints one summary line on
stdout; per-model lines go to stderr and guardrail-status.json. Key values are never printed.

The Converse API on bedrock-runtime is used throughout, so usage is billed
on the same path as other Bedrock runtime calls.

Usage:
  python chinese_model_guardrail.py --check
  python chinese_model_guardrail.py --prompt prompt.md --manuscript paper.txt --out-dir guardrail
  python chinese_model_guardrail.py ... --models deepseek,qwen,glm,kimi
  python chinese_model_guardrail.py ... --models "Qwen=qwen.qwen3-235b-a22b-2507-v1:0@us-west-2"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Tuple

Model = Tuple[str, str, str, int]  # (label, model id, region, max output tokens)

DEFAULT_REGION = "us-east-1"
DEFAULT_MAX_TOKENS = 8192
# Output caps follow the Bedrock model cards (8K for DeepSeek V3.2 and Qwen3).
# Kimi K3 needs 32000: its reviews ran 11k to 18k tokens and truncated at 16000.
KNOWN_MODELS = {
    "deepseek": ("DeepSeek", "deepseek.v3.2", "us-east-1", 8192),
    "qwen": ("Qwen", "qwen.qwen3-235b-a22b-2507-v1:0", "us-west-2", 8192),
    "glm": ("GLM", "zai.glm-5", "us-east-1", 8192),
    "kimi": ("Kimi", "us.moonshotai.kimi-k3", "us-east-1", 32000),
}
DEFAULT_MODELS = "deepseek,qwen,glm,kimi"
PREFLIGHT_TOKENS = 16  # Kimi K3 rejects a smaller maxTokens
KEY_RE = re.compile(r"ABSK[A-Za-z0-9+/=]{20,}")
OFF_VALUES = {"off", "0", "disabled", "false", "no"}
STAGE = "Chinese-model guardrail"


def parse_models(spec: str, max_tokens: Optional[int]) -> List[Model]:
    models: List[Model] = []
    for item in (part.strip() for part in spec.split(",")):
        if not item:
            continue
        if item.lower() in KNOWN_MODELS:
            label, model_id, region, cap = KNOWN_MODELS[item.lower()]
            models.append((label, model_id, region, max_tokens or cap))
            continue
        label, sep, rest = item.partition("=")
        model_id, _, region = rest.partition("@")
        if not sep or not label.strip() or not model_id.strip():
            raise SystemExit(
                f"bad model entry {item!r}: use a known name ({', '.join(KNOWN_MODELS)}) "
                "or Label=model_id@region"
            )
        models.append((label.strip(), model_id.strip(), region.strip() or DEFAULT_REGION,
                       max_tokens or DEFAULT_MAX_TOKENS))
    if not models:
        raise SystemExit("no models selected")
    return models


def redact(text: str) -> str:
    """Remove Bedrock API key values from text that may be printed or saved."""
    token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    if token:
        text = text.replace(token, "<redacted>")
    return KEY_RE.sub("<redacted>", text)


def find_credentials(key_file: Optional[str], notes: List[str]) -> Optional[str]:
    """Return a description of the credential source, or None when nothing is found."""
    if os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip():
        return "Bedrock API key from AWS_BEARER_TOKEN_BEDROCK"
    notes.append("AWS_BEARER_TOKEN_BEDROCK unset")

    if key_file:
        path = Path(key_file).expanduser()
        try:
            contents = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            notes.append(f"key file {path} unreadable ({type(exc).__name__})")
        else:
            match = KEY_RE.search(contents)
            if match:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = match.group(0)
                return f"Bedrock API key from key file {path}"
            notes.append(f"no Bedrock API key in {path}")
    else:
        notes.append("no key file configured")

    import boto3
    from botocore.exceptions import BotoCoreError

    try:
        creds = boto3.Session().get_credentials()
    except BotoCoreError as exc:
        notes.append(f"default AWS chain error: {redact(str(exc))}")
        return None
    if creds is None:
        notes.append("default AWS credential chain empty")
        return None
    profile = os.environ.get("AWS_PROFILE")
    return f"AWS credentials ({creds.method}" + (f", profile {profile}" if profile else "") + ")"


def short_error(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if isinstance(response, dict) and "Error" in response:
        err = response["Error"]
        text = f"{err.get('Code', type(exc).__name__)}: {err.get('Message', '')}"
    else:
        text = f"{type(exc).__name__}: {exc}"
    return redact(" ".join(text.split()))[:300]


def converse(model: Model, text: str, max_tokens: int, read_timeout: int) -> dict:
    import boto3
    from botocore.config import Config

    _, model_id, region, _ = model
    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(read_timeout=read_timeout, connect_timeout=30,
                      retries={"max_attempts": 3, "mode": "adaptive"}),
    )
    return client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )


def preflight(model: Model) -> Optional[str]:
    """Return None when the model answers a short call, else the error."""
    try:
        converse(model, "Reply with one word: ok", max_tokens=PREFLIGHT_TOKENS, read_timeout=120)
        return None
    except Exception as exc:  # any failure means skip this model
        return short_error(exc)


def load_manuscript(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8", errors="replace")
    import pypdf  # ImportError is turned into a skip by the caller

    reader = pypdf.PdfReader(str(path))
    pages = [f"=== Page {i} ===\n{(page.extract_text() or '').strip()}"
             for i, page in enumerate(reader.pages, 1)]
    return "\n\n".join(pages)


def safe_name(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", label).strip("-") or "model"


def record(model: Model, status: str, **fields) -> dict:
    label, model_id, region, _ = model
    return {"label": label, "model": model_id, "region": region, "status": status, **fields}


def review(model: Model, prompt: str, out_dir: Path) -> dict:
    start = time.time()
    try:
        resp = converse(model, prompt, max_tokens=model[3], read_timeout=1800)
    except Exception as exc:
        return record(model, "failed", reason=short_error(exc))
    seconds = round(time.time() - start)
    stop = resp.get("stopReason")
    blocks = resp.get("output", {}).get("message", {}).get("content", [])
    text = "\n".join(b["text"] for b in blocks if "text" in b).strip()
    if not text:
        return record(model, "failed", reason=f"no text in response (stopReason {stop})")

    usage = resp.get("usage", {})
    out = out_dir / f"Guardrail-{safe_name(model[0])}.md"
    header = (f"<!-- model: {model[1]}; region: {model[2]}; stopReason: {stop}; "
              f"seconds: {seconds}; outputTokens: {usage.get('outputTokens')} -->\n\n")
    tmp = out.with_name(f".{out.name}.tmp")
    tmp.write_text(header + text + "\n", encoding="utf-8")
    os.replace(tmp, out)
    return record(model, "ok", file=out.name, seconds=seconds, stop_reason=stop,
                  truncated=stop == "max_tokens", input_tokens=usage.get("inputTokens"),
                  output_tokens=usage.get("outputTokens"))


def finish(status: dict, out_dir: Optional[Path], summary: str) -> int:
    status["summary"] = summary
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "guardrail-status.json"
        tmp = target.with_name(f".{target.name}.tmp")
        tmp.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, target)
    for entry in status["models"]:
        detail = entry.get("reason") or f"{entry.get('seconds')}s, stopReason {entry.get('stop_reason')}"
        if entry.get("truncated"):
            detail += ", output truncated at the max-tokens cap"
        print(f"  {entry['label']} ({entry['model']} @ {entry['region']}): {entry['status']}, {detail}",
              file=sys.stderr)
    print(summary)
    return 0


def run(args: argparse.Namespace) -> int:
    models = parse_models(args.models, args.max_tokens)
    out_dir = None if args.check else args.out_dir
    status = {"stage": STAGE, "credentials": None, "models": []}

    def skip(reason: str) -> int:
        return finish(status, out_dir, f"{STAGE}: skipped, {reason}.")

    if os.environ.get("VENUE_PANEL_ZH_GUARDRAIL", "").strip().lower() in OFF_VALUES:
        return skip("disabled by VENUE_PANEL_ZH_GUARDRAIL")
    try:
        import boto3  # noqa: F401
    except ImportError:
        return skip("boto3 is not installed")

    prompt = ""
    if not args.check:
        try:
            manuscript = load_manuscript(args.manuscript)
        except ImportError:
            return skip("pypdf is not installed; pass extracted text instead of the PDF")
        except Exception as exc:
            return skip(f"could not read {args.manuscript.name} ({type(exc).__name__}); "
                        "pass extracted text instead")
        prompt = (args.prompt.read_text(encoding="utf-8").strip()
                  + "\n\n--- MANUSCRIPT BEGIN ---\n" + manuscript + "\n--- MANUSCRIPT END ---")

    notes: List[str] = []
    source = find_credentials(args.key_file, notes)
    if source is None:
        return skip(f"no Bedrock credentials found ({'; '.join(notes)})")
    status["credentials"] = source

    with ThreadPoolExecutor(max_workers=len(models)) as pool:
        errors = list(pool.map(preflight, models))
    ready = [m for m, err in zip(models, errors) if err is None]
    skipped = [record(m, "skipped", reason=f"preflight failed: {err}")
               for m, err in zip(models, errors) if err is not None]
    if not ready:
        status["models"] = skipped
        return skip(f"no model passed preflight with {source}; see the per-model reasons")

    if args.check:
        status["models"] = [record(m, "ready", reason="preflight passed") for m in ready] + skipped
        return finish(status, None, f"{STAGE}: {len(ready)} of {len(models)} models ready with {source}.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=len(ready)) as pool:
        results = list(pool.map(lambda m: review(m, prompt, args.out_dir), ready))
    status["models"] = results + skipped

    ran = [r["label"] for r in results if r["status"] == "ok"]
    not_ran = [e["label"] for e in status["models"] if e["status"] != "ok"]
    summary = f"{STAGE}: ran {len(ran)} of {len(models)} models ({', '.join(ran) or 'none'}) with {source}."
    if not_ran:
        summary += f" Not run: {', '.join(not_ran)}; see guardrail-status.json."
    return finish(status, args.out_dir, summary)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="find credentials and preflight each model; send no manuscript")
    ap.add_argument("--prompt", type=Path, help="the filled casual Chinese prompt")
    ap.add_argument("--manuscript", type=Path, help="manuscript text (.txt, .md, .tex) or .pdf")
    ap.add_argument("--out-dir", type=Path, help="where Guardrail-<Model>.md and guardrail-status.json go")
    ap.add_argument("--models", default=os.environ.get("VENUE_PANEL_ZH_MODELS", DEFAULT_MODELS),
                    help=f"comma list of {', '.join(KNOWN_MODELS)} or Label=model_id@region "
                         f"(default: VENUE_PANEL_ZH_MODELS or {DEFAULT_MODELS})")
    ap.add_argument("--key-file", default=os.environ.get("VENUE_PANEL_BEDROCK_KEY_FILE"),
                    help="file holding a Bedrock API key (default: VENUE_PANEL_BEDROCK_KEY_FILE)")
    ap.add_argument("--max-tokens", type=int,
                    help=f"output cap for every model (default: per model, {DEFAULT_MAX_TOKENS} "
                         "for custom entries)")
    args = ap.parse_args()

    if not args.check:
        missing = [flag for flag, value in (("--prompt", args.prompt), ("--manuscript", args.manuscript),
                                            ("--out-dir", args.out_dir)) if value is None]
        if missing:
            ap.error(f"{', '.join(missing)} required unless --check")
        for path in (args.prompt, args.manuscript):
            if not path.is_file():
                ap.error(f"{path} not found")

    try:
        return run(args)
    except Exception as exc:  # the guardrail must never block the panel
        print(f"{STAGE}: skipped, unexpected {type(exc).__name__}: {redact(str(exc))[:200]}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

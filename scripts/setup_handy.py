#!/usr/bin/env python3
"""Point Handy's post-processing at an OpenAI-compatible endpoint and install
the Chinese oral-to-written prompt.

    python3 setup_handy.py --base-url http://127.0.0.1:8080/v1 \
                           --model gpt-4o-mini \
                           --api-key sk-xxx

Runs on the Mac where Handy lives. Quit Handy first -- a running instance holds
settings in memory and writes them back on exit.
"""
import argparse
import json
import pathlib
import shutil
import sys

STORE = pathlib.Path.home() / "Library/Application Support/com.pais.handy/settings_store.json"
PROMPT_ID = "zh_oral_to_written"
PROMPT_FILE = pathlib.Path(__file__).resolve().parent.parent / "prompt/zh_oral_to_written.txt"

CUSTOM_WORDS = [
    "SBCTNet", "mAP", "LaTeX", "DOI", "Overleaf", "Zenodo",
    "时频重构", "齿轮箱", "故障诊断",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="e.g. http://127.0.0.1:8080/v1")
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="local", help="any non-empty string for a local gateway")
    ap.add_argument("--store", default=str(STORE))
    ap.add_argument("--prompt-file", default=str(PROMPT_FILE))
    ap.add_argument("--raw-hotkey", default="option+shift+space",
                    help="binding for transcribe-without-cleanup")
    ap.add_argument("--clean-hotkey", default="option+space",
                    help="binding for transcribe-and-clean")
    ap.add_argument("--no-autostart", action="store_true")
    args = ap.parse_args()

    store = pathlib.Path(args.store)
    if not store.exists():
        sys.exit(f"settings store not found: {store}\nLaunch Handy once, quit it, then rerun.")

    shutil.copy2(store, store.with_suffix(".json.bak"))
    data = json.loads(store.read_text())
    s = data["settings"]

    # --- recognition -------------------------------------------------------
    s["selected_model"] = "turbo"
    s["selected_language"] = "zh"          # not "auto": short Chinese clips drift
    s["spoken_languages"] = ["zh", "en"]
    s["chinese_script"] = "simplified"
    s["translate_to_english"] = False
    s["onboarding_completed"] = True
    s["vad_enabled"] = True
    s["long_form_chunking"] = True
    s["append_trailing_space"] = True
    s["custom_words"] = CUSTOM_WORDS
    s["autostart_enabled"] = not args.no_autostart
    s["start_hidden"] = True

    # --- post-processing ---------------------------------------------------
    s["post_process_enabled"] = True
    s["post_process_provider_id"] = "custom"

    providers = s.get("post_process_providers") or []
    custom = next((p for p in providers if p.get("id") == "custom"), None)
    if custom is None:
        custom = {"id": "custom", "label": "Custom", "allow_base_url_edit": True,
                  "models_endpoint": None, "supports_structured_output": False,
                  "api_format": "openai"}
        providers.append(custom)
    custom["base_url"] = args.base_url
    custom["api_format"] = "openai"
    custom["models_endpoint"] = None
    # Leaving structured output off keeps Handy on the single-message path, which
    # is what the prompt below is written for. See docs/prompt-design.md.
    custom["supports_structured_output"] = False
    s["post_process_providers"] = providers

    s["post_process_api_keys"] = {"custom": args.api_key}
    s["post_process_models"] = {"custom": args.model}

    prompt = pathlib.Path(args.prompt_file).read_text().strip()
    s["post_process_prompts"] = [{"id": PROMPT_ID, "name": "中文口语转书面", "prompt": prompt}]
    s["post_process_selected_prompt_id"] = PROMPT_ID

    # --- hotkeys -----------------------------------------------------------
    b = s.setdefault("bindings", {})
    b.setdefault("transcribe", {"id": "transcribe", "name": "Transcribe",
                                "description": "Converts your speech into text.",
                                "default_binding": "option+space"})
    b["transcribe"]["current_binding"] = args.raw_hotkey
    b.setdefault("transcribe_with_post_process",
                 {"id": "transcribe_with_post_process",
                  "name": "Transcribe with Post-Processing",
                  "description": "Converts your speech into text and applies AI post-processing.",
                  "default_binding": "option+shift+space"})
    b["transcribe_with_post_process"]["current_binding"] = args.clean_hotkey
    b.setdefault("cancel", {"id": "cancel", "name": "Cancel",
                            "description": "Cancels the current recording.",
                            "default_binding": "escape"})
    b["cancel"]["current_binding"] = "escape"

    data["settings"] = s
    store.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    print(f"base_url : {args.base_url}")
    print(f"model    : {args.model}")
    print(f"hotkeys  : {args.clean_hotkey} (clean) / {args.raw_hotkey} (raw) / escape (cancel)")
    print(f"backup   : {store}.bak")
    print("Now start Handy.")


if __name__ == "__main__":
    main()

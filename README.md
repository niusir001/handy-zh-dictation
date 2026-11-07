# handy-zh-dictation

A dictation setup for Mandarin: **recognition stays on your machine, cleanup runs on your own model endpoint.** Speak with a hotkey, get clean written Chinese pasted at your cursor — as a paragraph when you're telling a story, as a numbered list when you're listing things.

No subscription, no word quota, no audio leaving the device.

```
mic ──▶ whisper.cpp on Metal/CPU (local) ──▶ raw transcript
                                                   │
                                                   ▼
                                     LLM cleanup at your endpoint
                                     (paragraph / list / single line)
                                                   │
                                                   ▼
                                          paste at cursor
```

Typeless and similar apps put both halves in the cloud and meter the free tier by words per week. This one keeps the expensive, latency-critical half local and the language half on hardware you already pay for.

## What's in here

| Path | |
|---|---|
| `scripts/setup_handy.py` | Writes the whole config into Handy's settings store |
| `scripts/test_prompt.py` | Replays the prompt over 8 spoken-style cases, asserts output shape |
| `prompt/zh_oral_to_written.txt` | The cleanup prompt, with the reasoning behind each rule |
| `docs/case-study.md` | The build log: what broke, why, what fixed it |
| `docs/prompt-design.md` | Why the prompt is shaped the way it is |

## Requirements

- macOS 12+ (Apple Silicon recommended; a 1.5 GB model runs ~8x real-time on an M-series GPU)
- [Handy](https://github.com/cjpais/Handy) — MIT, offline dictation
- Any OpenAI-compatible chat endpoint. A local llama.cpp / Ollama server, or a gateway of your own.

Windows and Linux work with Handy too, but the settings paths in the scripts are macOS-specific.

## Setup

**1. Install Handy** and launch it once, then quit it. It has to write a default settings store before we can edit it.

```
# prebuilt, notarized
open https://github.com/cjpais/Handy/releases
cp -R Handy.app /Applications/
```

**2. Download a recognition model.** In Handy: Settings → Models → **Whisper Turbo**. Or drop any ggml model into `~/Library/Application Support/com.pais.handy/models/`.

Turbo is the right trade for Mandarin: 1.5 GB, ~8x real-time on M-series, and noticeably better on Chinese than `small` or `medium`. `large-v3` is more accurate still and about 2x slower — worth it only if your machine idles anyway.

**3. Point the cleanup at your endpoint.**

```
python3 scripts/setup_handy.py \
  --base-url http://127.0.0.1:8080/v1 \
  --model your-model-name
```

Use `--api-key` if your endpoint wants one. The script backs up the existing store to `settings_store.json.bak` first.

**4. Restart Handy.** Then hold the hotkey and talk.

**5. Check it.** Every prompt edit should be followed by:

```
python3 scripts/test_prompt.py \
  --base-url http://127.0.0.1:8080/v1 --model your-model-name
```

## Usage

| Hotkey | |
|---|---|
| `Option+Space` | hold to talk → cleaned text pasted |
| `Option+Shift+Space` | hold to talk → raw transcript, no cleanup |
| `Esc` | cancel the current recording |

A tap under 300 ms locks recording on until the next press, so you don't have to hold for long passages.

**What comes out depends on what you say:**

| You say | You get |
|---|---|
| A story, one train of thought | One paragraph |
| "第一… 第二… 第三…" / "首先… 然后… 最后…" / "要做几件事" | A numbered list, one item per line |
| One sentence | One sentence |
| Exactly two items | One paragraph — two items isn't a list |

The list/paragraph decision is made by the prompt, not by the app. It looks for three or more parallel items carrying ordinal, sequential, or enumeration markers.

## When the endpoint is down

Handy falls back to pasting the **raw transcript** and shows a small notice. You lose the cleanup, not the dictation. This is deliberate — a dictation tool that silently drops your words when a server hiccups is worse than one that gives you a rough draft.

## Design notes

**Recognition is pinned to `zh`, not `auto`.** Whisper's language detector needs a few seconds of speech to settle; on short Chinese utterances it drifts to Japanese or English and then transliterates. Pinning costs you nothing if you only dictate Chinese and everything if you don't.

**Structured output is deliberately off.** Handy's custom provider can speak either Chat Completions or Anthropic Messages. With structured output enabled it wraps your transcript in a JSON schema request; the prompt here is written for the plain single-message path, where the transcript and the instructions sit in one message and need `<transcript>` tags to stay separate. See `docs/prompt-design.md` for the failure this prevents.

**The prompt has three parts,** in order: decide the output shape, clean the text, refuse to editorialize. The third exists because of a specific failure — when speech recognition returns garbage, a model asked only to "clean this up" will answer *"this transcript can't be reliably cleaned"* and that sentence becomes what gets pasted into your document. See `docs/case-study.md`.

## If you'd rather not use Handy

Any offline dictation app that supports a custom OpenAI-compatible endpoint will work. `tover0314-w/opentypeless` is the closest alternative. Handy is the better base here for its Voice Activity Detection, Metal acceleration, and the fallback-to-raw behavior above.

## License

MIT.

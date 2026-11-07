#!/usr/bin/env python3
"""Show what the cleanup step buys you, side by side, on one utterance.

    python3 compare_raw_vs_clean.py --base-url http://127.0.0.1:8080/v1 --model m
    python3 compare_raw_vs_clean.py --spoken "这周要干几件事 第一..." --only list
"""
import argparse
import json
import pathlib
import sys
import urllib.request

SAMPLES = {
    "sentence": "嗯 那个 明天 上午 十点 开会 啊",
    "narrative": ("我 昨天 去 了 那个 车间 看 了 一下 设备 整体 状况 还 可以 "
                  "但是 三号 机 的 轴承 有点 异响 我 觉得 应该 安排 一次 检修"),
    "list": ("这周要干几件事 第一把 A0153 的稿子改完 第二周二之前给编辑回信 "
             "第三把 Figure 1 的架构图调一下 第四 Zenodo 的 DOI 挂上"),
}


def clean(base_url, model, api_key, prompt, spoken):
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt.replace("${output}", spoken)}],
        "stream": False,
        "reasoning_effort": "none",
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "content-type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    resp = json.load(urllib.request.urlopen(req, timeout=90))
    return (resp["choices"][0]["message"]["content"] or "").strip()


def wrap(text, width=72):
    out, line = [], ""
    for ch in text:
        line += ch
        if len(line) >= width and ch in "，。！？；、":
            out.append(line)
            line = ""
    if line:
        out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url")
    ap.add_argument("--model")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--spoken", help="dictate your own line instead of the built-in samples")
    ap.add_argument("--only", choices=sorted(SAMPLES), help="run a single built-in sample")
    ap.add_argument("--prompt-file",
                    default=str(pathlib.Path(__file__).resolve().parent.parent
                                / "prompt/zh_oral_to_written.txt"))
    args = ap.parse_args()

    if args.spoken:
        samples = {"yours": args.spoken}
    elif args.only:
        samples = {args.only: SAMPLES[args.only]}
    else:
        samples = SAMPLES

    prompt = pathlib.Path(args.prompt_file).read_text().strip()

    for key, spoken in samples.items():
        raw = wrap(spoken.replace("  ", ""))
        print("─" * 74)
        print(f"[{key}] RAW — what the recognizer heard")
        for ln in raw:
            print(f"  {ln}")

        print(f"[{key}] CLEANED — what lands at your cursor")
        if args.base_url and args.model:
            try:
                result = clean(args.base_url, args.model, args.api_key, prompt, spoken)
                for ln in result.splitlines():
                    print(f"  {ln}")
            except Exception as exc:                      # noqa: BLE001
                print(f"  !! cleanup failed: {exc}")
                print("  (this is where Handy pastes the raw text instead)")
        else:
            print("  (pass --base-url and --model to see this half)")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

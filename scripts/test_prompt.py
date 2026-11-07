#!/usr/bin/env python3
"""Replay the prompt against a batch of spoken-style inputs and report, per case,
whether the output shape matched what we expect (paragraph / list / single line).

Run this after any prompt edit -- a change that fixes one case routinely breaks
another, and the breakage is silent.

    python3 test_prompt.py --base-url http://127.0.0.1:8080/v1 --model gpt-4o-mini
"""
import argparse
import json
import pathlib
import sys
import time
import urllib.request

CASES = [
    ("single",   "单句",   "嗯 那个 明天 上午 十点 开会", "para",
     "One sentence, no numbering."),
    ("narrative", "叙述",
     "我 昨天 去 了 那个 车间 看 了 一下 设备 整体 状况 还 可以 但是 三号 机 的 轴承 有点 异响 我 觉得 应该 安排 一次 检修",
     "para", "Continuous story stays one paragraph."),
    ("narrative-long", "长叙述",
     "我 今天 上午 跟 编辑 通 了 个 电话 他 说 我们 那篇 稿子 的 审稿 意见 下周 会 下来 大概 有 三到四个 月 的 修改 时间 我 觉得 节奏 上 还 可以 但是 得 提前 把 补充 实验 规划 好 免得到时候 来不及",
     "para", "Longer narrative still one paragraph."),
    ("list-explicit", "清单",
     "这周要干几件事 第一把 A0153 的稿子改完 第二周二之前给编辑回信 第三把 Figure 1 的架构图调一下 第四 Zenodo 的 DOI 挂上",
     "list", "Explicit ordinals -> numbered lines."),
    ("list-steps", "步骤",
     "操作步骤是这样 先打开 那个 工单 页面 然后 点 新建 填 工单号 再 上传 附件 最后 提交",
     "list", "Sequential markers -> numbered lines."),
    ("list-points", "要点",
     "这个方案 我 觉得 有 三个 问题 一是 样本 太 少 二是 标签 不 干净 三是 没有 做 跨设备 验证",
     "list", "This was the hardest case: it collapsed to one line."),
    ("two-items", "两项不算",
     "我 觉得 主要 就是 两个 问题 一个 是 样本 另一个 是 标签",
     "para", "Only two items -> do NOT split."),
    ("garbage", "乱码兜底",
     "水扇计刑 ンデ sticks, 丹ritis, NATO, 臭, 手臭的一下 Had Well, kırk Deanessar, you didn't speak for?是, 过来说, 过来ホスト치 clASA",
     "any", "Must echo something, never an apology about quality."),
]

BANNED = ["无法辨认", "无法可靠整理", "内容混杂", "请提供文本", "需要更多信息",
          "无法识别", "不能整理"]


def shape(text):
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if any(ln.lstrip().startswith(("1.", "1、", "1）")) for ln in lines):
        return "list"
    return "para"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--prompt-file",
                    default=str(pathlib.Path(__file__).resolve().parent.parent
                                / "prompt/zh_oral_to_written.txt"))
    args = ap.parse_args()

    tpl = pathlib.Path(args.prompt_file).read_text().strip()
    url = args.base_url.rstrip("/") + "/chat/completions"
    fails = 0

    for _key, tag, spoken, want, why in CASES:
        user = tpl.replace("${output}", spoken)
        body = json.dumps({
            "model": args.model,
            "messages": [{"role": "user", "content": user}],
            "stream": False,
            "reasoning_effort": "none",
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "content-type": "application/json",
            "Authorization": f"Bearer {args.api_key}",
        })
        t0 = time.time()
        try:
            resp = json.load(urllib.request.urlopen(req, timeout=90))
            out = resp["choices"][0]["message"]["content"] or ""
        except Exception as exc:                      # noqa: BLE001
            print(f"[ERR ] {tag:8s} {exc}")
            fails += 1
            continue
        dt = time.time() - t0

        got = shape(out)
        ok_shape = want == "any" or got == want
        ok_banned = want != "any" or not any(w in out for w in BANNED)
        ok = ok_shape and ok_banned
        fails += 0 if ok else 1

        print(f"[{'PASS' if ok else 'FAIL'}] {tag:8s} want={want:4s} got={got:4s} "
              f"{dt * 1000:4.0f}ms  {why}")
        for ln in out.strip().splitlines():
            print(f"        {ln}")
        print()

    print(f"{len(CASES) - fails}/{len(CASES)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

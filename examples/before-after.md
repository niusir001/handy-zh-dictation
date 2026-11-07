# Before / after

Real output from the pipeline, captured with `scripts/compare_raw_vs_clean.py`.
`RAW` is what whisper.cpp produced; `CLEANED` is what reached the cursor.

## sentence

```
[sentence] RAW — what the recognizer heard
  嗯 那个 明天 上午 十点 开会 啊
[sentence] CLEANED — what lands at your cursor
  明天上午10点开会。
```

## narrative

```
[narrative] RAW — what the recognizer heard
  我 昨天 去 了 那个 车间 看 了 一下 设备 整体 状况 还 可以 但是 三号 机 的 轴承 有点 异响 我 觉得 应该 安排 一次 检修
[narrative] CLEANED — what lands at your cursor
  我昨天去了车间看了一下，设备整体状况还可以，但是3号机的轴承有点异响，我觉得应该安排一次检修。
```

## list

```
[list] RAW — what the recognizer heard
  这周要干几件事 第一把 A0153 的稿子改完 第二周二之前给编辑回信 第三把 Figure 1 的架构图调一下 第四 Zenodo 的 DOI 挂上
[list] CLEANED — what lands at your cursor
  这周要干几件事：
  1. 把 A0153 的稿子改完。
  2. 周二之前给编辑回信。
  3. 把 Figure 1 的架构图调一下。
  4. 把 Zenodo 的 DOI 挂上。
```


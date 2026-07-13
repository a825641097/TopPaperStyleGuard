# TopPaperStyleGuard

**学习顶刊写法结构，但不复制顶刊文本。**

[English](README.md) | [方法说明](docs/method.md) | [Agent Skill](docs/agent-skill.md) | [伦理边界](docs/ethics.md)

TopPaperStyleGuard 会把你本地投喂的顶级期刊论文语料，转成几类本地文件：

- **style profile**：抽象的写作结构画像，例如段落功能、论证推进、句长节奏、语气克制程度；
- **guardpack**：哈希化的 n-gram 指纹，用来检查后续草稿是否过度贴近原始论文表达。
- **skill reference**：给 Agent 读取的可读风格摘要，不包含原始论文句子。

核心原则：

> 学习 rhetorical moves，不学习句子。

也就是说，它帮助 AI 学会顶刊论文如何提出问题、制造 gap、描述识别策略、控制贡献表述和限制性语气，但不会把原文句子塞进 Skill 里让模型照着改。

## 快速开始

在项目目录安装：

```console
python -m pip install .
```

如果只是临时在源码目录试用，也可以不安装：

```console
PYTHONPATH=src python -m toppaperstyleguard --help
```

### 先跑内置示例

如果你还没有自己的顶刊语料，可以先跑仓库内的离线示例：

```console
python -m toppaperstyleguard build examples/corpus \
  --field economics \
  --profile-out /tmp/tpsg.profile.json \
  --guard-out /tmp/tpsg.guard.json \
  --skill-reference /tmp/tpsg-profile.md \
  --common-doc-threshold 2

python -m toppaperstyleguard audit examples/drafts/introduction.md \
  --profile /tmp/tpsg.profile.json \
  --guard /tmp/tpsg.guard.json \
  --ignore-common-ngrams \
  --fail-on none
```

从本地顶刊语料生成 profile 和 guardpack：

```console
tpsg build papers/top-journal-corpus \
  --field economics \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md \
  --common-doc-threshold 5
```

语料准备建议：先用同一领域、同一文体的 10-30 篇论文或章节。尽量使用干净的 UTF-8 文本，并在可能时删除参考文献、附录、表格和 OCR 噪声。只用 introduction 等分章节语料，往往比混合整篇论文更容易解释。

### 真实 Introduction 工作流

如果你只想学习顶刊 introduction 写法，建议一篇 introduction 一个文件：

```text
data/top-intros/paper-01.txt
data/top-intros/paper-02.txt
drafts/my-introduction.md
```

如果语料文件本身已经只有 introduction，不要加 `--sections`：

```console
tpsg build data/top-intros \
  --field economics \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md

tpsg audit drafts/my-introduction.md \
  --profile topstyle.profile.json \
  --guard topstyle.guard.json \
  --ignore-common-ngrams \
  --fail-on medium
```

如果语料文件是整篇论文，并且标题能被识别为 `Introduction` 或 `\section{Introduction}`，再使用：

```console
tpsg build data/top-papers \
  --field economics \
  --sections introduction \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md
```

检查清单：UTF-8 文本、一篇论文或一个章节一个文件、清理明显 OCR 噪声、尽量去掉表格和参考文献。如果标题不规则或缺失，把目标章节单独保存成文件，并省略 `--sections`。

审计自己的草稿：

```console
tpsg audit drafts/introduction.md \
  --profile topstyle.profile.json \
  --guard topstyle.guard.json \
  --ignore-common-ngrams \
  --fail-on none
```

## 它解决什么问题

- 让 AI 学习顶刊写法的抽象结构，而不是背原句。
- 改写 abstract、introduction、contribution、discussion 时保持学术表达的克制和层次。
- 在 agent 帮你润色后，检查是否与投喂语料过度接近。
- 生成可挂载到 Codex、Claude Code、Cursor 等工具里的 Skill。

## 它不会做什么

- 不保证 0 重复率。
- 不帮助绕过查重。
- 不把别人的句子改几个词后当成原创。
- 不替代真实学术贡献、识别策略或文献贡献。

它的正确用途是：**用顶刊语料学习写作策略，再用守门器把文本推离原始表达。**

注意：guardpack 不包含原文句子，但包含 salted hash 指纹，仍应保存在本地或私有仓库，不建议公开发布。

## Agent Skill

仓库内置 Skill：[`skills/toppaperstyleguard`](skills/toppaperstyleguard)。

可以这样要求 agent：

```text
Use $toppaperstyleguard to revise my introduction toward top-journal structure.
Preserve my claims, avoid source-like wording, and run tpsg audit before finalizing.
```

安装与适配方式见 [Agent Skill 文档](docs/agent-skill.md)。

## 当前支持

Alpha 版本支持 `.txt`、`.md`、`.markdown` 和 `.tex`。PDF 建议先用本地工具提取文本，再交给 `tpsg build`。

如果语料库较大，可以在构建时使用 `--common-doc-threshold` 标记多篇论文都出现的通用表达，并在审计时使用 `--ignore-common-ngrams` 降低常见学术套语带来的误报。
这个阈值不能大于语料文档数量；小示例可以用 `2`，较大语料再考虑 `5` 或 `10`。

用 `tpsg inspect topstyle.profile.json --guard topstyle.guard.json` 可以确认选中的章节、move sequence、n-gram 大小和 guardpack 设置。

`--fail-on none` 适合日常写作探索；`--fail-on medium` 适合分享或投稿前；`--fail-on high` 适合较宽松的 CI 门禁。只有在明确不做重合检测时才使用 `--style-only`。

审计报告默认不输出草稿片段。只有当你确认可以保存或分享草稿片段时，才使用 `--include-excerpts`。

## 许可证

Apache-2.0，见 [LICENSE](LICENSE)。

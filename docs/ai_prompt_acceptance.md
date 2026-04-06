# AI 提示词与心理学框架验收文档

## 1. 文档目的

这份文档用于跟踪论文 3.6.4 节相关实现的整改与验收进度。

后续工作方式：

1. 按用户指令逐项修改代码。
2. 每完成一项，同步更新本文件的状态、影响范围和验证结果。
3. 以本文件作为“当前验收基线”，避免代码和说明再次脱节。

## 2. 当前涉及文件

| 文件 | 当前职责 | 验收关注点 |
| --- | --- | --- |
| `modules/ai_analyzer.py` | 同步 AI 分析主链路 | 语气提示词、主系统提示词、心理学理论映射 |
| `modules/ai_analysis.py` | 异步/备用 AI 分析链路 | 与主链路的理论框架一致性、语气一致性 |
| `modules/reference_pipeline.py` | 规则式心理学报告 | 理论维度覆盖、阈值一致性、解释质量 |
| `modules/advisor.py` | 规则式优化建议 | 与心理学报告和 AI 分析口径一致 |

## 3. 当前问题基线

以下问题来自本轮评审结论，作为后续整改的起点。

### 3.1 主提示词缺少理论框架

- `modules/ai_analyzer.py` 中的 `BASE_SYSTEM_PROMPT` 目前更强调“基于数据说话”。
- Prompt 没有明确告诉模型如何将视觉特征映射到认知心理学理论。
- 结果是模型即使看到 `entropy`、`text_density` 等指标，也不一定会稳定产出“认知负荷”“信息过载”等理论化解释。

### 3.2 心理学规则报告覆盖不足

- `modules/reference_pipeline.py` 的 `generate_psychological_report()` 当前只覆盖少数维度。
- 还没有完整覆盖以下论文提到的理论：
  - 认知负荷理论
  - 信息过载理论
  - 选择性注意理论
  - 中心偏好理论
- 现有判断条件还存在硬编码问题，例如阈值与 `config.py` 中的配置不完全一致。

### 3.3 备用 AI 链路过于简化

- `modules/ai_analysis.py` 的提示词版本更轻量。
- 其中的系统提示词没有承接心理学框架。
- 语气说明以英文为主，与主链路中文语境不统一。

### 3.4 四种语气只区分“怎么说”，没有区分“怎么解读”

- 当前语气主要体现表达风格差异。
- 但无论哪种语气，都应该沿用同一套理论框架来解释数据。
- 正确目标不是“每个语气一套理论”，而是“同一理论框架下，不同语气输出”。

## 4. 目标理论框架

后续整改以以下四个理论维度为主线：

1. 认知负荷理论
2. 信息过载理论
3. 选择性注意理论
4. 中心偏好理论

验收时要求这些理论不是只出现在文案里，而是能对应到实际特征和判断逻辑。

## 5. 验收项总表

| 编号 | 验收项 | 目标说明 | 相关文件 | 当前状态 |
| --- | --- | --- | --- | --- |
| A1 | 主 AI Prompt 理论化 | `ai_analyzer.py` 中主提示词明确给出理论框架、特征映射和输出边界 | `modules/ai_analyzer.py` | 已完成 |
| A2 | 四种语气继承同一理论框架 | `professional / gentle / direct / marketing` 只改变表达风格，不改变理论主线 | `modules/ai_analyzer.py` | 已完成 |
| A3 | 备用 AI 链路对齐 | `ai_analysis.py` 的系统提示词、语气定义、输出约束与主链路保持一致 | `modules/ai_analysis.py` | 已完成 |
| A4 | 心理学规则报告补全 | `generate_psychological_report()` 覆盖四个理论维度，并给出更稳健的特征解释 | `modules/reference_pipeline.py` | 已完成 |
| A5 | 阈值来源统一 | 心理学报告和规则建议尽量复用 `config.py` 阈值，减少散落硬编码 | `modules/reference_pipeline.py`, `modules/advisor.py`, `config.py` | 已完成 |
| A6 | 建议与心理学报告口径统一 | 规则建议、心理学报告、AI 分析三者不要互相打架 | `modules/advisor.py`, `modules/reference_pipeline.py`, `modules/ai_analyzer.py`, `modules/ai_analysis.py` | 已完成 |
| A7 | 输出语义可回溯 | 至少能说明“哪个特征触发了哪种理论解释”，避免空泛结论 | `modules/ai_analyzer.py`, `modules/reference_pipeline.py` | 待完成 |
| A8 | 不破坏现有接口 | 现有 `/ai-analysis` 请求结构、前端语气切换、缓存逻辑不因 prompt 整改而失效 | `api.py`, `front/src/api/ai.ts`, `front/src/components/AIAnalysisCard.tsx` | 已完成 |

## 6. 详细验收标准

### A1 主 AI Prompt 理论化

通过标准：

- `BASE_SYSTEM_PROMPT` 或等效主提示词中明确写出四个理论维度。
- Prompt 中说明常见特征与理论的关联方式，例如：
  - `entropy` / `text_density` 可关联认知负荷与信息过载
  - `subject_area_ratio` / 画面聚焦可关联选择性注意与中心偏好
  - `contrast` / `brightness` / `color_saturation` 可辅助判断注意力集中与视觉唤醒
- Prompt 明确限制模型只能基于已有结构化数据解释，不允许虚构图片内容。

### A2 四种语气继承同一理论框架

通过标准：

- 四种语气都保留同样的心理学解读框架。
- 语气差异只体现在表达方式，不体现在分析维度缺失。
- 同一输入下，四种输出应体现：
  - 关注点一致
  - 理论一致
  - 语气不同

### A3 备用 AI 链路对齐

通过标准：

- `modules/ai_analysis.py` 不再是“无心理学框架”的弱化版本。
- 中英文混用的语气定义整理为与主链路一致的表达方式。
- 输出要求、理论框架、错误处理口径与主链路尽量对齐。

### A4 心理学规则报告补全

通过标准：

- `generate_psychological_report()` 至少输出四个理论维度中的主要判断。
- 每个理论维度都要有明确触发条件或解释逻辑。
- 文本不是简单罗列术语，而是能说明：
  - 当前画面表现
  - 潜在心理影响
  - 优化方向

### A5 阈值来源统一

通过标准：

- 能复用 `config.py` 的地方优先复用，不再散落多个魔法数字。
- 如确实需要新增阈值，应集中配置，并写明用途。
- 同一特征的“高/低”判断在不同模块中不要出现明显冲突。
- `generate_psychological_report()` 不再额外写入局部硬编码阈值，例如 `0.12 / 0.15 / 0.25` 这类只在单个函数内生效的判断。

### A6 建议与心理学报告口径统一

通过标准：

- `advisor.py` 的规则建议不与心理学报告和 AI 分析互相矛盾。
- 相同问题在不同模块中表述可不同，但结论方向要一致。
- 优先级、问题描述、优化建议应能互相印证。

### A7 输出语义可回溯

通过标准：

- 无论是 AI 输出还是规则输出，都尽量能回到具体特征。
- 避免只说“画面有问题”“吸引力不足”这类空泛结论。
- 至少应能看出“为什么这样判断”。

### A8 不破坏现有接口

通过标准：

- `/ai-analysis` 的请求结构保持兼容。
- 前端语气切换仍可正常触发不同风格分析。
- 前端缓存键逻辑保持有效，避免因输出整改导致重复请求失控。
- `/analyze` 的核心特征提取与 CTR 预测应与 `heatmap/untitled7.py` 保持同源，不混入会改变核心输入定义的新预处理链。
- 如果 `untitled7.py` 没有对外传出某类原始参数，后端响应与前端展示层也不应继续伪造或补零这些参数。
- 视觉特征板块应保留，但只展示 `untitled7.py` 同源链路当前真实输出的指标，不额外展示 `brightness / contrast / saturation` 这类未输出字段。
- AI 二次分析应保留，并复用 `/analyze` 返回的同源特征子集与 `ctr.score`。

## 7. 回归验证建议

每轮改动后至少核对以下内容：

1. `/ai-analysis` 仍可正常返回结果。
2. 四种语气仍可切换，且不会报错。
3. 同一输入下，四种语气的理论框架一致，但措辞不同。
4. 高视觉熵 / 高文字密度样本能稳定出现“认知负荷”或“信息过载”方向解释。
5. 主体过小、焦点弱的样本能稳定出现“选择性注意”或“中心偏好”方向解释。
6. 规则建议、心理学报告、AI 输出之间没有明显冲突。

## 8. 迭代记录

后续每次按用户指令修改时，在这里追加记录。

| 日期 | 指令摘要 | 变更文件 | 影响验收项 | 验证结果 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 2026-04-07 | 建立初版验收文档 | `docs/ai_prompt_acceptance.md` | A1-A8 | 文档建立完成 | 作为后续逐项整改基线 |
| 2026-04-07 | 重写 `ai_analyzer.py` 主系统提示词与心理学特征映射 | `modules/ai_analyzer.py`, `docs/ai_prompt_acceptance.md` | A1, A2 | 已完成代码替换，待后续结合真实样本继续验证输出效果 | 四种语气继续沿用独立语气说明，但统一继承新的理论框架 |
| 2026-04-07 | 重写主链路/备用链路语气提示词，并重写心理学规则报告 | `modules/ai_analyzer.py`, `modules/ai_analysis.py`, `modules/reference_pipeline.py`, `docs/ai_prompt_acceptance.md` | A3, A4, A5 | 已完成代码替换与语法检查 | A5 当前仅部分落地，新增的 0.12 / 0.15 / 0.25 等阈值后续仍需统一收口 |
| 2026-04-07 | 将 `advisor.py` 规则建议改为心理学术语口径，并与心理学报告对齐 | `modules/advisor.py`, `docs/ai_prompt_acceptance.md` | A6 | `advisor.py` 语法检查通过 | 规则建议现已显式引用认知负荷、信息过载、选择性注意、中心构图等理论表述 |
| 2026-04-07 | 删除 `generate_psychological_report()` 中新增的局部数值判断，改为复用现有阈值或描述性解释 | `modules/reference_pipeline.py`, `docs/ai_prompt_acceptance.md` | A4, A5 | `reference_pipeline.py` 语法检查通过 | 已移除 `6.0 / 0.12 / 0.15 / 0.2 / 0.25 / 0.3 / 0.4 / 0.6` 等仅在报告函数内部生效的阈值判断 |
| 2026-04-07 | 将 `/analyze` 核心链路收口到 `untitled7.py` 同源算法，并移除前端对缺失特征的补零误导 | `api.py`, `modules/advisor.py`, `modules/reference_pipeline.py`, `front/src/api/analyze.ts`, `front/src/app/components/DemoPage.tsx`, `docs/ai_prompt_acceptance.md` | A4, A8 | 样例图实测与 `untitled7.py` 特征和 CTR 完全一致 | 后端核心特征与 CTR 预测改为直接复用 `reference_pipeline`，不再混入 `preprocessor.py` / `feature_extractor.py` 的新链路结果 |
| 2026-04-07 | 删除 `untitled7.py` 未输出的扩展特征字段，并阻止前端将缺失值补零后误展示 | `api.py`, `front/src/api/analyze.ts`, `front/src/components/AIAnalysisCard.tsx`, `docs/ai_prompt_acceptance.md` | A8 | 前端改为按真实返回字段渲染 | 不再补零伪造 `brightness / contrast / saturation` 等不在同源输出范围内的字段 |
| 2026-04-07 | 删除与 `untitled7.py` 核心算法不一致且已失效的链路模块，并将向量预计算脚本改回同源实现 | `api.py`, `precompute_vectors.py`, `modules/ctr_predictor.py`, `modules/feature_extractor.py`, `modules/preprocessor.py`, `README.md`, `docs/ai_prompt_acceptance.md` | A8 | Python 语法检查通过，仓库内已无运行时引用，前端 `pnpm build` 通过 | `precompute_vectors.py` 改为直接复用 `reference_pipeline.get_clip_feature()`，`ctr_predictor / feature_extractor / preprocessor` 已删除 |
| 2026-04-07 | 恢复视觉特征板块与 AI 二次分析，仅保留 `untitled7.py` 同源输出的 5 个特征字段 | `api.py`, `modules/ai_analyzer.py`, `front/src/components/AIAnalysisCard.tsx`, `front/src/utils/featureDisplay.ts`, `README.md`, `docs/ai_prompt_acceptance.md` | A8 | Python 语法检查通过，前端 `pnpm build` 通过 | `/analyze` 重新返回 `entropy / text_density / subject_area_ratio / edge_density / color_saturation`，前端特征板块和 AI 卡片同步恢复 |
| 2026-04-07 | 修复后端刚启动时首次点击“开始分析”偶发 `Failed to fetch` 的问题 | `front/src/api/analyze.ts`, `front/src/hooks/useAnalyze.ts`, `README.md`, `docs/ai_prompt_acceptance.md` | A8 | 前端 `pnpm build` 通过，待浏览器交互复测 | 首次网络失败时前端会先轮询 `/health`，待后端就绪后自动重试一次，并把兜底报错改成更明确的中文提示 |

## 9. 后续更新规则

后续每完成一项整改，需要同步更新本文件：

1. 修改“验收项总表”中的状态。
2. 在“迭代记录”补一条对应记录。
3. 如果新增了判断规则或阈值，补到对应验收标准中。
4. 如果实现方案发生变化，先更新文档，再继续下一项代码修改。

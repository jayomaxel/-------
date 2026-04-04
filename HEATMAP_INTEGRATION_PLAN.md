# Heatmap 参考脚本并入后端方案（修订版）

## 0. 修订说明

本文档基于 Codex 初版方案修订，主要修正以下问题：

- 阶段一与阶段二存在硬依赖关系，原方案将其拆为可独立执行的两步，实际不可行——已合并
- 原方案缺少前端对接章节，而"前后端接不上"恰恰是当前最大痛点——已补充
- 原方案建议新增 3-4 个文件（`feature_schemas.py` / `model_profiles.py` / `readiness.py`），对比赛项目而言过度工程化——已精简
- 原方案对 `scikit-learn` / `xgboost` 版本风险描述过轻，该风险实际是阻断性前置条件——已提权为第 0 步
- 补充了具体代码示例和验证命令，便于直接执行


## 1. 方案目标

本方案用于将 `heatmap/untitled7.py` 中已经存在的模型资源和训练口径，逐步并入当前 FastAPI 后端，**并确保前端能正常调通 `/analyze` 接口**，同时保持以下原则：

- `untitled7.py` 保持参考脚本身份，不作为主服务代码直接改造
- 现有前端接口契约不变：`/analyze` 仍返回 `features / ctr / heatmap_base64 / similar / advice`
- 优先解决 CTR 模型长期处于 mock 模式的问题
- 不因为相似检索或数据集缺失而让整个 `/analyze` 直接 500
- **前端能够成功上传图片、拿到完整 JSON 响应、正确渲染结果**


## 2. 核心决策

### 2.1 关于 `untitled7.py`

`heatmap/untitled7.py` 的定位调整为：

- 训练口径参考
- 特征定义参考
- 单机实验脚本
- 结果对照脚本

不建议让它直接承担以下职责：

- FastAPI 路由逻辑
- 上传文件流处理
- API 响应格式组织
- 生产环境异常处理
- 健康检查

结论：

`untitled7.py` 不动或少动，仅作为“规范来源”和“对照样本”保留。


## 3. 当前问题总结

### 3.1 现有主后端的问题

当前后端 `api.py + modules/*` 主要问题：

1. `models/ctr_xgboost_model.pkl` 和 `models/ctr_feature_scaler.pkl` 缺失，CTR 预测退回 mock 值。
2. `modules/ctr_predictor.py` 当前按 514 维特征组装输入：
   - `entropy`
   - `text_density`
   - `clip_vector(512)`
3. `heatmap/ctr_feature_scaler.pkl` 实际需要 517 维特征。
4. 相似检索依赖 `data/` 目录和 Excel 元数据，当前缺失时会导致 `/analyze` 整体失败。
5. `/health` 目前只做存活检查，不做资源就绪检查。
6. **`scikit-learn` 和 `xgboost` 版本可能与模型训练环境不一致，导致 `.pkl` 文件无法反序列化——此问题是阻断性的，必须在所有其他步骤之前验证。**

### 3.2 前端对接的问题

当前前后端无法联通，已知或潜在原因：

1. 前端是否使用 `multipart/form-data` 上传图片？字段名是否为 `file`？（后端 `UploadFile = File(...)` 要求字段名为 `file`）
2. 前端开发服务器（通常 3000 或 5173 端口）与后端（8000 端口）之间的跨域问题——虽然 `api.py` 已配置 `allow_origins=["*"]`，但需确认前端请求未被浏览器拦截。
3. `start_all.bat` 是否正确同时启动了前端和后端？端口是否冲突？
4. 前端期望的 response 字段与 `api.py` 实际返回是否一致？需逐字段核对。
5. 后端任何一个环节抛异常都会导致整体 500，前端拿到的是 `{"error": "..."}` 而非预期结构，JS 端可能直接崩溃。

### 3.3 `untitled7.py` 的口径

`heatmap/untitled7.py` 里的全局模型使用 517 维输入：

- `entropy`
- `text_density`
- `subject_area_ratio`
- `edge_density`
- `color_saturation`
- `clip_vector(512)`

因此：

- 现有 514 维主链不能直接加载 `heatmap` 目录下的模型
- 如果要使用该模型，必须按其训练口径重新适配输入特征


## 4. 方案边界

### 4.1 本阶段要做的事

1. 使用 `heatmap` 目录里的全局 CTR 模型恢复真实 CTR 预测
2. 保持 `untitled7.py` 不直接进入服务链路
3. 对现有 `/analyze` 做分段降级
4. 让 `/health` 能反映系统是否真正“可用”
5. **确保前端能成功调用 `/analyze` 并正确渲染返回数据**

### 4.2 本阶段不做的事

1. 不重写 `untitled7.py`
2. 不让 `untitled7.py` 直接 import 到 FastAPI 路由
3. 不在本阶段替换当前主热力图算法
4. 不在本阶段重训模型
5. 不在本阶段引入任务队列或异步作业系统


## 5. 推荐总体架构

### 5.1 总体思路

采用“参考脚本保留 + 正式模块适配”的结构：

- `heatmap/untitled7.py`
  - 保留
  - 继续作为参考脚本
  - 仅用于验证训练口径、单机对照、人工实验

- `modules/feature_extractor.py`
  - 扩展正式服务所需的额外特征
  - 输出同时覆盖 514 维方案和 517 维方案所需字段

- `modules/ctr_predictor.py`
  - 支持多模型配置
  - 按模型 schema 组装不同特征向量

- `api.py`
  - 继续作为唯一服务入口
  - 保持前端接口不变
  - 对每一段分析链路做容错和降级


## 6. 文件影响矩阵

### 6.1 不建议修改的文件

- `heatmap/untitled7.py`

处理原则：

- 保持原脚本身份
- 不改算法
- 不改现有预测流程
- 不让其直接承担 API 运行职责

### 6.2 建议小改的文件

- `config.py`
- `modules/feature_extractor.py`
- `modules/ctr_predictor.py`
- `modules/heatmap.py`
- `modules/retriever.py`
- `api.py`

### 6.3 关于新增文件（精简原则）

原方案建议新增 `feature_schemas.py`、`model_profiles.py`、`readiness.py` 等文件。

**对于比赛项目，不建议新增这些文件。** 理由：

- 每多一个文件就多一层调试成本
- 这些逻辑体量很小，完全可以内联到现有模块中
- 比赛评委关注的是功能是否跑通，而非架构是否优雅

替代方案：

- 模型路径和维度配置 → 直接写在 `config.py` 里
- 特征 schema 定义 → 直接写在 `ctr_predictor.py` 的常量区
- 资源检查逻辑 → 直接写在 `api.py` 的 `/health` 路由中

## 7. 具体实施方案

### 7.0 前置步骤（阻断性）：验证模型文件可加载

**此步骤必须在所有代码修改之前完成。如果失败，后续步骤全部无意义。**

在你的运行环境中直接执行：

```python
import pickle, sys

try:
    with open("heatmap/ctr_xgboost_model_global.pkl", "rb") as f:
        model = pickle.load(f)
    print(f"[OK] model loaded, type={type(model).__name__}")
except Exception as e:
    print(f"[FAIL] model load error: {e}")
    sys.exit(1)

try:
    with open("heatmap/ctr_feature_scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    print(f"[OK] scaler loaded, n_features={scaler.n_features_in_}")
except Exception as e:
    print(f"[FAIL] scaler load error: {e}")
    sys.exit(1)
```

如果出现 `sklearn` 或 `xgboost` 版本不兼容错误：

- 方案 A：在 `requirements.txt` 中锁定与训练环境一致的版本，重新安装
- 方案 B：联系模型提供方（做 `untitled7.py` 的同学），在他的环境中重新导出模型

**如果这一步过不了，不要往下走。**


### 7.1 阶段一（原 7.1 + 7.2 + 7.3 合并）：恢复真实 CTR 预测

**重要修订说明：原方案将"接入模型"、"补齐特征"、"适配 schema"拆为三个独立阶段。实际上这三步存在硬依赖——`heatmap/ctr_feature_scaler.pkl` 要求 517 维输入，只切换模型路径而不补齐特征会导致 `scaler.transform()` 直接报维度错误。因此这三步必须作为一个原子操作一起完成。**

目标：

让主服务能使用 `heatmap/` 下的 517 维全局 CTR 模型完成真实预测。

具体做法（四件事一起做）：

**A. 修改 `config.py`**

```python
# 新增 heatmap 全局模型配置
GLOBAL_MODEL_PATH = "heatmap/ctr_xgboost_model_global.pkl"
GLOBAL_SCALER_PATH = "heatmap/ctr_feature_scaler.pkl"
GLOBAL_FEATURE_SCALAR_COLS = [
    "entropy", "text_density",
    "subject_area_ratio", "edge_density", "color_saturation"
]
GLOBAL_FEATURE_DIM = len(GLOBAL_FEATURE_SCALAR_COLS) + CLIP_DIM  # = 517

# 将默认路径切换到全局模型
MODEL_PATH = GLOBAL_MODEL_PATH
SCALER_PATH = GLOBAL_SCALER_PATH
FEATURE_SCALAR_COLS = GLOBAL_FEATURE_SCALAR_COLS
FEATURE_DIM = GLOBAL_FEATURE_DIM
```

**B. 在 `modules/feature_extractor.py` 中补齐三个特征**

从 `untitled7.py` 中**抄写**（不是 import）以下三个特征的计算逻辑：

1. `subject_area_ratio` — 主体面积占比
2. `edge_density` — 边缘密度
3. `color_saturation` — 色彩饱和度

实施原则：

- 阅读 `untitled7.py` 中对应函数的实现，理解算法
- 在 `feature_extractor.py` 中重新实现为独立函数
- **不要** `import untitled7` 或 `from heatmap.untitled7 import ...`
- 确保 `extract_features()` 返回的 dict 中包含这三个新 key

**C. 修改 `modules/ctr_predictor.py` 的特征拼接**

将特征向量拼接顺序改为 517 维口径：

```python
# 拼接顺序必须与 scaler 训练时一致
feature_vector = np.concatenate([
    [features["entropy"]],
    [features["text_density"]],
    [features["subject_area_ratio"]],
    [features["edge_density"]],
    [features["color_saturation"]],
    features["clip_vector"]   # 512 维
])
# 总计 5 + 512 = 517 维
```

**D. 保留旧 514 维路径作为 fallback**

在 `ctr_predictor.py` 中，如果 517 维模型加载失败，可以 fallback 到旧的 514 维逻辑（如果旧模型文件存在）或返回 mock 值。

验收标准：

- `scaler.transform()` 不报维度错误
- `/analyze` 返回的 `ctr.score` 不再固定接近 mock 值
- `untitled7.py` 未被修改


### 7.2 阶段二：保持现有热力图主算法不变

目标：

在本阶段不改动主热力图的生成策略，避免引入额外变量。

当前建议：

- 继续使用 `modules/heatmap.py` 的正式服务化实现
- 它已经适配了内存图像输入和 base64 返回链路
- 只让它依赖新的 `predict_ctr()`，而不是依赖 `untitled7.py`

结论：

本阶段不会改变当前主服务热力图算法。

`untitled7.py` 中的 `generate_attention_heatmap()`：

- 保留
- 不删
- 不改
- 作为未来“快速热力图模式”候选实现


### 7.3 阶段三：`/analyze` 分段降级（关键步骤）

目标：

即使部分模块失败（`data/` 缺失、Excel 缺失、检索不可用），接口也不应整体 500。

**当前 `api.py` 的核心问题：** 整个 `/analyze` 路由被一个大 try-except 包裹，任何一个环节抛异常都会导致前端收到 `{"error": "..."}` 而非预期的 JSON 结构，前端 JS 很可能因为访问不存在的字段而直接崩溃。

推荐改法（将 `api.py` 的 `/analyze` 改为分段 try-except）：

```python
@app.post('/analyze')
async def analyze(file: UploadFile = File(...)) -> Any:
    warnings = []

    # === 图像读取（此步失败则整体失败，合理） ===
    try:
        file_bytes = await file.read()
        pil_image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
        image_array = np.array(pil_image)
        processed_image = preprocess_image(image_array)
        features = extract_features(processed_image)
    except Exception as exc:
        return JSONResponse(status_code=400,
            content={'error': f'图像处理失败: {exc}'})

    # === CTR 预测（失败则降级） ===
    try:
        ctr_score, ctr_percentile = predict_ctr(features)
    except Exception:
        ctr_score, ctr_percentile = 0.5, 50
        warnings.append('ctr_fallback_mock_value')

    # === 热力图生成（失败则返回原图） ===
    try:
        heatmap_array = generate_heatmap(processed_image)
    except Exception:
        heatmap_array = processed_image
        warnings.append('heatmap_fallback_original_image')

    # === 相似检索（失败则返回空数组） ===
    similar_items = []
    try:
        similar_items = retrieve_similar(
            features['clip_vector'], top_k=config.TOP_K_SIMILAR)
    except Exception:
        warnings.append('retrieval_disabled')

    # === 建议生成（失败则返回空数组） ===
    advice = []
    try:
        advice = generate_advice(features, float(ctr_score), int(ctr_percentile))
    except Exception:
        warnings.append('advice_generation_failed')

    # === 组装响应（保持原有字段结构不变） ===
    response = {
        'features': {
            'entropy': _to_float(features.get('entropy', 0.0)),
            'text_density': _to_float(features.get('text_density', 0.0)),
            'brightness': _to_float(features.get('brightness', 0.0)),
            'contrast': _to_float(features.get('contrast', 0.0)),
            'saturation': _to_float(features.get('saturation', 0.0)),
        },
        'ctr': {
            'score': _to_float(ctr_score),
            'percentile': int(ctr_percentile),
        },
        'heatmap_base64': _rgb_array_to_base64(heatmap_array),
        'similar': [
            {
                'rank': int(item.get('rank', index + 1)),
                'img_name': str(item.get('img_name', '')),
                'similarity': _to_float(item.get('similarity', 0.0)),
                'relative_ctr': _to_float(item.get('relative_ctr', 0.0)),
                'price': _to_float(item.get('price', 0.0)),
                'img_base64': _similar_image_to_base64(item.get('img_path')),
            }
            for index, item in enumerate(similar_items[:config.TOP_K_SIMILAR])
        ],
        'advice': [
            {
                'priority': str(item.get('priority', '')),
                'category': str(item.get('category', '')),
                'issue': str(item.get('issue', '')),
                'suggestion': str(item.get('suggestion', '')),
            }
            for item in advice
        ],
        'warnings': warnings,  # 新增字段，前端可选消费
    }
    return response
```

关键原则：

- 只有图像读取失败才返回非 200（400），其余模块失败一律降级
- `warnings` 字段是增量的，前端暂时不用也不影响现有逻辑
- 每个 except 块不要 `pass`，要记录 warning 便于调试

验收标准：

- 即使 `data/` 目录完全缺失，接口也返回 200
- `similar` 为空数组 `[]` 而不是整体 500
- 响应中 `warnings` 数组能反映哪些模块降级了


### 7.4 阶段四：把 `/health` 升级为 readiness 检查

当前 `/health` 只说明服务启动了，不说明是否“真的能分析”。

推荐改造方向：

检查项至少包含：

1. FastAPI 服务是否启动
2. CTR 模型文件是否存在
3. scaler 是否存在
4. 向量缓存是否存在
5. Excel 数据是否存在
6. 图片目录是否存在
7. 检索链路是否可用

建议返回结构：

```json
{
  "status": "ok",
  "ready": false,
  "components": {
    "ctr_model": true,
    "ctr_scaler": true,
    "vector_cache": true,
    "dataset_excel": false,
    "dataset_images": false,
    "retrieval": false
  }
}
```



### 7.5 阶段五（新增）：前端对接验证

**原方案完全没有覆盖前端对接，但这是你反馈的最大痛点。本节补充。**

目标：

确保前端页面能成功上传图片、调通 `/analyze`、正确渲染结果。

#### 7.5.1 排查清单

按顺序逐项验证：

**Step 1：后端能否独立跑通？**

```bash
# 启动后端
python api.py

# 用 curl 测试（不经过前端）
curl -X POST http://localhost:8000/analyze \
  -F "file=@test_image.jpg" \
  | python -m json.tool
```

如果这一步返回了正确的 JSON，说明后端没问题，问题在前端或网络层。

**Step 2：前端请求格式是否正确？**

后端 `api.py` 使用 `UploadFile = File(...)`，要求：

- 请求方法：`POST`
- Content-Type：`multipart/form-data`
- 字段名必须是 `file`（不是 `image`、不是 `photo`）

前端代码应类似：

```typescript
const formData = new FormData();
formData.append('file', selectedFile);  // 字段名必须是 'file'

const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData,
  // 注意：不要手动设置 Content-Type，浏览器会自动加 boundary
});

const data = await response.json();
```

常见错误：

- `formData.append('image', file)` → 字段名不对，后端收不到
- 手动设置 `Content-Type: multipart/form-data` → 缺少 boundary，后端解析失败
- 使用 `JSON.stringify` 发送 → 格式完全不对

**Step 3：CORS 是否真正生效？**

虽然 `api.py` 已配置 `allow_origins=["*"]`，但要确认：

- 前端是否通过 `http://localhost:3000`（或其他端口）访问？
- 浏览器开发者工具 Network 面板是否有 CORS 报错？
- 是否有浏览器扩展拦截了请求？

**Step 4：`start_all.bat` 是否正确？**

检查批处理文件是否同时启动了前端和后端，且端口不冲突。典型结构应该是：

```bat
start cmd /k "cd /d %~dp0 && python api.py"
start cmd /k "cd /d %~dp0\网页界面设计 (1) && npm run dev"
```

**Step 5：前端是否正确处理了降级响应？**

加入分段降级后，前端需要能处理以下情况：

- `similar` 为空数组 → 不渲染相似图片区域，或显示"暂无数据"
- `advice` 为空数组 → 同理
- `warnings` 存在 → 可选：在页面上显示提示信息

建议在前端加防御性代码：

```typescript
// 防御性访问，避免字段缺失导致崩溃
const similar = data.similar || [];
const advice = data.advice || [];
const warnings = data.warnings || [];
```

#### 7.5.2 前后端接口契约确认

以下是 `/analyze` 接口的完整契约，前后端必须对齐：

| 字段路径 | 类型 | 说明 | 可能缺失？ |
|---------|------|------|-----------|
| `features.entropy` | float | 信息熵 | 否 |
| `features.text_density` | float | 文字密度 | 否 |
| `features.brightness` | float | 亮度 | 否 |
| `features.contrast` | float | 对比度 | 否 |
| `features.saturation` | float | 饱和度 | 否 |
| `ctr.score` | float | CTR 预测分 | 否（降级时为 0.5） |
| `ctr.percentile` | int | CTR 百分位 | 否（降级时为 50） |
| `heatmap_base64` | string | 热力图 PNG base64 | 否（降级时为原图） |
| `similar` | array | 相似图片列表 | 可能为空数组 |
| `advice` | array | 优化建议列表 | 可能为空数组 |
| `warnings` | array | 降级警告（新增） | 可能为空数组 |

## 8. 对 `untitled7.py` 的实际影响评估

### 8.1 不会发生的影响

按本方案实施时，以下内容不会发生：

- 不会强制把 `untitled7.py` 改写成 FastAPI 模块
- 不会改变它现有的 CTR 预测算法
- 不会改变它现有的 attention heatmap 算法
- 不会把它改成生产服务入口

### 8.2 可能发生的最小影响

如果后续需要为团队协作增加说明，最多只建议做非常轻量的改动：

- 在文件头部补一段注释，说明其“参考脚本”身份
- 记录该脚本对应的模型文件与特征口径

这类改动不是必须项。


## 9. 实施顺序建议（修订版）

### 第零步（阻断性前置）

验证 `.pkl` 模型文件能在当前环境加载。

验收标准：

- `pickle.load()` 无报错
- `scaler.n_features_in_` 输出 517

**如果此步失败，立即停止，先解决依赖版本问题。**

### 第一步

同时完成：切换模型路径 + 补齐 3 个特征 + 适配 517 维拼接。

验收标准：

- `/analyze` 不再出现 mock CTR 值
- `scaler.transform()` 不报维度错误
- `untitled7.py` 未被修改

### 第二步

将 `/analyze` 改为分段降级。

验收标准：

- 即使缺失 `data/`，接口也返回 200
- `similar` 为空数组而不是整体 500
- 响应中包含 `warnings` 字段

### 第三步

前端对接验证。

验收标准：

- 前端能上传图片并收到 JSON 响应
- 页面能正确渲染 heatmap、CTR 分数、特征值
- `similar` 为空时页面不崩溃

### 第四步（可选）

升级 `/health`。

验收标准：

- 能一眼看出当前是"完整模式"还是"降级模式"

说明：

第四步优先级最低，比赛演示时评委不会去看 `/health` 端点。如果时间紧张可以跳过。

## 10. 风险与注意事项

### 10.1 版本风险（严重度：阻断性）

**此风险已提权为阻断性前置条件，见 7.0 节。**

当前 `heatmap` 下模型和 scaler 已存在版本兼容警告：

- `scikit-learn` 版本不一致 → 可能导致 `pkl` 文件无法反序列化
- `xgboost` 序列化版本不一致 → 可能导致 model.predict() 直接报错

应对方案（按优先级排列）：

1. **首选：** 在 `requirements.txt` 中锁定与训练环境一致的版本号，例如 `scikit-learn==1.3.2`、`xgboost==2.0.3`（具体版本需向模型提供方确认）
2. **备选：** 联系做 `untitled7.py` 的同学，让他在当前版本环境下重新 `pickle.dump()` 导出模型
3. **最后手段：** 如果以上都不行，CTR 模块保持 mock 模式，优先保证其他功能跑通

### 10.2 配置编码风险

`config.py` 当前有中文乱码痕迹。

建议：

- 后续单独安排一轮 UTF-8 清理
- 内部 dataset key 改成英文稳定标识
- 展示文案不要直接复用配置 key

### 10.3 性能风险

`modules/heatmap.py` 目前是 CPU 重任务。

本方案第一阶段不处理性能，只处理正确性和稳定性。

后续再考虑：

- 任务队列
- 快速模式热力图
- 模型预热


### 10.4 前端对接风险

前端（`网页界面设计 (1)` 目录）与后端之间可能存在：

- 请求格式不匹配（字段名、Content-Type）
- 端口冲突或 CORS 问题
- 前端代码假设响应一定有某些字段，缺失时 JS 报错

建议：

- 在后端完成分段降级后，用 curl 先确认接口正常
- 再逐步调前端，优先保证"上传图片 → 拿到 JSON → 渲染 heatmap"这条主路径

## 11. 最终建议（修订版）

推荐采用以下执行原则：

1. **先验证模型能加载**，这是一切的前提
2. `untitled7.py` 不作为主服务代码直接改造，只抄写其特征计算逻辑
3. 正式服务只改 `modules/*`、`config.py` 和 `api.py`，不新增额外文件
4. 模型接入 + 特征补齐 + schema 适配必须一步到位（原子操作）
5. `/analyze` 必须做分段降级，杜绝整体 500
6. **后端改完后必须验证前端对接**，这才是"接上"的真正含义

一句话总结：

保留 `untitled7.py`，复用它的模型和特征口径，但不要把它本身拖进主服务链路。**先确保后端单独跑通，再确保前端调得通。**

# Heatmap 参考脚本并入后端方案

## 1. 方案目标

本方案用于将 `heatmap/untitled7.py` 中已经存在的模型资源和训练口径，逐步并入当前 FastAPI 后端，同时保持以下原则：

- `untitled7.py` 保持参考脚本身份，不作为主服务代码直接改造
- 现有前端接口契约不变：`/analyze` 仍返回 `features / ctr / heatmap_base64 / similar / advice`
- 优先解决 CTR 模型长期处于 mock 模式的问题
- 不因为相似检索或数据集缺失而让整个 `/analyze` 直接 500


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

### 3.2 `untitled7.py` 的口径

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

### 6.3 建议新增的文件

建议新增正式服务层使用的适配文件，而不是碰 `untitled7.py`：

- `modules/feature_schemas.py`
  - 定义 514 维与 517 维 schema
- `modules/model_profiles.py`
  - 定义模型档位、输入维度、路径、描述
- `modules/readiness.py`
  - 聚合资源检查逻辑
- `docs/` 可选
  - 后续放运维说明和模型说明

说明：

即使不新增这些文件，也建议至少在现有模块中以“清晰结构”的形式实现这些职责，而不是把所有适配逻辑堆进 `api.py`。


## 7. 具体实施方案

### 7.1 阶段一：接入 `heatmap` 全局 CTR 模型

目标：

让主服务不再依赖缺失的 `models/*.pkl`，而是能使用 `heatmap/` 下已有模型完成真实 CTR 预测。

建议做法：

1. 在 `config.py` 中新增一个模型档位，例如：
   - `global_xgb_517`
2. 将以下路径配置到新档位：
   - `heatmap/ctr_xgboost_model_global.pkl`
   - `heatmap/ctr_feature_scaler.pkl`
3. 在 `modules/ctr_predictor.py` 中引入“模型档位 -> 输入 schema”的映射。
4. 默认优先使用 `global_xgb_517`，旧 514 维模型保留为兼容路径。

这一阶段的结果：

- CTR 能恢复真实预测
- `untitled7.py` 无需修改
- 当前主 API 响应格式不变


### 7.2 阶段二：扩展正式特征提取，补齐 517 维口径

目标：

让正式服务输出与 `untitled7.py` 训练口径一致的特征集合。

建议在 `modules/feature_extractor.py` 中补齐以下特征：

1. `subject_area_ratio`
2. `edge_density`
3. `color_saturation`

实施原则：

- 尽量复用 `untitled7.py` 的计算思路
- 但不要直接 import 该脚本
- 在正式模块中重新实现为稳定的服务函数

原因：

- 避免让服务层依赖实验脚本
- 避免脚本中的路径读写、副作用输出、乱码注释进入主链


### 7.3 阶段三：将 CTR 预测从单一 schema 改为多 schema

目标：

让 `modules/ctr_predictor.py` 根据模型档位动态选择输入维度。

推荐策略：

- 514 维模型：
  - `entropy`
  - `text_density`
  - `clip_vector(512)`

- 517 维模型：
  - `entropy`
  - `text_density`
  - `subject_area_ratio`
  - `edge_density`
  - `color_saturation`
  - `clip_vector(512)`

这样做的好处：

- 新旧模型能并存
- 方便回退
- 便于后续再引入新的模型口径


### 7.4 阶段四：保持现有热力图主算法不变

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


### 7.5 阶段五：相似检索改为可降级

目标：

即使 `data/` 或 Excel 缺失，接口也不应整体失败。

推荐策略：

- CTR 失败：允许回退或返回默认值
- heatmap 失败：返回原图或空值
- similar 失败：返回空数组 `[]`
- advice 失败：返回空数组 `[]`

响应中建议增加：

- `warnings: string[]`

例如：

- `retrieval_disabled_missing_dataset`
- `mock_ctr_used`
- `heatmap_fallback_used`

说明：

这一步对前端是增量友好的。即使前端暂时不使用 `warnings`，也不会破坏现有页面。


### 7.6 阶段六：把 `/health` 升级为 readiness 检查

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


## 9. 实施顺序建议

### 第一步

接入 `heatmap` 模型资源，恢复真实 CTR 预测。

验收标准：

- `/analyze` 不再出现“CTR predictor missing model file”警告
- 返回的 `ctr.score` 不再固定接近 mock 值

### 第二步

补齐 517 维特征并支持多 schema 预测。

验收标准：

- scaler 输入维度匹配
- `predict_ctr()` 不再因维度不一致回退

### 第三步

让 `/analyze` 支持分段降级。

验收标准：

- 即使缺失 `data/`，接口也返回 200
- `similar` 为空数组而不是整体 500

### 第四步

升级 `/health`。

验收标准：

- 能一眼看出当前是“完整模式”还是“降级模式”


## 10. 风险与注意事项

### 10.1 版本风险

当前 `heatmap` 下模型和 scaler 已存在版本兼容警告：

- `scikit-learn` 版本不一致
- `xgboost` 序列化版本不一致

建议：

- 后续最好在原训练环境中重新导出标准模型格式
- 在部署环境固定 `scikit-learn` 和 `xgboost` 版本

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


## 11. 最终建议

推荐采用以下执行原则：

1. `untitled7.py` 不作为主服务代码直接改造
2. `untitled7.py` 只作为模型口径和实验实现的参考来源
3. 正式服务只改 `modules/*` 和 `api.py`
4. 第一优先级是恢复真实 CTR 预测
5. 第二优先级是让 `/analyze` 在数据不完整时仍能返回部分结果

一句话总结：

保留 `untitled7.py`，复用它的模型和特征口径，但不要把它本身拖进主服务链路。


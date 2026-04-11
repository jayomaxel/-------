"""预计算并缓存数据集的 CLIP 向量。"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

import config
from modules.reference_pipeline import get_clip_feature


def _resolve_path(path_value: str) -> Path:
    """把配置里的路径统一转成绝对路径。"""
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _extract_clip_vector_only(image_path: Path) -> np.ndarray:
    """只提取 CLIP 向量，算法与当前主链路保持同源。"""
    vector = get_clip_feature(image_path)
    if not isinstance(vector, np.ndarray) or vector.shape != (512,):
        raise ValueError(f"Invalid CLIP vector shape: {getattr(vector, 'shape', None)}")
    return vector.astype(np.float32)


def process_dataset(dataset_key: str = config.DEFAULT_DATASET) -> dict:
    """为单个数据集生成向量缓存。"""
    if dataset_key not in config.DATASETS:
        valid_keys = ", ".join(config.DATASETS.keys())
        raise ValueError(f"Unknown dataset_key: {dataset_key}. Available: {valid_keys}")

    dataset_cfg = config.DATASETS[dataset_key]
    excel_path = _resolve_path(dataset_cfg["excel_path"])
    images_dir = _resolve_path(dataset_cfg["images_dir"])
    cache_vectors_path = _resolve_path(dataset_cfg["cache_vectors"])

    print(f"\n[INFO] 开始处理数据集: {dataset_key}")
    print(f"[INFO] Excel: {excel_path}")
    print(f"[INFO] Images: {images_dir}")
    print(f"[INFO] Cache: {cache_vectors_path}")

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel 文件不存在: {excel_path}")

    try:
        dataframe = pd.read_excel(excel_path)
    except Exception as exc:
        raise RuntimeError(f"读取 Excel 失败: {excel_path}. 错误: {exc}") from exc

    if config.COL_IMG_NAME not in dataframe.columns:
        raise ValueError(
            f"Excel 缺少必要列: {config.COL_IMG_NAME}. 实际列: {list(dataframe.columns)}"
        )

    image_names = dataframe[config.COL_IMG_NAME].tolist()
    total_count = len(image_names)
    vectors = np.zeros((total_count, 512), dtype=np.float32)

    success_count = 0
    skipped_count = 0
    start_time = time.time()

    for idx, image_name in enumerate(image_names, start=1):
        image_name_str = str(image_name).strip() if pd.notna(image_name) else ""
        if not image_name_str:
            skipped_count += 1
            print(f"[WARNING] 第 {idx} 行图片名为空，填充零向量")
        else:
            image_path = images_dir / image_name_str
            if not image_path.exists():
                skipped_count += 1
                print(f"[WARNING] 图片不存在: {image_path}，填充零向量")
            else:
                try:
                    vectors[idx - 1] = _extract_clip_vector_only(image_path)
                    success_count += 1
                except Exception as exc:
                    skipped_count += 1
                    print(f"[WARNING] 图片处理失败: {image_path}，填充零向量。错误: {exc}")

        if idx % 100 == 0 or idx == total_count:
            elapsed = time.time() - start_time
            print(f"[INFO] 进度: 已处理 {idx}/{total_count}，耗时 {elapsed:.2f}s")

    try:
        cache_vectors_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(
            f"创建缓存目录失败: {cache_vectors_path.parent}. 错误: {exc}"
        ) from exc

    try:
        np.save(cache_vectors_path, vectors)
    except Exception as exc:
        raise RuntimeError(f"保存向量文件失败: {cache_vectors_path}. 错误: {exc}") from exc

    elapsed_total = time.time() - start_time
    print(f"[INFO] 数据集 {dataset_key} 处理完成")
    print(
        f"[INFO] 总计 {total_count} 张，成功 {success_count}，跳过 {skipped_count}，"
        f"总耗时 {elapsed_total:.2f}s"
    )

    return {
        "dataset_key": dataset_key,
        "total": total_count,
        "success": success_count,
        "skipped": skipped_count,
        "elapsed_seconds": elapsed_total,
    }


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数。"""
    dataset_choices = list(config.DATASETS.keys()) + ["all"]
    parser = argparse.ArgumentParser(description="预计算 CLIP 向量缓存")
    parser.add_argument(
        "--dataset",
        type=str,
        default="all",
        choices=dataset_choices,
        help=f"选择数据集: {', '.join(dataset_choices)}",
    )
    return parser


def main() -> None:
    """脚本入口。"""
    parser = _build_parser()
    args = parser.parse_args()

    selected_keys = (
        list(config.DATASETS.keys()) if args.dataset == "all" else [args.dataset]
    )

    overall_start = time.time()
    results: list[dict] = []
    failed: list[str] = []

    for dataset_key in selected_keys:
        try:
            results.append(process_dataset(dataset_key))
        except Exception as exc:
            failed.append(dataset_key)
            print(f"[ERROR] 数据集处理失败: {dataset_key}. 错误: {exc}")

    overall_elapsed = time.time() - overall_start
    total_images = sum(item["total"] for item in results)
    total_success = sum(item["success"] for item in results)
    total_skipped = sum(item["skipped"] for item in results)

    print("\n[INFO] ===== 全部任务统计 =====")
    print(
        f"[INFO] 数据集数量: {len(selected_keys)}，总图片: {total_images}，"
        f"成功: {total_success}，跳过: {total_skipped}，总耗时: {overall_elapsed:.2f}s"
    )

    if failed:
        failed_str = ", ".join(failed)
        raise RuntimeError(f"以下数据集处理失败: {failed_str}")


if __name__ == "__main__":
    main()

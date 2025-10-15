#!/usr/bin/env python3
"""
Dataset Toolkit 基本使用示例

这个脚本演示了如何使用 dataset_toolkit 进行基本的数据集操作
"""

from pathlib import Path
from dataset_toolkit import (
    load_yolo_from_local,
    merge_datasets,
    export_to_coco,
    export_to_txt
)


def example_basic_workflow():
    """基本工作流示例"""
    print("=" * 60)
    print("示例 1: 基本工作流")
    print("=" * 60)
    
    # 1. 加载第一个数据集
    print("\n步骤 1: 加载数据集...")
    dataset1 = load_yolo_from_local(
        "/path/to/dataset1",
        categories={0: 'cat', 1: 'dog'}
    )
    
    # 2. 加载第二个数据集
    dataset2 = load_yolo_from_local(
        "/path/to/dataset2",
        categories={0: 'car', 1: 'bicycle'}
    )
    
    # 3. 合并数据集
    print("\n步骤 2: 合并数据集...")
    final_categories = {0: 'animal', 1: 'vehicle'}
    category_mapping = {
        'cat': 'animal',
        'dog': 'animal',
        'car': 'vehicle',
        'bicycle': 'vehicle'
    }
    
    merged = merge_datasets(
        datasets=[dataset1, dataset2],
        category_mapping=category_mapping,
        final_categories=final_categories,
        new_dataset_name="merged_animal_vehicle"
    )
    
    # 4. 导出结果
    print("\n步骤 3: 导出数据集...")
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    export_to_coco(merged, str(output_dir / "merged.json"))
    export_to_txt(merged, str(output_dir / "merged.txt"))
    
    print("\n✅ 完成！")


def example_pipeline_usage():
    """使用管道API的示例"""
    print("\n" + "=" * 60)
    print("示例 2: 使用管道API")
    print("=" * 60)
    
    from dataset_toolkit.pipeline import DatasetPipeline
    
    pipeline = DatasetPipeline()
    
    result = (pipeline
        .load_yolo("/path/to/dataset1", {0: 'cat', 1: 'dog'})
        .load_yolo("/path/to/dataset2", {0: 'car'})
        .merge(
            category_mapping={
                'cat': 'animal',
                'dog': 'animal',
                'car': 'vehicle'
            },
            final_categories={0: 'animal', 1: 'vehicle'}
        )
        .export_coco("output/pipeline_merged.json")
        .get_result())
    
    # 打印摘要
    print("\n" + pipeline.get_summary())
    print("\n✅ 完成！")


def example_single_dataset_conversion():
    """单个数据集格式转换示例"""
    print("\n" + "=" * 60)
    print("示例 3: 单个数据集格式转换")
    print("=" * 60)
    
    # 加载YOLO格式
    print("\n加载YOLO格式数据集...")
    dataset = load_yolo_from_local(
        "/path/to/yolo_dataset",
        categories={0: 'person', 1: 'car', 2: 'bicycle'}
    )
    
    # 转换为COCO格式
    print("转换为COCO格式...")
    export_to_coco(dataset, "output/converted.json")
    
    print("\n✅ 完成！")


def example_batch_processing():
    """批量处理示例"""
    print("\n" + "=" * 60)
    print("示例 4: 批量处理多个数据集")
    print("=" * 60)
    
    # 待处理的数据集列表
    dataset_paths = [
        "/path/to/dataset1",
        "/path/to/dataset2",
        "/path/to/dataset3",
    ]
    
    categories = {0: 'object'}
    
    print("\n开始批量处理...")
    for dataset_path in dataset_paths:
        print(f"\n处理: {dataset_path}")
        
        # 加载
        ds = load_yolo_from_local(dataset_path, categories)
        
        # 导出
        output_name = Path(dataset_path).name
        export_to_coco(ds, f"output/{output_name}.json")
        
        print(f"  ✓ 已导出: output/{output_name}.json")
    
    print("\n✅ 批量处理完成！")


if __name__ == "__main__":
    print("\n🚀 Dataset Toolkit 使用示例\n")
    
    # 运行各个示例（注意：需要修改路径为实际路径）
    try:
        # example_basic_workflow()
        # example_pipeline_usage()
        # example_single_dataset_conversion()
        # example_batch_processing()
        
        print("\n" + "=" * 60)
        print("提示: 请根据实际情况修改数据集路径后运行相应示例")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("提示: 请确保数据集路径正确且数据格式符合要求")


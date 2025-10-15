# dataset_toolkit/pipeline.py
"""
提供链式API，让数据集处理更加流畅和优雅
"""
from typing import Dict, List, Optional
from pathlib import Path
from dataset_toolkit.models import Dataset
from dataset_toolkit.loaders.local_loader import load_yolo_from_local
from dataset_toolkit.processors.merger import merge_datasets
from dataset_toolkit.exporters.coco_exporter import export_to_coco
from dataset_toolkit.exporters.txt_exporter import export_to_txt


class DatasetPipeline:
    """
    数据集处理管道，支持链式调用
    
    示例:
        >>> pipeline = DatasetPipeline()
        >>> result = (pipeline
        ...     .load_yolo("/path/to/dataset1", {0: 'cat'})
        ...     .load_yolo("/path/to/dataset2", {0: 'dog'})
        ...     .merge(
        ...         category_mapping={'cat': 'animal', 'dog': 'animal'},
        ...         final_categories={0: 'animal'}
        ...     )
        ...     .export_coco("output.json")
        ...     .get_result())
    """
    
    def __init__(self):
        self._datasets: List[Dataset] = []
        self._current_dataset: Optional[Dataset] = None
        self._operations = []
    
    def load_yolo(self, dataset_path: str, categories: Dict[int, str]) -> 'DatasetPipeline':
        """
        加载YOLO格式数据集
        
        Args:
            dataset_path: 数据集路径
            categories: 类别映射
            
        Returns:
            self: 返回自身以支持链式调用
        """
        dataset = load_yolo_from_local(dataset_path, categories)
        self._datasets.append(dataset)
        self._current_dataset = dataset
        self._operations.append(f"加载数据集: {dataset_path}")
        return self
    
    def merge(
        self,
        category_mapping: Dict[str, str],
        final_categories: Dict[int, str],
        new_dataset_name: str = "merged_dataset"
    ) -> 'DatasetPipeline':
        """
        合并已加载的所有数据集
        
        Args:
            category_mapping: 类别映射规则
            final_categories: 最终类别体系
            new_dataset_name: 合并后的数据集名称
            
        Returns:
            self: 返回自身以支持链式调用
        """
        if len(self._datasets) < 1:
            raise ValueError("至少需要一个数据集才能执行合并操作")
        
        self._current_dataset = merge_datasets(
            datasets=self._datasets,
            category_mapping=category_mapping,
            final_categories=final_categories,
            new_dataset_name=new_dataset_name
        )
        self._operations.append(f"合并 {len(self._datasets)} 个数据集")
        return self
    
    def export_coco(self, output_path: str) -> 'DatasetPipeline':
        """
        导出为COCO格式
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            self: 返回自身以支持链式调用
        """
        if self._current_dataset is None:
            raise ValueError("没有可导出的数据集")
        
        export_to_coco(self._current_dataset, output_path)
        self._operations.append(f"导出COCO格式: {output_path}")
        return self
    
    def export_txt(
        self,
        output_path: str,
        use_relative_paths: bool = False,
        base_path: Optional[str] = None
    ) -> 'DatasetPipeline':
        """
        导出为TXT格式
        
        Args:
            output_path: 输出文件路径
            use_relative_paths: 是否使用相对路径
            base_path: 相对路径的基准目录
            
        Returns:
            self: 返回自身以支持链式调用
        """
        if self._current_dataset is None:
            raise ValueError("没有可导出的数据集")
        
        export_to_txt(self._current_dataset, output_path, use_relative_paths, base_path)
        self._operations.append(f"导出TXT格式: {output_path}")
        return self
    
    def filter_by_category(self, category_ids: List[int]) -> 'DatasetPipeline':
        """
        按类别过滤数据集（未来功能）
        
        Args:
            category_ids: 要保留的类别ID列表
            
        Returns:
            self: 返回自身以支持链式调用
        """
        # TODO: 实现类别过滤功能
        raise NotImplementedError("此功能尚未实现")
    
    def get_result(self) -> Dataset:
        """
        获取当前处理结果
        
        Returns:
            Dataset: 当前的数据集对象
        """
        if self._current_dataset is None:
            raise ValueError("管道中没有任何数据集")
        return self._current_dataset
    
    def get_summary(self) -> str:
        """
        获取管道操作摘要
        
        Returns:
            str: 操作摘要信息
        """
        summary = "数据集处理管道操作摘要:\n"
        summary += "\n".join(f"{i+1}. {op}" for i, op in enumerate(self._operations))
        
        if self._current_dataset:
            summary += f"\n\n最终结果:"
            summary += f"\n  - 数据集名称: {self._current_dataset.name}"
            summary += f"\n  - 图片数量: {len(self._current_dataset.images)}"
            summary += f"\n  - 类别: {self._current_dataset.categories}"
        
        return summary
    
    def reset(self) -> 'DatasetPipeline':
        """
        重置管道状态
        
        Returns:
            self: 返回自身以支持链式调用
        """
        self._datasets = []
        self._current_dataset = None
        self._operations = []
        return self


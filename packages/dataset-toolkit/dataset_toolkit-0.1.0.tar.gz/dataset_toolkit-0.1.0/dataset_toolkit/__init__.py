"""
Dataset Toolkit - 计算机视觉数据集处理工具包

这个工具包提供了一套完整的解决方案，用于加载、处理和导出计算机视觉数据集。

主要功能：
- 加载多种格式的数据集（YOLO、COCO等）
- 合并和转换数据集
- 导出为标准格式
- 坐标转换等工具函数

基本用法：
    >>> from dataset_toolkit import load_yolo_from_local, export_to_coco
    >>> dataset = load_yolo_from_local("/path/to/dataset", {0: 'cat'})
    >>> export_to_coco(dataset, "output.json")
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 导入核心类和函数，提供简洁的顶层API
from dataset_toolkit.models import (
    Dataset,
    ImageAnnotation,
    Annotation
)

from dataset_toolkit.loaders.local_loader import (
    load_yolo_from_local
)

from dataset_toolkit.processors.merger import (
    merge_datasets
)

from dataset_toolkit.exporters.coco_exporter import (
    export_to_coco
)

from dataset_toolkit.exporters.txt_exporter import (
    export_to_txt
)

from dataset_toolkit.utils.coords import (
    yolo_to_absolute_bbox
)

from dataset_toolkit.pipeline import (
    DatasetPipeline
)

# 定义公共API
__all__ = [
    # 版本信息
    "__version__",
    
    # 数据模型
    "Dataset",
    "ImageAnnotation",
    "Annotation",
    
    # 加载器
    "load_yolo_from_local",
    
    # 处理器
    "merge_datasets",
    
    # 导出器
    "export_to_coco",
    "export_to_txt",
    
    # 工具函数
    "yolo_to_absolute_bbox",
    
    # 管道API
    "DatasetPipeline",
]


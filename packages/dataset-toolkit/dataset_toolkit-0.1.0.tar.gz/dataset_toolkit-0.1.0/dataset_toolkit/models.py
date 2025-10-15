# dataset_toolkit/models.py
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Annotation:
    """代表一个边界框标注."""
    category_id: int
    # 存储格式为 [x_min, y_min, width, height]，单位是绝对像素值
    bbox: List[float]

@dataclass
class ImageAnnotation:
    """代表一张图片及其所有相关的标注信息."""
    image_id: str
    path: str
    width: int
    height: int
    annotations: List[Annotation] = field(default_factory=list)

@dataclass
class Dataset:
    """代表一个完整的数据集对象，作为系统内部的标准化表示."""
    name: str
    images: List[ImageAnnotation] = field(default_factory=list)
    categories: Dict[int, str] = field(default_factory=dict)
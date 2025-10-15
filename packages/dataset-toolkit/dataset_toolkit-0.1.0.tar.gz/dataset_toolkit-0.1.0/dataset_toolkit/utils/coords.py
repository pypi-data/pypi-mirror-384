# dataset_toolkit/utils/coords.py
from typing import Tuple, List

def yolo_to_absolute_bbox(yolo_bbox: Tuple[float, ...], img_width: int, img_height: int) -> List[float]:
    """
    将YOLO的相对坐标 (x_center, y_center, width, height) 转换为绝对像素坐标 (x_min, y_min, width, height)。
    """
    x_center, y_center, rel_width, rel_height = yolo_bbox
    
    abs_width = rel_width * img_width
    abs_height = rel_height * img_height
    x_min = (x_center * img_width) - (abs_width / 2)
    y_min = (y_center * img_height) - (abs_height / 2)
    
    return [x_min, y_min, abs_width, abs_height]
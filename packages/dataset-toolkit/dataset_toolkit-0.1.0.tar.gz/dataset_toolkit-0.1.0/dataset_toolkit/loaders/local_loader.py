# dataset_toolkit/loaders/local_loader.py
from pathlib import Path
from typing import Dict
from PIL import Image

# 从我们自己的包中导入模块
from dataset_toolkit.models import Dataset, ImageAnnotation, Annotation
from dataset_toolkit.utils.coords import yolo_to_absolute_bbox

def load_yolo_from_local(dataset_path: str, categories: Dict[int, str]) -> Dataset:
    """
    从本地文件系统加载YOLO格式的数据集。
    """
    root_path = Path(dataset_path)
    image_dir = root_path / 'images'
    label_dir = root_path / 'labels'
    
    if not image_dir.is_dir():
        raise FileNotFoundError(f"图片目录不存在: {image_dir}")
    if not label_dir.is_dir():
        raise FileNotFoundError(f"标注目录不存在: {label_dir}")

    dataset = Dataset(name=root_path.name, categories=categories)
    supported_extensions = ['.jpg', '.jpeg', '.png']
    
    print(f"开始加载数据集: {root_path.name}...")
    
    for image_path in image_dir.iterdir():
        if image_path.suffix.lower() not in supported_extensions:
            continue

        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
        except IOError:
            print(f"警告: 无法打开图片，已跳过: {image_path}")
            continue
        image_annotation = ImageAnnotation(
            image_id=image_path.name,
            path=str(image_path.resolve()),
            width=img_width,
            height=img_height
        )
        
        label_path = label_dir / (image_path.stem + '.txt')
        if label_path.exists():
            with open(label_path, 'r') as f:
                for line in f:
                    try:
                        parts = [float(p) for p in line.strip().split()]
                        if len(parts) != 5: continue
                        
                        cls_id, yolo_box = int(parts[0]), parts[1:]
                        abs_bbox = yolo_to_absolute_bbox(tuple(yolo_box), img_width, img_height)
                        
                        annotation = Annotation(category_id=cls_id, bbox=abs_bbox)
                        image_annotation.annotations.append(annotation)
                    except (ValueError, IndexError):
                        print(f"警告: 无法解析行，已跳过: {label_path} -> '{line.strip()}'")

        dataset.images.append(image_annotation)

    print(f"加载完成. 共找到 {len(dataset.images)} 张图片.")
    return dataset
# dataset_toolkit/exporters/coco_exporter.py
import json
import datetime
from dataset_toolkit.models import Dataset

def export_to_coco(dataset: Dataset, output_path: str):
    """
    将数据集对象导出为COCO JSON格式。

    Args:
        dataset (Dataset): 内部标准数据集对象。
        output_path (str): .json文件的输出路径。
    """
    coco_format = {
        "info": {
            "description": f"Exported from dataset_toolkit: {dataset.name}",
            "date_created": datetime.datetime.utcnow().isoformat()
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": []
    }

    # 1. 填充 categories
    for cat_id, cat_name in dataset.categories.items():
        coco_format["categories"].append({
            "id": cat_id,
            "name": cat_name,
            "supercategory": "none"
        })

    # 2. 遍历图片和标注，填充 images 和 annotations
    annotation_id_counter = 1
    for image_id_counter, image_ann in enumerate(dataset.images, 1):
        # 添加 image 条目
        coco_format["images"].append({
            "id": image_id_counter,
            "file_name": image_ann.image_id, # 使用原始文件名
            "width": image_ann.width,
            "height": image_ann.height
        })

        # 添加 annotation 条目
        for ann in image_ann.annotations:
            x_min, y_min, width, height = ann.bbox
            area = width * height
            
            coco_format["annotations"].append({
                "id": annotation_id_counter,
                "image_id": image_id_counter,
                "category_id": ann.category_id,
                "bbox": [round(c, 2) for c in ann.bbox],
                "area": round(area, 2),
                "iscrowd": 0,
                "segmentation": [] # 对于bbox，segmentation通常为空
            })
            annotation_id_counter += 1
    
    # 3. 写入JSON文件
    with open(output_path, 'w') as f:
        json.dump(coco_format, f, indent=4)
    
    print(f"成功将数据集导出为COCO格式: {output_path}")
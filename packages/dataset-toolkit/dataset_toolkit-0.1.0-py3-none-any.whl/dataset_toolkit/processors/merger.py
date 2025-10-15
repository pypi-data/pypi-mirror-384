# dataset_toolkit/processors/merger.py
import copy
from typing import List, Dict
from dataset_toolkit.models import Dataset

def merge_datasets(
    datasets: List[Dataset],
    category_mapping: Dict[str, str],
    final_categories: Dict[int, str],
    new_dataset_name: str = "merged_dataset"
) -> Dataset:
    """
    基于一个确定的最终类别体系，合并多个数据集。

    Args:
        datasets (List[Dataset]): 需要合并的数据集对象列表。
        category_mapping (Dict[str, str]): 从旧类别名到新类别名的映射规则。
            例如: {'cat': 'animal', 'dog': 'animal', 'car': 'vehicle'}
        final_categories (Dict[int, str]): 最终的、目标类别体系。
            例如: {0: 'animal', 1: 'vehicle', 2: 'bicycle'}
        new_dataset_name (str): 新合并数据集的名称。

    Returns:
        Dataset: 一个全新的、合并后的数据集对象。
    """
    if not datasets:
        return Dataset(name=new_dataset_name)

    # 1. 创建新数据集的框架，并为最终类别创建名称->ID的反向映射以便快速查找
    merged_dataset = Dataset(name=new_dataset_name, categories=final_categories)
    final_name_to_id = {name: id for id, name in final_categories.items()}

    # 2. 遍历每个待合并的数据集
    for ds in datasets:
        # 为当前数据集构建一个从 旧ID -> 最终ID 的映射表
        id_remap_table = {}
        for old_id, old_name in ds.categories.items():
            # 查找旧类别名对应的新类别名
            final_name = category_mapping.get(old_name, old_name)
            # 如果这个新类别名存在于我们最终的类别体系中，则记录ID映射关系
            if final_name in final_name_to_id:
                id_remap_table[old_id] = final_name_to_id[final_name]
        
        # 3. 遍历并处理图片和标注
        for image_ann in ds.images:
            # 深拷贝以避免修改原始数据，确保函数无副作用
            new_image_ann = copy.deepcopy(image_ann)
            
            # 基于上面生成的id_remap_table，更新标注的category_id
            updated_annotations = []
            for ann in new_image_ann.annotations:
                # 只有当一个标注的旧ID可以在重映射表中找到时，它才会被保留
                if ann.category_id in id_remap_table:
                    ann.category_id = id_remap_table[ann.category_id]
                    updated_annotations.append(ann)
            
            new_image_ann.annotations = updated_annotations
            merged_dataset.images.append(new_image_ann)

    print(f"合并完成. 新数据集 '{merged_dataset.name}' 包含 {len(merged_dataset.images)} 张图片。")
    print(f"最终类别体系: {merged_dataset.categories}")
    return merged_dataset
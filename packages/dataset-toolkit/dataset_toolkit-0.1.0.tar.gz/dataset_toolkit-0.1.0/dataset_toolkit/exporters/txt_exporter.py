# dataset_toolkit/exporters/txt_exporter.py
import os
from dataset_toolkit.models import Dataset

def export_to_txt(dataset: Dataset, output_path: str, use_relative_paths: bool = False, base_path: str = None):
    """
    将数据集导出为每行一条记录的TXT文件。
    格式: image_path class_id,x_min,y_min,x_max,y_max class_id,x_min,y_min,x_max,y_max ...

    Args:
        dataset (Dataset): 内部标准数据集对象。
        output_path (str): .txt文件的输出路径。
        use_relative_paths (bool): 是否使用相对路径。
        base_path (str): 计算相对路径时的基准目录。如果为None，则使用当前工作目录。
    """
    lines = []
    for image_ann in dataset.images:
        path = image_ann.path
        if use_relative_paths:
            try:
                path = os.path.relpath(path, start=base_path)
            except ValueError:
                # 在Windows上，如果路径在不同磁盘驱动器上，会引发ValueError
                pass # 保持绝对路径
        
        line = f"{path}"
        lines.append(line)

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
        
    print(f"成功将数据集导出为TXT格式: {output_path}")
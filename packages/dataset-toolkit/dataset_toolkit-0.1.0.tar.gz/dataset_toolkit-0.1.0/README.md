# Dataset Toolkit

一个功能强大、易于使用的 Python 工具包，用于处理计算机视觉数据集。支持多种数据格式的加载、合并、转换和导出。

## ✨ 特性

- 🔄 **多格式支持**：支持 YOLO、COCO 等常见格式
- 🔗 **数据集合并**：轻松合并多个数据集，支持类别重映射
- 📤 **灵活导出**：导出为 COCO JSON、TXT 等多种格式
- 🛠️ **工具函数**：提供坐标转换等实用工具
- 📦 **标准化数据模型**：统一的内部数据表示，方便扩展

## 📦 安装

### 从 PyPI 安装（推荐）

```bash
pip install dataset-toolkit
```

### 从源码安装

```bash
git clone https://github.com/yourusername/dataset-toolkit.git
cd dataset-toolkit
pip install -e .
```

### 开发模式安装

```bash
pip install -e ".[dev]"
```

## 🚀 快速开始

### 基本用法

```python
from dataset_toolkit import load_yolo_from_local, merge_datasets, export_to_coco

# 1. 加载 YOLO 格式数据集
dataset1 = load_yolo_from_local(
    "/path/to/dataset1",
    categories={0: 'cat', 1: 'dog'}
)

dataset2 = load_yolo_from_local(
    "/path/to/dataset2",
    categories={0: 'car', 1: 'bicycle'}
)

# 2. 合并数据集（带类别重映射）
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
    new_dataset_name="merged_dataset"
)

# 3. 导出为 COCO 格式
export_to_coco(merged, "output/merged.json")
```

### 链式 API 用法

```python
from dataset_toolkit import DatasetPipeline

# 使用管道模式处理数据集
pipeline = DatasetPipeline()
result = (pipeline
    .load_yolo("/path/to/dataset1", {0: 'cat', 1: 'dog'})
    .load_yolo("/path/to/dataset2", {0: 'car'})
    .merge(
        category_mapping={'cat': 'animal', 'dog': 'animal', 'car': 'vehicle'},
        final_categories={0: 'animal', 1: 'vehicle'}
    )
    .export_coco("output/merged.json")
    .execute())
```

## 📚 API 文档

### 数据加载器

#### `load_yolo_from_local(dataset_path, categories)`

从本地文件系统加载 YOLO 格式的数据集。

**参数：**
- `dataset_path` (str): 数据集根目录路径，应包含 `images/` 和 `labels/` 子目录
- `categories` (Dict[int, str]): 类别ID到类别名的映射

**返回：**
- `Dataset`: 标准化的数据集对象

**示例：**
```python
dataset = load_yolo_from_local(
    "/data/my_dataset",
    categories={0: 'person', 1: 'car'}
)
```

### 数据处理器

#### `merge_datasets(datasets, category_mapping, final_categories, new_dataset_name)`

合并多个数据集，支持类别重映射。

**参数：**
- `datasets` (List[Dataset]): 要合并的数据集列表
- `category_mapping` (Dict[str, str]): 旧类别名到新类别名的映射
- `final_categories` (Dict[int, str]): 最终的类别体系
- `new_dataset_name` (str, optional): 合并后数据集的名称

**返回：**
- `Dataset`: 合并后的数据集对象

### 数据导出器

#### `export_to_coco(dataset, output_path)`

导出为 COCO JSON 格式。

**参数：**
- `dataset` (Dataset): 要导出的数据集
- `output_path` (str): 输出文件路径

#### `export_to_txt(dataset, output_path, use_relative_paths, base_path)`

导出为 TXT 格式。

**参数：**
- `dataset` (Dataset): 要导出的数据集
- `output_path` (str): 输出文件路径
- `use_relative_paths` (bool, optional): 是否使用相对路径
- `base_path` (str, optional): 相对路径的基准目录

## 🏗️ 架构设计

```
dataset_toolkit/
├── models.py              # 数据模型定义
├── loaders/              # 数据加载器
│   ├── local_loader.py   # 本地文件系统加载器
│   └── remote_loader.py  # 远程数据源加载器（待开发）
├── processors/           # 数据处理器
│   ├── merger.py         # 数据集合并
│   └── filter.py         # 数据过滤（待开发）
├── exporters/            # 数据导出器
│   ├── coco_exporter.py  # COCO格式导出
│   └── txt_exporter.py   # TXT格式导出
└── utils/                # 工具函数
    └── coords.py         # 坐标转换
```

## 🔧 高级用法

### 自定义数据加载器

```python
from dataset_toolkit.models import Dataset, ImageAnnotation
from dataset_toolkit.loaders import BaseLoader

class CustomLoader(BaseLoader):
    def load(self, path, **kwargs):
        # 实现你的自定义加载逻辑
        dataset = Dataset(name="custom")
        # ... 加载数据 ...
        return dataset
```

### 批量处理

```python
from pathlib import Path
from dataset_toolkit import load_yolo_from_local, export_to_coco

# 批量处理多个数据集
dataset_dirs = [
    "/data/dataset1",
    "/data/dataset2",
    "/data/dataset3"
]

categories = {0: 'object'}

for dataset_dir in dataset_dirs:
    ds = load_yolo_from_local(dataset_dir, categories)
    output_name = Path(dataset_dir).name + ".json"
    export_to_coco(ds, f"output/{output_name}")
```

## 🧪 测试

运行测试：

```bash
pytest
```

生成测试覆盖率报告：

```bash
pytest --cov=dataset_toolkit --cov-report=html
```

## 📝 开发计划

- [ ] 支持更多数据格式（Pascal VOC、YOLO v8等）
- [ ] 添加数据增强功能
- [ ] 支持远程数据源（S3、HTTP等）
- [ ] 添加数据统计和可视化功能
- [ ] 提供命令行工具
- [ ] 支持视频数据集

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

如有问题，请通过以下方式联系：
- Email: your.email@example.com
- GitHub Issues: https://github.com/yourusername/dataset-toolkit/issues


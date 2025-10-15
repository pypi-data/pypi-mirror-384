# tests/test_loaders.py
"""
测试数据加载器
"""
import pytest
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from dataset_toolkit.loaders.local_loader import load_yolo_from_local
from dataset_toolkit.models import Dataset


class TestLocalLoader:
    """测试本地YOLO加载器"""
    
    @pytest.fixture
    def temp_dataset(self):
        """创建临时测试数据集"""
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        dataset_path = Path(temp_dir) / "test_dataset"
        images_dir = dataset_path / "images"
        labels_dir = dataset_path / "labels"
        
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)
        
        # 创建测试图片
        img = Image.new('RGB', (800, 600), 'white')
        img.save(images_dir / "test1.jpg")
        
        # 创建测试标注
        with open(labels_dir / "test1.txt", 'w') as f:
            f.write("0 0.5 0.5 0.2 0.3\n")
            f.write("1 0.3 0.4 0.1 0.2\n")
        
        yield dataset_path
        
        # 清理
        shutil.rmtree(temp_dir)
    
    def test_load_basic(self, temp_dataset):
        """测试基本加载功能"""
        categories = {0: 'cat', 1: 'dog'}
        dataset = load_yolo_from_local(str(temp_dataset), categories)
        
        assert isinstance(dataset, Dataset)
        assert len(dataset.images) == 1
        assert dataset.categories == categories
        assert len(dataset.images[0].annotations) == 2
    
    def test_load_nonexistent_path(self):
        """测试加载不存在的路径"""
        with pytest.raises(FileNotFoundError):
            load_yolo_from_local("/nonexistent/path", {0: 'test'})
    
    def test_image_dimensions(self, temp_dataset):
        """测试图片尺寸读取"""
        dataset = load_yolo_from_local(str(temp_dataset), {0: 'cat'})
        
        image = dataset.images[0]
        assert image.width == 800
        assert image.height == 600
    
    def test_bbox_conversion(self, temp_dataset):
        """测试边界框坐标转换"""
        dataset = load_yolo_from_local(str(temp_dataset), {0: 'cat'})
        
        annotation = dataset.images[0].annotations[0]
        bbox = annotation.bbox
        
        # 验证bbox格式为 [x_min, y_min, width, height]
        assert len(bbox) == 4
        assert all(isinstance(x, float) for x in bbox)
        
        # 验证坐标在合理范围内
        assert 0 <= bbox[0] <= 800  # x_min
        assert 0 <= bbox[1] <= 600  # y_min
        assert bbox[2] > 0          # width
        assert bbox[3] > 0          # height


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


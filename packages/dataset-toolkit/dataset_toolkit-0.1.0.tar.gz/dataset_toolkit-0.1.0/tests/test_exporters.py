# tests/test_exporters.py
"""
测试数据导出器
"""
import pytest
import json
import tempfile
from pathlib import Path

from dataset_toolkit.models import Dataset, ImageAnnotation, Annotation
from dataset_toolkit.exporters.coco_exporter import export_to_coco
from dataset_toolkit.exporters.txt_exporter import export_to_txt


class TestCocoExporter:
    """测试COCO格式导出"""
    
    @pytest.fixture
    def sample_dataset(self):
        """创建示例数据集"""
        dataset = Dataset(name="test", categories={0: 'cat', 1: 'dog'})
        
        img = ImageAnnotation(
            image_id="test.jpg",
            path="/path/to/test.jpg",
            width=800,
            height=600,
            annotations=[
                Annotation(category_id=0, bbox=[100, 100, 50, 50]),
                Annotation(category_id=1, bbox=[200, 200, 60, 60])
            ]
        )
        dataset.images.append(img)
        
        return dataset
    
    def test_export_coco_basic(self, sample_dataset):
        """测试基本COCO导出"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            export_to_coco(sample_dataset, output_path)
            
            # 验证文件存在
            assert Path(output_path).exists()
            
            # 读取并验证JSON结构
            with open(output_path, 'r') as f:
                coco_data = json.load(f)
            
            assert 'images' in coco_data
            assert 'annotations' in coco_data
            assert 'categories' in coco_data
            assert len(coco_data['images']) == 1
            assert len(coco_data['annotations']) == 2
            assert len(coco_data['categories']) == 2
        
        finally:
            Path(output_path).unlink()
    
    def test_coco_format_structure(self, sample_dataset):
        """测试COCO格式结构"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            export_to_coco(sample_dataset, output_path)
            
            with open(output_path, 'r') as f:
                coco_data = json.load(f)
            
            # 验证categories格式
            cat = coco_data['categories'][0]
            assert 'id' in cat
            assert 'name' in cat
            
            # 验证images格式
            img = coco_data['images'][0]
            assert 'id' in img
            assert 'file_name' in img
            assert 'width' in img
            assert 'height' in img
            
            # 验证annotations格式
            ann = coco_data['annotations'][0]
            assert 'id' in ann
            assert 'image_id' in ann
            assert 'category_id' in ann
            assert 'bbox' in ann
            assert 'area' in ann
            assert len(ann['bbox']) == 4
        
        finally:
            Path(output_path).unlink()


class TestTxtExporter:
    """测试TXT格式导出"""
    
    @pytest.fixture
    def sample_dataset(self):
        """创建示例数据集"""
        dataset = Dataset(name="test", categories={0: 'cat'})
        
        for i in range(3):
            img = ImageAnnotation(
                image_id=f"test{i}.jpg",
                path=f"/path/to/test{i}.jpg",
                width=800,
                height=600,
                annotations=[Annotation(category_id=0, bbox=[100, 100, 50, 50])]
            )
            dataset.images.append(img)
        
        return dataset
    
    def test_export_txt_basic(self, sample_dataset):
        """测试基本TXT导出"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_path = f.name
        
        try:
            export_to_txt(sample_dataset, output_path)
            
            # 验证文件存在
            assert Path(output_path).exists()
            
            # 读取并验证内容
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3  # 3张图片
        
        finally:
            Path(output_path).unlink()
    
    def test_txt_line_format(self, sample_dataset):
        """测试TXT行格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_path = f.name
        
        try:
            export_to_txt(sample_dataset, output_path)
            
            with open(output_path, 'r') as f:
                lines = [line.strip() for line in f.readlines()]
            
            # 每行应该是一个路径
            for line in lines:
                assert line.startswith('/path/to/test')
                assert line.endswith('.jpg')
        
        finally:
            Path(output_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


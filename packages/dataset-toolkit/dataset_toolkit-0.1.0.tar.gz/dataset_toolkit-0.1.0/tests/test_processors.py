# tests/test_processors.py
"""
测试数据处理器
"""
import pytest
from dataset_toolkit.models import Dataset, ImageAnnotation, Annotation
from dataset_toolkit.processors.merger import merge_datasets


class TestMerger:
    """测试数据集合并功能"""
    
    @pytest.fixture
    def sample_datasets(self):
        """创建示例数据集"""
        # 数据集1: 动物
        ds1 = Dataset(name="animals", categories={0: 'cat', 1: 'dog'})
        img1 = ImageAnnotation(
            image_id="img1.jpg",
            path="/path/to/img1.jpg",
            width=800,
            height=600,
            annotations=[
                Annotation(category_id=0, bbox=[100, 100, 50, 50]),
                Annotation(category_id=1, bbox=[200, 200, 60, 60])
            ]
        )
        ds1.images.append(img1)
        
        # 数据集2: 交通工具
        ds2 = Dataset(name="vehicles", categories={0: 'car', 1: 'bicycle'})
        img2 = ImageAnnotation(
            image_id="img2.jpg",
            path="/path/to/img2.jpg",
            width=1024,
            height=768,
            annotations=[
                Annotation(category_id=0, bbox=[150, 150, 80, 80])
            ]
        )
        ds2.images.append(img2)
        
        return ds1, ds2
    
    def test_merge_basic(self, sample_datasets):
        """测试基本合并功能"""
        ds1, ds2 = sample_datasets
        
        final_categories = {0: 'animal', 1: 'vehicle'}
        category_mapping = {
            'cat': 'animal',
            'dog': 'animal',
            'car': 'vehicle',
            'bicycle': 'vehicle'
        }
        
        merged = merge_datasets(
            datasets=[ds1, ds2],
            category_mapping=category_mapping,
            final_categories=final_categories
        )
        
        assert len(merged.images) == 2
        assert merged.categories == final_categories
    
    def test_category_remapping(self, sample_datasets):
        """测试类别重映射"""
        ds1, ds2 = sample_datasets
        
        final_categories = {0: 'animal', 1: 'vehicle'}
        category_mapping = {
            'cat': 'animal',
            'dog': 'animal',
            'car': 'vehicle',
            'bicycle': 'vehicle'
        }
        
        merged = merge_datasets(
            datasets=[ds1, ds2],
            category_mapping=category_mapping,
            final_categories=final_categories
        )
        
        # 检查第一张图片的标注是否都映射到 'animal' (id=0)
        for ann in merged.images[0].annotations:
            assert ann.category_id == 0
        
        # 检查第二张图片的标注是否映射到 'vehicle' (id=1)
        assert merged.images[1].annotations[0].category_id == 1
    
    def test_merge_empty_datasets(self):
        """测试合并空数据集列表"""
        merged = merge_datasets(
            datasets=[],
            category_mapping={},
            final_categories={}
        )
        
        assert len(merged.images) == 0
        assert len(merged.categories) == 0
    
    def test_annotation_count_preservation(self, sample_datasets):
        """测试标注数量保持"""
        ds1, ds2 = sample_datasets
        
        original_ann_count = sum(
            len(img.annotations) 
            for ds in [ds1, ds2] 
            for img in ds.images
        )
        
        final_categories = {0: 'animal', 1: 'vehicle'}
        category_mapping = {
            'cat': 'animal',
            'dog': 'animal',
            'car': 'vehicle'
        }
        
        merged = merge_datasets(
            datasets=[ds1, ds2],
            category_mapping=category_mapping,
            final_categories=final_categories
        )
        
        merged_ann_count = sum(
            len(img.annotations) 
            for img in merged.images
        )
        
        assert merged_ann_count == original_ann_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


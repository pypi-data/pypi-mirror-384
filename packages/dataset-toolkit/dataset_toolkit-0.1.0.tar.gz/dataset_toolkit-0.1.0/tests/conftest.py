# tests/conftest.py
"""
pytest配置文件和共享fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image


@pytest.fixture(scope="session")
def temp_workspace():
    """创建临时工作空间"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def create_test_image():
    """工厂fixture：创建测试图片"""
    def _create(path: Path, width: int = 800, height: int = 600, color: str = 'white'):
        img = Image.new('RGB', (width, height), color)
        img.save(path)
        return path
    
    return _create


@pytest.fixture
def create_yolo_label():
    """工厂fixture：创建YOLO标注文件"""
    def _create(path: Path, annotations: list):
        """
        annotations: list of (class_id, x_center, y_center, width, height)
        """
        with open(path, 'w') as f:
            for ann in annotations:
                f.write(f"{ann[0]} {ann[1]} {ann[2]} {ann[3]} {ann[4]}\n")
        return path
    
    return _create


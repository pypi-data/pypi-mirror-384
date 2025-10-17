import os
import tempfile
import shutil
from xl_docx.mixins.component import ComponentMixin


def test_component_slot():
    """测试组件slot功能"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 在临时目录中创建xl-haha.xml文件
        xl_haha_file = os.path.join(temp_dir, 'xl-haha.xml')
        with open(xl_haha_file, 'w', encoding='utf-8') as f:
            f.write('<xl-p style="{{ style }}">{{ content }},<slot/></xl-p>')
        
        # 创建ComponentMixin实例，使用临时目录作为外置组件目录
        processor = ComponentMixin(external_components_dir=temp_dir)
        
        # 测试XML模板
        test_xml = '<xl-haha style="align:center" content="haha">123</xl-haha>'
        
        # 只使用ComponentMixin编译
        compiled = processor.process_components(test_xml)
        
        # 验证结果
        expected = '<xl-p style="align:center">haha,123</xl-p>'
        assert compiled.strip() == expected, f"期望结果: {expected}, 实际结果: {compiled.strip()}"
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_slot_without_attributes():
    """测试没有属性的slot功能"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 在临时目录中创建xl-haha.xml文件
        xl_haha_file = os.path.join(temp_dir, 'xl-haha.xml')
        with open(xl_haha_file, 'w', encoding='utf-8') as f:
            f.write('<xl-p style="{{ style }}">{{ content }},<slot/></xl-p>')
        
        # 创建ComponentMixin实例，使用临时目录作为外置组件目录
        processor = ComponentMixin(external_components_dir=temp_dir)
        
        test_xml = '<xl-haha>test content</xl-haha>'
        compiled = processor.process_components(test_xml)
        
        # 由于找到了xl-haha组件模板，会进行替换，但没有提供content属性，{{content}}被替换为空字符串
        expected = '<xl-p>,test content</xl-p>'
        assert compiled.strip() == expected, f"期望结果: {expected}, 实际结果: {compiled.strip()}"
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_slot_with_style_only():
    """测试只有style属性的slot功能"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 在临时目录中创建xl-haha.xml文件
        xl_haha_file = os.path.join(temp_dir, 'xl-haha.xml')
        with open(xl_haha_file, 'w', encoding='utf-8') as f:
            f.write('<xl-p style="{{ style }}">{{ content }},<slot/></xl-p>')
        
        # 创建ComponentMixin实例，使用临时目录作为外置组件目录
        processor = ComponentMixin(external_components_dir=temp_dir)
        
        test_xml = '<xl-haha style="color:red">test content</xl-haha>'
        compiled = processor.process_components(test_xml)
        
        # 由于找到了xl-haha组件模板，会进行替换，但没有提供content属性
        expected = '<xl-p style="color:red">,test content</xl-p>'
        assert compiled.strip() == expected
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_slot_nested_content():
    """测试嵌套内容的slot功能"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 在临时目录中创建xl-haha.xml文件
        xl_haha_file = os.path.join(temp_dir, 'xl-haha.xml')
        with open(xl_haha_file, 'w', encoding='utf-8') as f:
            f.write('<xl-p style="{{ style }}">{{ content }},<slot/></xl-p>')
        
        # 创建ComponentMixin实例，使用临时目录作为外置组件目录
        processor = ComponentMixin(external_components_dir=temp_dir)
        
        test_xml = '<xl-haha style="align:center" content="haha"><span>nested</span> content</xl-haha>'
        compiled = processor.process_components(test_xml)
        
        # 验证结果
        expected = '<xl-p style="align:center">haha,<span>nested</span> content</xl-p>'
        assert compiled.strip() == expected, f"期望结果: {expected}, 实际结果: {compiled.strip()}"
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

import os
import tempfile
from xl_docx.compiler.processors.slot import SlotProcessor


def test_basic_slot():
    """Test basic slot functionality"""
    # 创建临时目录和slot文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建 xl-for.xml 文件
        slot_file = os.path.join(temp_dir, 'xl-for.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('($ for index in range(2) $)<slot/>($ endfor $)')
        
        # 创建处理器
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试基本slot功能
        xml = '<xl-for><xl-p>123</xl-p></xl-for>'
        result = processor.compile(xml)
        expected = '($ for index in range(2) $)<xl-p>123</xl-p>($ endfor $)'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_slot_with_attributes():
    """Test slot with attributes"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建带属性的slot文件
        slot_file = os.path.join(temp_dir, 'xl-repeat.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('($ for {{var}} in range({{count}}) $)<slot/>($ endfor $)')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试带属性的slot
        xml = '<xl-repeat var="item" count="3"><xl-p>Hello</xl-p></xl-repeat>'
        result = processor.compile(xml)
        expected = '($ for item in range(3) $)<xl-p>Hello</xl-p>($ endfor $)'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_slot_with_style_attribute():
    """Test slot with style attribute"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建带style属性的slot文件
        slot_file = os.path.join(temp_dir, 'xl-container.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('<div style="{{style}}"><slot/></div>')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试带style的slot
        xml = '<xl-container style="color: red"><xl-p>Content</xl-p></xl-container>'
        result = processor.compile(xml)
        expected = '<div style="color: red"><xl-p>Content</xl-p></div>'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_slot_without_style_attribute():
    """Test slot without style attribute"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建带style属性的slot文件
        slot_file = os.path.join(temp_dir, 'xl-container.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('<div style="{{style}}"><slot/></div>')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试不带style的slot
        xml = '<xl-container><xl-p>Content</xl-p></xl-container>'
        result = processor.compile(xml)
        expected = '<div><xl-p>Content</xl-p></div>'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_multiple_slots():
    """Test multiple slots in one XML"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建多个slot文件
        for_file = os.path.join(temp_dir, 'xl-for.xml')
        with open(for_file, 'w', encoding='utf-8') as f:
            f.write('($ for index in range(2) $)<slot/>($ endfor $)')
        
        container_file = os.path.join(temp_dir, 'xl-container.xml')
        with open(container_file, 'w', encoding='utf-8') as f:
            f.write('<div><slot/></div>')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试多个slot
        xml = '''<xl-for><xl-container><xl-p>123</xl-p></xl-container></xl-for>'''
        result = processor.compile(xml)
        expected = '($ for index in range(2) $)<div><xl-p>123</xl-p></div>($ endfor $)'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_slot_not_found():
    """Test slot that doesn't exist"""
    with tempfile.TemporaryDirectory() as temp_dir:
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试不存在的slot
        xml = '<xl-unknown><xl-p>123</xl-p></xl-unknown>'
        result = processor.compile(xml)
        # 应该返回原始XML
        assert result == xml, f"Expected: {xml}, Got: {result}"


def test_empty_slot_content():
    """Test slot with empty content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        slot_file = os.path.join(temp_dir, 'xl-for.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('($ for index in range(2) $)<slot/>($ endfor $)')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试空内容的slot
        xml = '<xl-for></xl-for>'
        result = processor.compile(xml)
        expected = '($ for index in range(2) $)($ endfor $)'
        assert result == expected, f"Expected: {expected}, Got: {result}"


def test_slot_with_nested_content():
    """Test slot with nested XML content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        slot_file = os.path.join(temp_dir, 'xl-wrapper.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('<div class="wrapper"><slot/></div>')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 测试嵌套内容的slot
        xml = '''<xl-wrapper><xl-p>Hello <strong>World</strong></xl-p></xl-wrapper>'''
        result = processor.compile(xml)
        expected = '<div class="wrapper"><xl-p>Hello <strong>World</strong></xl-p></div>'
        assert result == expected, f"Expected: {expected}, Got: {result}"

def test_new():
    with tempfile.TemporaryDirectory() as temp_dir:
        slot_file = os.path.join(temp_dir, 'xl-page.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('<xl-page><slot/></xl-page>')
        
        processor = SlotProcessor(external_slots_dir=temp_dir)


        xml = '''
        <xl-page w:rsidR="00DF733E">
    <w:headerReference r:id="rId166" w:type="default"/>
    <w:pgSz w:h="15840" w:w="12240"/>
    <w:pgMar w:bottom="1440" w:footer="720" w:gutter="0" w:header="720" w:left="1440" w:right="1440" w:top="1440"/>
    <w:cols w:space="720"/>
    <w:docGrid w:linePitch="360"/>
    </xl-page>'''
    result = processor.compile(xml)
    print('result~~~~~~~~~~~~~~~~~~~~')
    print(result)
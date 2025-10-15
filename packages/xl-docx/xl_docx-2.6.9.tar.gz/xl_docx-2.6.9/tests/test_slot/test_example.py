"""
Slot Processor 使用示例
演示如何使用 SlotProcessor 处理 slot 标签
"""
import os
import sys
import tempfile

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from xl_docx.compiler.processors.slot import SlotProcessor


def test_xl_for_example():
    """演示 xl-for slot 的使用"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建 xl-for.xml 文件
        slot_file = os.path.join(temp_dir, 'xl-for.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('($ for index in range(2) $)<slot/>($ endfor $)')
        
        # 创建处理器
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 使用示例
        xml = '<xl-for><xl-p>123</xl-p></xl-for>'
        result = processor.compile(xml)
        expected = '($ for index in range(2) $)<xl-p>123</xl-p>($ endfor $)'
        
        print(f"Input: {xml}")
        print(f"Output: {result}")
        print(f"Expected: {expected}")
        assert result == expected


def test_nested_slots_example():
    """演示嵌套 slot 的使用"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建多个 slot 文件
        for_file = os.path.join(temp_dir, 'xl-for.xml')
        with open(for_file, 'w', encoding='utf-8') as f:
            f.write('($ for index in range(2) $)<slot/>($ endfor $)')
        
        container_file = os.path.join(temp_dir, 'xl-container.xml')
        with open(container_file, 'w', encoding='utf-8') as f:
            f.write('<div class="item"><slot/></div>')
        
        # 创建处理器
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 使用嵌套 slot
        xml = '<xl-for><xl-container><xl-p>Hello World</xl-p></xl-container></xl-for>'
        result = processor.compile(xml)
        expected = '($ for index in range(2) $)<div class="item"><xl-p>Hello World</xl-p></div>($ endfor $)'
        
        print(f"\nNested slot example:")
        print(f"Input: {xml}")
        print(f"Output: {result}")
        print(f"Expected: {expected}")
        assert result == expected


def test_slot_with_attributes_example():
    """演示带属性的 slot 使用"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建带变量的 slot 文件
        slot_file = os.path.join(temp_dir, 'xl-repeat.xml')
        with open(slot_file, 'w', encoding='utf-8') as f:
            f.write('($ for {{var}} in range({{count}}) $)<slot/>($ endfor $)')
        
        # 创建处理器
        processor = SlotProcessor(external_slots_dir=temp_dir)
        
        # 使用带属性的 slot
        xml = '<xl-repeat var="item" count="3"><xl-p>Item {{item}}</xl-p></xl-repeat>'
        result = processor.compile(xml)
        expected = '($ for item in range(3) $)<xl-p>Item {{item}}</xl-p>($ endfor $)'
        
        print(f"\nSlot with attributes example:")
        print(f"Input: {xml}")
        print(f"Output: {result}")
        print(f"Expected: {expected}")
        assert result == expected


if __name__ == "__main__":
    print("Slot Processor Usage Examples")
    print("=" * 50)
    
    test_xl_for_example()
    test_nested_slots_example()
    test_slot_with_attributes_example()
    
    print("\nAll examples ran successfully!")

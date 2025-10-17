#!/usr/bin/env python3
"""
测试XMLCompiler与ComponentProcessor的集成
"""

import sys
import os
import tempfile
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xl_docx.compiler import XMLCompiler


def test_compiler_with_external_components():
    """测试XMLCompiler使用外置组件目录"""
    print("=== Testing XMLCompiler with External Components ===")
    
    # 创建临时外置组件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建外置组件文件
        components = {
            'my-button.xml': '<button type="{{type}}" class="{{class}}">{{label}}</button>',
            'ui-card.xml': '''
<div class="card">
    <h3>{{title}}</h3>
    <p>{{content}}</p>
</div>
            '''.strip()
        }
        
        for filename, content in components.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 创建XMLCompiler实例，传入外置组件目录
        compiler = XMLCompiler(external_components_dir=temp_dir)
        
        # 测试模板
        template = '''
        <document>
            <my-button type="primary" class="btn-large" label="Submit"/>
            <ui-card title="Welcome" content="This is a test card"/>
            <xl-text data="Builtin component"/>
        </document>
        '''
        
        print("Original template:")
        print(template)
        
        # 编译模板
        compiled_template = compiler.compile_template(template)
        
        print("\nCompiled template:")
        print(compiled_template)
        
        # 验证编译结果 - 注意其他processor也会处理结果
        expected_results = [
            '<button type="primary" class="btn-large">Submit</button>',
            '<div class="card">',
            'Builtin component'  # 被ParagraphProcessor处理后的结果
        ]
        
        all_found = all(result in compiled_template for result in expected_results)
        
        if all_found:
            print("\n[SUCCESS] XMLCompiler with external components test passed")
            return True
        else:
            print("\n[FAILED] XMLCompiler with external components test failed")
            return False


def test_compiler_without_external_components():
    """测试XMLCompiler不使用外置组件目录"""
    print("\n=== Testing XMLCompiler without External Components ===")
    
    # 创建XMLCompiler实例，不传入外置组件目录
    compiler = XMLCompiler()
    
    # 测试模板
    template = '''
    <document>
        <xl-text data="Builtin component only"/>
    </document>
    '''
    
    print("Original template:")
    print(template)
    
    # 编译模板
    compiled_template = compiler.compile_template(template)
    
    print("\nCompiled template:")
    print(compiled_template)
    
    # 验证编译结果 - 被ParagraphProcessor处理后的结果
    if "Builtin component only" in compiled_template:
        print("\n[SUCCESS] XMLCompiler without external components test passed")
        return True
    else:
        print("\n[FAILED] XMLCompiler without external components test failed")
        return False


def test_compiler_render_with_external_components():
    """测试XMLCompiler渲染功能与外置组件"""
    print("\n=== Testing XMLCompiler Render with External Components ===")
    
    # 创建临时外置组件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建外置组件文件
        components = {
            'my-header.xml': '<h1>{{title}}</h1>',
            'my-button.xml': '<button onclick="{{action}}">{{label}}</button>'
        }
        
        for filename, content in components.items():
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 创建XMLCompiler实例
        compiler = XMLCompiler(external_components_dir=temp_dir)
        
        # 测试模板
        template = '''
        <document>
            <my-header title="{{page_title}}"/>
            <my-button action="{{button_action}}" label="{{button_text}}"/>
        </document>
        '''
        
        # 渲染数据
        data = {
            'page_title': 'My Page',
            'button_action': 'submit()',
            'button_text': 'Submit Form'
        }
        
        print("Template:")
        print(template)
        print("\nData:")
        print(data)
        
        # 渲染模板
        result = compiler.render_template(template, data)
        
        print("\nRendered result:")
        print(result)
        
        # 验证渲染结果
        expected_results = [
            '<h1>My Page</h1>',
            '<button onclick="submit()">Submit Form</button>'
        ]
        
        all_found = all(expected in result for expected in expected_results)
        
        if all_found:
            print("\n[SUCCESS] XMLCompiler render with external components test passed")
            return True
        else:
            print("\n[FAILED] XMLCompiler render with external components test failed")
            return False


def test_compiler_processor_order():
    """测试处理器执行顺序"""
    print("\n=== Testing Processor Execution Order ===")
    
    # 创建XMLCompiler实例
    compiler = XMLCompiler()
    
    # 验证ComponentProcessor在第一位
    first_processor = compiler.processors[0]
    processor_name = first_processor.__class__.__name__
    
    if processor_name == 'ComponentProcessor':
        print(f"[SUCCESS] ComponentProcessor is first: {processor_name}")
        return True
    else:
        print(f"[FAILED] ComponentProcessor is not first: {processor_name}")
        return False


if __name__ == "__main__":
    print("Starting XMLCompiler Integration Tests...\n")
    
    results = []
    results.append(test_compiler_with_external_components())
    results.append(test_compiler_without_external_components())
    results.append(test_compiler_render_with_external_components())
    results.append(test_compiler_processor_order())
    
    print(f"\nTest results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("[SUCCESS] All XMLCompiler integration tests passed!")
    else:
        print("[FAILED] Some XMLCompiler integration tests failed!")

#!/usr/bin/env python3
"""
XMLCompiler使用示例 - 展示外置组件目录功能
"""

import sys
import os
import tempfile
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from xl_docx.compiler import XMLCompiler


def create_sample_components():
    """创建示例组件文件"""
    temp_dir = tempfile.mkdtemp()
    
    # 创建各种组件
    components = {
        'my-header.xml': '<h1 style="color: blue;">{{title}}</h1>',
        'my-button.xml': '<button type="{{type}}" class="btn">{{label}}</button>',
        'ui-card.xml': '''
<div class="card" style="border: 1px solid #ccc; padding: 10px;">
    <h3>{{title}}</h3>
    <p>{{content}}</p>
</div>
        '''.strip(),
        'xl-custom.xml': '<xl-p style="font-weight: bold;">Custom: {{data}}</xl-p>'
    }
    
    for filename, content in components.items():
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return temp_dir


def demo_basic_usage():
    """演示基本使用"""
    print("=== Basic XMLCompiler Usage ===")
    
    # 不使用外置组件目录
    compiler = XMLCompiler()
    
    template = '''
    <document>
        <xl-text data="Hello from builtin component"/>
    </document>
    '''
    
    result = compiler.compile_template(template)
    print("Without external components:")
    print(result)
    print()


def demo_with_external_components():
    """演示使用外置组件目录"""
    print("=== XMLCompiler with External Components ===")
    
    # 创建示例组件
    components_dir = create_sample_components()
    
    try:
        # 使用外置组件目录
        compiler = XMLCompiler(external_components_dir=components_dir)
        
        template = '''
        <document>
            <my-header title="My Application"/>
            <my-button type="submit" label="Save"/>
            <ui-card title="Welcome" content="This is a demo"/>
            <xl-custom data="Custom component"/>
            <xl-text data="Builtin component"/>
        </document>
        '''
        
        print("Template:")
        print(template)
        print("\nCompiled result:")
        result = compiler.compile_template(template)
        print(result)
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(components_dir, ignore_errors=True)


def demo_render_with_data():
    """演示渲染功能"""
    print("\n=== XMLCompiler Render with Data ===")
    
    # 创建示例组件
    components_dir = create_sample_components()
    
    try:
        # 使用外置组件目录
        compiler = XMLCompiler(external_components_dir=components_dir)
        
        template = '''
        <document>
            <my-header title="{{page_title}}"/>
            <my-button type="{{button_type}}" label="{{button_text}}"/>
            <ui-card title="{{card_title}}" content="{{card_content}}"/>
        </document>
        '''
        
        data = {
            'page_title': 'My Dashboard',
            'button_type': 'primary',
            'button_text': 'Get Started',
            'card_title': 'Welcome',
            'card_content': 'This is your personalized dashboard.'
        }
        
        print("Template:")
        print(template)
        print("\nData:")
        print(data)
        print("\nRendered result:")
        result = compiler.render_template(template, data)
        print(result)
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(components_dir, ignore_errors=True)


if __name__ == "__main__":
    print("XMLCompiler Usage Examples\n")
    
    demo_basic_usage()
    demo_with_external_components()
    demo_render_with_data()
    
    print("\n[SUCCESS] All examples completed!")

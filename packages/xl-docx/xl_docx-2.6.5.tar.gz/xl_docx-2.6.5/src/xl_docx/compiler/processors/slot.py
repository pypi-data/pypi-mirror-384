import os
import re
from xl_docx.compiler.processors.base import BaseProcessor


class SlotProcessor(BaseProcessor):
    """处理slot标签的XML处理器"""
    
    # slot标签匹配模式 - 支持开始和结束标签
    SLOT_PATTERN = r'''
        <([a-zA-Z][a-zA-Z0-9-]*)            # slot名称
        ([^>]*)                              # 属性
        \s*>                                 # 开始标签
        (.*?)                                # 内容（非贪婪匹配）
        </\1>                                # 结束标签
    '''
    
    def __init__(self, external_slots_dir=None):
        # slot缓存，避免重复读取文件
        self._slot_cache = {}
        # 获取内置slots目录路径
        self._builtin_slots_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'slots'
        )
        # 外置slot目录
        self._external_slots_dir = external_slots_dir
    
    def compile(self, xml: str) -> str:
        """编译XML，处理slot标签"""
        return self._process_slots(xml)
    
    def _process_slots(self, xml: str) -> str:
        """处理所有slot标签，支持递归处理嵌套slot"""
        def process_slot(match):
            slot_name, attrs_str, content = match.groups()
            # 提取属性
            attrs = self._parse_attrs(attrs_str)
            # 获取slot模板
            slot_template = self._get_slot_template(slot_name)
            if slot_template:
                # 递归处理内容中的嵌套slot
                processed_content = self._process_slots(content)
                # 渲染slot
                return self._render_slot(slot_template, processed_content, attrs)
            else:
                # 如果找不到slot，递归处理内容后返回原始标签
                processed_content = self._process_slots(content)
                return f'<{slot_name}{attrs_str}>{processed_content}</{slot_name}>'
        
        # 持续处理直到没有更多的slot标签
        prev_xml = None
        while prev_xml != xml:
            prev_xml = xml
            xml = re.sub(self.SLOT_PATTERN, process_slot, xml, flags=re.VERBOSE | re.DOTALL)
        
        return xml
    
    def _get_slot_template(self, slot_name: str) -> str:
        """获取slot模板内容，优先从外置目录查找，然后从内置目录查找"""
        if slot_name in self._slot_cache:
            return self._slot_cache[slot_name]
        
        # 首先尝试从外置slot目录查找
        if self._external_slots_dir:
            external_file = os.path.join(self._external_slots_dir, f'{slot_name}.xml')
            if os.path.exists(external_file):
                try:
                    with open(external_file, 'r', encoding='utf-8') as f:
                        template = f.read()
                        self._slot_cache[slot_name] = template
                        return template
                except (FileNotFoundError, IOError):
                    pass
        
        # 然后尝试从内置slot目录查找
        builtin_file = os.path.join(self._builtin_slots_dir, f'{slot_name}.xml')
        try:
            with open(builtin_file, 'r', encoding='utf-8') as f:
                template = f.read()
                self._slot_cache[slot_name] = template
                return template
        except FileNotFoundError:
            # slot文件不存在，缓存空字符串避免重复尝试
            self._slot_cache[slot_name] = ''
            return ''
    
    def _parse_attrs(self, attrs_str: str) -> dict:
        """解析属性字符串为字典"""
        attrs = {}
        if not attrs_str.strip():
            return attrs
        
        # 使用正则表达式匹配属性
        attr_pattern = r'(\w+)="([^"]*)"'
        for match in re.finditer(attr_pattern, attrs_str):
            key, value = match.groups()
            attrs[key] = value
        
        return attrs
    
    def _render_slot(self, template: str, content: str, attrs: dict) -> str:
        """渲染slot模板，替换slot标签和变量"""
        result = template
        
        # 替换 <slot/> 标签为实际内容
        result = re.sub(r'<slot\s*/>', content, result)
        
        # 替换模板中的变量
        for key, value in attrs.items():
            # 替换 {{key}} 格式的变量，支持空格
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            result = re.sub(pattern, value, result)
        
        # 处理未替换的模板变量（没有提供对应属性的变量）
        # 对于 style 属性，如果没有提供，移除整个 style 属性
        if 'style' not in attrs:
            # 移除 style="{{style}}" 等格式
            result = re.sub(r'\s*style\s*=\s*"\{\{\s*style\s*\}\}"', '', result)
        
        # 对于其他未替换的变量，保留它们（不移除）
        # result = re.sub(r'\{\{\s*\w+\s*\}\}', '', result)
        
        # 清理空的 style 属性
        result = re.sub(r'\s*style\s*=\s*""\s*', '', result)
        
        return result
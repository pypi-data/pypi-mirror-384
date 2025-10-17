import os
import re


class ComponentProcessor:
    """处理组件标签的XML处理器，支持自闭合标签和开始/结束标签"""
    
    # 自闭合组件标签匹配模式
    COMPONENT_PATTERN = r'''
        <([a-zA-Z][a-zA-Z0-9-]*)            # 组件名（完整名称）
        ([^>]*)                              # 属性
        \s*/?>                               # 自闭合标签
    '''
    
    # 开始和结束标签匹配模式 - 支持slot功能
    SLOT_PATTERN = r'''
        <([a-zA-Z][a-zA-Z0-9-]*)            # 组件名称
        ((?:\s+[^=]+="[^"]*")*)              # 属性（支持引号内的>字符）
        \s*>                                 # 开始标签
        (.*?)                                # 内容（非贪婪匹配）
        </\1>                                # 结束标签
    '''
    
    def __init__(self, external_components_dir=None):
        # 组件缓存，避免重复读取文件
        self._component_cache = {}
        # 获取内置components目录路径
        self._builtin_components_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'components'
        )
        # 外置组件目录
        self._external_components_dir = external_components_dir
        # 初始化时一次性加载所有组件
        self._load_all_components()
    
    def _load_all_components(self):
        """一次性加载所有组件到缓存中"""
        self._load_builtin_components()
        self._load_external_components()
    
    def _load_builtin_components(self):
        """加载内置组件目录中的所有组件"""
        if os.path.exists(self._builtin_components_dir):
            self._load_components_from_dir(self._builtin_components_dir, overwrite=False)
    
    def _load_external_components(self):
        """加载外置组件目录中的所有组件"""
        if self._external_components_dir and os.path.exists(self._external_components_dir):
            self._load_components_from_dir(self._external_components_dir, overwrite=True)
    
    def _load_components_from_dir(self, components_dir, overwrite=True):
        """从指定目录加载组件
        
        Args:
            components_dir: 组件目录路径
            overwrite: 是否覆盖已存在的组件（True=覆盖，False=跳过已存在的）
        """
        for filename in os.listdir(components_dir):
            if filename.endswith('.xml'):
                component_name = filename[:-4]  # 移除.xml扩展名
                # 如果设置了不覆盖且组件已存在，则跳过
                if not overwrite and component_name in self._component_cache:
                    continue
                    
                filepath = os.path.join(components_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template = f.read()
                        self._component_cache[component_name] = template
                except (FileNotFoundError, IOError):
                    pass
        
    
    def compile(self, xml: str) -> str:
        """编译XML，处理组件标签（支持自闭合和开始/结束标签）"""
        # 先处理开始/结束标签（slot功能）
        xml = self._process_slots(xml)
        # 再处理自闭合标签
        xml = self._process_components(xml)
        return xml
    
    def _process_slots(self, xml: str) -> str:
        """处理所有开始/结束标签，支持递归处理嵌套slot"""
        def process_slot(match):
            component_name, attrs_str, content = match.groups()
            # 提取属性
            attrs = self._parse_attrs(attrs_str)
            # 获取组件模板
            component_template = self._get_component_template(component_name)
            if component_template:
                # 递归处理内容中的嵌套slot
                processed_content = self._process_slots(content)
                # 渲染组件
                return self._render_slot(component_template, processed_content, attrs)
            else:
                # 如果找不到组件，递归处理内容后返回原始标签
                processed_content = self._process_slots(content)
                return f'<{component_name}{attrs_str}>{processed_content}</{component_name}>'
        
        # 持续处理直到没有更多的slot标签
        prev_xml = None
        while prev_xml != xml:
            prev_xml = xml
            xml = re.sub(self.SLOT_PATTERN, process_slot, xml, flags=re.VERBOSE | re.DOTALL)
        
        return xml
    
    def _process_components(self, xml: str) -> str:
        """处理所有自闭合组件标签"""
        def process_component(match):
            component_name, attrs_str = match.groups()
            # 提取属性
            attrs = self._parse_attrs(attrs_str)
            # 获取组件模板
            component_template = self._get_component_template(component_name)
            if component_template:
                # 渲染组件
                return self._render_component(component_template, attrs)
            else:
                # 如果找不到组件，返回原始标签
                return match.group(0)
        
        return re.sub(self.COMPONENT_PATTERN, process_component, xml, flags=re.VERBOSE)
    
    def _get_component_template(self, component_name: str) -> str:
        """获取组件模板内容，从已加载的缓存中查找"""
        return self._component_cache.get(component_name, '')
    
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
        
        # 对于其他未替换的变量，替换为空字符串
        result = re.sub(r'\{\{\s*\w+\s*\}\}', '', result)
        
        # 清理空的 style 属性
        result = re.sub(r'\s*style\s*=\s*""\s*', '', result)
        
        # 清理多余的空白字符，但保留必要的结构
        # 只清理模板内部的换行符，保留slot内容的结构
        result = re.sub(r'\n\s*', '', result)     # 移除换行符及其后的空白
        result = re.sub(r'\s+', ' ', result)      # 将多个连续空白字符替换为单个空格
        result = result.strip()                   # 移除首尾空白
        
        return result
    
    def _render_component(self, template: str, attrs: dict) -> str:
        """渲染组件模板，替换变量"""
        result = template
        
        # 替换模板中的变量
        for key, value in attrs.items():
            # 替换 {{key}} 格式的变量，支持空格
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            result = re.sub(pattern, value, result)
        
        # 处理未替换的模板变量（没有提供对应属性的变量）
        # 对于 style 属性，如果没有提供，移除整个 style 属性
        if 'style' not in attrs:
            # 移除 style="{{ style }}" 或 style="{{style}}" 等格式
            result = re.sub(r'\s*style\s*=\s*\{\{\s*style\s*\}\}\s*', '', result)
        
        # 对于其他未替换的变量，移除它们
        result = re.sub(r'\{\{\s*\w+\s*\}\}', '', result)
        
        # 清理空的 style 属性
        result = re.sub(r'\s*style\s*=\s*""\s*', '', result)
        
        # 如果标签内容为空，转换为自闭合标签
        # 匹配 >< 和 </xl-p> 之间的空白内容（包括没有空格的情况）
        result = re.sub(r'><\s*</xl-p>', '/>', result)
        # 处理完全空的内容
        result = re.sub(r'><</xl-p>', '/>', result)
        
        # 清理多余的空白字符，但保留必要的结构
        # 只清理模板内部的换行符，保留内容的结构
        result = re.sub(r'\n\s*', '', result)     # 移除换行符及其后的空白
        result = re.sub(r'\s+', ' ', result)      # 将多个连续空白字符替换为单个空格
        result = result.strip()                   # 移除首尾空白
        
        return result

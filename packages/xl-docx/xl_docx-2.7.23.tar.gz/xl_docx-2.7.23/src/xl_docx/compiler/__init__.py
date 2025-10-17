from jinja2 import Environment, BaseLoader, TemplateNotFound
from typing import Dict, Any
from xl_docx.compiler.processors import StyleProcessor, DirectiveProcessor, \
TableProcessor, ParagraphProcessor, PagerProcessor
from xl_docx.mixins.component import ComponentMixin


class XMLTemplateLoader(BaseLoader):
    def __init__(self, template_str: str):
        self.template_str = template_str

    def get_source(self, environment: Environment, template: str) -> tuple:
        if template == 'root':
            return self.template_str, None, lambda: True
        raise TemplateNotFound(template)

class XMLCompiler:
    """XML编译器主类"""
    
    # 自定义语法映射到Jinja2语法
    SYNTAX_MAP = {
        r'($': '{%',
        r'$)': '%}', 
        r'((': '{{',
        r'))': '}}',
    }
    
    def __init__(self, external_components_dir=None):
        # 初始化组件缓存
        ComponentMixin._load_all_components(external_components_dir)
        self.processors = [
            StyleProcessor(),
            DirectiveProcessor(), 
            TableProcessor(),
            ParagraphProcessor(),
            PagerProcessor(),
            ComponentMixin
        ]
        self.env = Environment(
            loader=XMLTemplateLoader(""),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )

    @classmethod
    def convert_syntax(cls, content: str) -> str:
        """转换自定义语法为Jinja2语法
        
        Args:
            content: 包含自定义语法的内容
            
        Returns:
            str: 转换后的内容
        """
        for custom, jinja in cls.SYNTAX_MAP.items():
            content = content.replace(custom, jinja)
        return content

    def compile_template(self, template: str) -> str:
        # 运行所有processor
        for processor in self.processors:
            if hasattr(processor, 'compile'):
                template = processor.compile(template)
            elif hasattr(processor, 'process_components'):
                template = processor.process_components(template)
        
        # 在所有processor完成后进行语法转换
        template = self.convert_syntax(template)
        
        return template
    
    def decompile_template(self, template: str) -> str:
        for processor in self.processors:
            if hasattr(processor, 'decompile'):
                template = processor.decompile(template)
            
        return template
    

    def render_template(self, template: str, data: Dict[str, Any], is_compile: bool = True) -> str:
        processed_template = self.compile_template(template) if is_compile else template
        env = Environment(
            loader=XMLTemplateLoader(processed_template),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        template = env.get_template('root')
        result = template.render(**data)
        
        return result

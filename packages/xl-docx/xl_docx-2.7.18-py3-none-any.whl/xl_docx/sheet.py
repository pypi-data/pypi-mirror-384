from xl_docx.word_file import WordFile
from xl_docx.compiler import XMLCompiler
from xl_docx.compiler.processors.component import ComponentProcessor
from pathlib import Path
import math 
import re


class Sheet(WordFile):
    """Word表单对象，用于处理Word模板文件的渲染和XML操作"""
    components_folder = None

    TEMPLATE_FUNCTIONS = {
        'enumerate': enumerate,
        'len': len, 
        'isinstance': isinstance,
        'tuple': tuple,
        'list': list,
        'str': str,
        'float': float,
        'int': int,
        'range': range,
        'ceil': math.ceil,
        'type': type
    }

    def __init__(self, tpl_path, xml_folder=None):
        """初始化Sheet对象
        
        Args:
            tpl_path: Word模板文件路径
            xml_folder: 可选的XML模板文件夹路径
            external_components_dir: 可选的外置组件目录路径
        """
        super().__init__(tpl_path)
        self.xml_folder = xml_folder
        # 初始化组件处理器
        self._component_processor = ComponentProcessor(self.components_folder)

    def process_components(self, xml: str) -> str:
        """处理组件标签"""
        return self._component_processor.compile(xml)

    def render_template(self, template_content, data, is_compile=True):
        """渲染Jinja2模板
        
        Args:
            template_content: 模板内容字符串
            data: 用于渲染的数据字典
            
        Returns:
            str: 渲染后的内容
        """

        rendered = XMLCompiler().render_template(template_content, {
            **data,
            **self.TEMPLATE_FUNCTIONS
        }, is_compile=is_compile)
        return rendered.replace(' & ', ' &amp; ')


    def get_xml_template(self, xml_filename, use_internal_template=False):
        """获取XML模板内容
        
        Args:
            xml_filename: XML文件名(不含扩展名)
            
        Returns:
            str: XML模板内容
        """
        if use_internal_template:
            return self._read_internal_template(xml_filename)
        if self.xml_folder:
            xml_path = Path(self.xml_folder) / f'{xml_filename}.xml'
            return self._read_external_template(xml_path)
        return self._read_internal_template(xml_filename)

    def _read_external_template(self, xml_path):
        """读取外部XML模板文件
        
        Args:
            xml_path: XML文件完整路径
            
        Returns:
            str: XML文件内容
        """
        with open(xml_path, 'r', encoding='utf-8') as file:
            return file.read()

    def _read_internal_template(self, xml_filename):
        """读取Word文档内部的XML模板
        
        Args:
            xml_filename: XML文件名
            
        Returns:
            str: XML文件内容
        """
        return self[f'word/{xml_filename}.xml'].decode()

    def download_file_as_bytes(self, uri):
        """下载文件为字节数据 - 待实现的方法
        
        Args:
            uri: 文件URI
            
        Returns:
            bytes: 文件字节数据
            
        Raises:
            NotImplementedError: 此方法需要子类实现
        """
        raise NotImplementedError("download_file_as_bytes方法需要在子类中实现")

    def _process_image_data(self, xml_string, xml_filename):
        """处理XML字符串中的图片数据
        
        Args:
            xml_string: 渲染后的XML字符串
            xml_filename: XML文件名
            
        Returns:
            str: 处理后的XML字符串
        """
        # 搜索所有<v:imagedata r:id="xxx"/>模式
        # 支持匹配<v:imagedata ... r:id="xxx" ... />，确保捕获r:id属性（即使属性顺序变化或包含其他属性）
        pattern = r'(<v:imagedata\b[^>]*\br:id="([^"]+)"[^>]*/>)'
        matches = re.findall(pattern, xml_string)
        
        for full_match, uri in matches:
            if '/' in uri:
                try:
                    # 通过download_file_as_bytes下载图片字节
                    image_bytes = self.download_file_as_bytes(uri)
                    
                    # 添加图片到文档并获取关系ID
                    image_rid = self.add_image(image_bytes, xml_filename=f'{xml_filename}.xml')
                    # 替换原来的URI为新的关系ID
                    new_replacement = f'<v:imagedata r:id="{image_rid}"/>'
                    xml_string = xml_string.replace(full_match, new_replacement)
                    
                except Exception as e:
                    print(f"处理图片 {uri} 时出错: {e}")
                    # 如果处理失败，保持原样
                    continue
                
        return xml_string

    def render_xml(self, xml_filename, data, use_internal_template=False):
        self.register_img()
        try:
            xml_template = self.get_xml_template(xml_filename, use_internal_template=use_internal_template)
            
            # 如果xml_filename包含"document"，检查是否需要包装w:document标签
            if "document" in xml_filename:
                # 检查是否已经包含w:document标签
                if "<w:document" not in xml_template:
                    # 包装在完整的Word文档结构中
                    word_document_wrapper = '''<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14">
<w:body>
{content}
</w:body>
</w:document>'''
                    xml_template = word_document_wrapper.format(content=xml_template)
            
            # 如果xml_filename包含"header"，检查是否需要包装w:hdr标签
            if "header" in xml_filename:
                xml_type = 'header'
                # 检查是否已经包含w:hdr标签
                if "<w:hdr" not in xml_template:
                    # 包装在完整的Word header结构中
                    word_header_wrapper = '''<w:hdr mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
{content}
</w:hdr>'''
                    xml_template = word_header_wrapper.format(content=xml_template)
                    
            
            # 如果xml_filename包含"footer"，检查是否需要包装w:ftr标签
            if "footer" in xml_filename:
                # 检查是否已经包含w:ftr标签
                if "<w:ftr" not in xml_template:
                    # 包装在完整的Word footer结构中
                    word_footer_wrapper = '''<w:ftr mc:Ignorable="w14 w15 w16se w16cid w16 w16cex w16sdtdh w16sdtfl w16du wp14" xmlns:aink="http://schemas.microsoft.com/office/drawing/2016/ink" xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:cx1="http://schemas.microsoft.com/office/drawing/2015/9/8/chartex" xmlns:cx2="http://schemas.microsoft.com/office/drawing/2015/10/21/chartex" xmlns:cx3="http://schemas.microsoft.com/office/drawing/2016/5/9/chartex" xmlns:cx4="http://schemas.microsoft.com/office/drawing/2016/5/10/chartex" xmlns:cx5="http://schemas.microsoft.com/office/drawing/2016/5/11/chartex" xmlns:cx6="http://schemas.microsoft.com/office/drawing/2016/5/12/chartex" xmlns:cx7="http://schemas.microsoft.com/office/drawing/2016/5/13/chartex" xmlns:cx8="http://schemas.microsoft.com/office/drawing/2016/5/14/chartex" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:oel="http://schemas.microsoft.com/office/2019/extlst" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:w16="http://schemas.microsoft.com/office/word/2018/wordml" xmlns:w16cex="http://schemas.microsoft.com/office/word/2018/wordml/cex" xmlns:w16cid="http://schemas.microsoft.com/office/word/2016/wordml/cid" xmlns:w16du="http://schemas.microsoft.com/office/word/2023/wordml/word16du" xmlns:w16sdtdh="http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash" xmlns:w16sdtfl="http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock" xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
{content}
</w:ftr>'''
                    xml_template = word_footer_wrapper.format(content=xml_template)
            
            # 处理组件标签
            xml_template = self.process_components(xml_template)
            xml_string = self.render_template(xml_template, data)
            
            # 处理图片数据：搜索<v:imagedata r:id="xxx"/>并替换为实际的图片ID
            xml_string = self._process_image_data(xml_string, xml_filename)
            
            xml_bytes = xml_string.encode()
            self[f'word/{xml_filename}.xml'] = xml_bytes
            return xml_bytes
        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except Exception as e:
            raise e
            print(f"An error occurred: {e}")

    def render_and_add_xml(self, xml_file, data, relation_id=None, use_internal_template=False):
        """渲染并添加新的XML文件到文档
        
        Args:
            xml_type: XML类型
            data: 渲染数据
            relation_id: 可选的关系ID
            
        Returns:
            str: 生成的关系ID
        """
        xml_content = self.render_template(
            self.get_xml_template(xml_file, use_internal_template = use_internal_template),
            data
        )
        if 'header' in xml_file:
            xml_type = 'header'
        elif 'footer' in xml_file:
            xml_type = 'footer'
        else:
            xml_type = 'document'
        return self.add_xml(xml_type, xml_content, relation_id)
    

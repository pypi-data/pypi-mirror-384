import re
from xl_docx.compiler.processors.base import BaseProcessor


class ImageProcessor(BaseProcessor):
    """处理图片相关的XML标签"""
    def compile(self, xml: str) -> str:
        def process_image(match):
            attrs = self._extract_attrs(match.group(0), ['rid', 'width', 'height'])
            rid = attrs[0]  # rid
            width = attrs[1]  # width
            height = attrs[2]  # height
            
            return f'''<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:{width}px;height:{height}px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="{rid}"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>'''
        
        def process_box_image(match):
            attrs = self._extract_attrs(match.group(0), ['rid', 'width', 'height', 'boxWidth', 'boxHeight'])
            rid = attrs[0]  # rid
            width = attrs[1]  # width
            height = attrs[2]  # height
            box_width = attrs[3]  # boxWidth
            box_height = attrs[4]  # boxHeight
            
            return f'''($ with $)
($ set max_width = {box_width} $)
($ set max_height = {box_height} $)
($ set original_width = {width} $)
($ set original_height = {height} $)
($ set width_ratio = max_width / original_width $)
($ set height_ratio = max_height / original_height $)
($ set scale_ratio = min(width_ratio, height_ratio) $)
($ set scaled_width = original_width * scale_ratio $)
($ set scaled_height = original_height * scale_ratio $)
<xl-image rid="{rid}" width="((scaled_width))" height="((scaled_height))"/>
($ endwith $)'''
        
        # 先处理 xl-box-image 标签（支持自闭合和有内容的标签）
        xml = self._process_tag(xml, r'<xl-box-image[^>]*?(?:/>|>.*?</xl-box-image>)', process_box_image, flags=re.DOTALL)
        # 再处理 xl-image 标签（支持自闭合和有内容的标签）
        xml = self._process_tag(xml, r'<xl-image[^>]*?(?:/>|>.*?</xl-image>)', process_image, flags=re.DOTALL)
        
        return xml

from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphImageProcessor:
    """测试段落图片功能"""

    def test_compile_xl_image_in_span(self):
        """测试xl-image标签在xl-span中的编译"""
        xml = '''<xl-p>
    <xl-span>
        <xl-image rid="rId1" width="200" height="150"></xl-image>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查是否包含段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        assert '</w:pPr>' in result
        
        # 检查是否包含图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert '<v:shape' in result
        assert 'r:id="rId1"' in result
        assert 'width:200px' in result
        assert 'height:150px' in result
        
        # 检查图片是否在span结构中
        assert '<v:imagedata' in result
        assert '<o:lock' in result

    def test_compile_xl_image_in_span_with_style(self):
        """测试带样式的xl-span中包含xl-image标签的编译"""
        xml = '''<xl-p>
    <xl-span style="color:red;font-size:14px">
        <xl-image rid="rId2" width="300" height="200"></xl-image>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查span样式
        assert '<w:rPr>' in result
        assert '<w:color w:val="red"/>' in result
        assert '<w:sz w:val="14px"/>' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="rId2"' in result
        assert 'width:300px' in result
        assert 'height:200px' in result

    def test_compile_xl_image_in_span_with_template_variables(self):
        """测试xl-span中包含带模板变量的xl-image标签的编译"""
        xml = '''<xl-p>
    <xl-span>
        <xl-image rid="{{image_id}}" width="{{img_width}}" height="{{img_height}}"></xl-image>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查图片结构中的模板变量
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="{{image_id}}"' in result
        assert 'width:{{img_width}}px' in result
        assert 'height:{{img_height}}px' in result

    def test_compile_multiple_xl_images_in_spans(self):
        """测试多个xl-span中包含xl-image标签的编译"""
        xml = '''<xl-p>
    <xl-span>图片1: <xl-image rid="rId1" width="100" height="80"></xl-image></xl-span>
    <xl-span>图片2: <xl-image rid="rId2" width="200" height="150"></xl-image></xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查两个图片都被编译
        assert result.count('<w:r>') == 2
        assert result.count('<w:pict>') == 2
        assert result.count('<v:imagedata') == 2
        
        # 检查具体的图片ID
        assert 'r:id="rId1"' in result
        assert 'r:id="rId2"' in result
        assert 'width:100px' in result
        assert 'width:200px' in result
        
        # 检查文本内容
        assert '图片1:' in result
        assert '图片2:' in result

    def test_compile_xl_image_in_nested_spans(self):
        """测试嵌套xl-span中包含xl-image标签的编译"""
        xml = '''<xl-p>
    <xl-span style="color:blue">
        外层span
        <xl-span style="font-weight:bold">
            内层span: <xl-image rid="rId3" width="150" height="120"></xl-image>
        </xl-span>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="rId3"' in result
        assert 'width:150px' in result
        assert 'height:120px' in result
        
        # 检查文本内容
        assert '外层span' in result
        assert '内层span:' in result

from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphBoxImageProcessor:
    """测试段落box-image功能"""

    def test_compile_xl_box_image_in_p(self):
        """测试xl-box-image标签在xl-p中的编译"""
        xml = '''<xl-p>
    <xl-box-image rid="rId1" width="400" height="300" boxWidth="200" boxHeight="150"></xl-box-image>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        assert '</w:pPr>' in result
        
        # 检查box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 200' in result
        assert 'max_height = 150' in result
        assert 'original_width = 400' in result
        assert 'original_height = 300' in result
        assert '($ endwith $)' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert '<v:shape' in result
        assert 'r:id="rId1"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result

    def test_compile_xl_box_image_in_span(self):
        """测试xl-box-image标签在xl-span中的编译"""
        xml = '''<xl-p>
    <xl-span>
        <xl-box-image rid="rId2" width="600" height="400" boxWidth="300" boxHeight="200"></xl-box-image>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        assert '</w:pPr>' in result
        
        # 检查box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 300' in result
        assert 'max_height = 200' in result
        assert 'original_width = 600' in result
        assert 'original_height = 400' in result
        assert '($ endwith $)' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert '<v:shape' in result
        assert 'r:id="rId2"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result

    def test_compile_xl_box_image_in_span_with_style(self):
        """测试带样式的xl-span中包含xl-box-image标签的编译"""
        xml = '''<xl-p>
    <xl-span style="color:red;font-size:14px">
        <xl-box-image rid="rId3" width="800" height="600" boxWidth="400" boxHeight="300"></xl-box-image>
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
        
        # 检查box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 400' in result
        assert 'max_height = 300' in result
        assert 'original_width = 800' in result
        assert 'original_height = 600' in result
        assert '($ endwith $)' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="rId3"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result

    def test_compile_xl_box_image_in_span_with_template_variables(self):
        """测试xl-span中包含带模板变量的xl-box-image标签的编译"""
        xml = '''<xl-p>
    <xl-span>
        <xl-box-image rid="image_id" width="img_width" height="img_height" boxWidth="box_w" boxHeight="box_h"></xl-box-image>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查box-image的模板代码中的模板变量
        assert '($ with $)' in result
        assert 'max_width = box_w' in result
        assert 'max_height = box_h' in result
        assert 'original_width = img_width' in result
        assert 'original_height = img_height' in result
        assert '($ endwith $)' in result
        
        # 检查图片结构中的模板变量
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="image_id"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result

        xml = '''
        <xl-p style="align:center">
                <xl-box-image rid="r['image']['rid']" width="r['image']['width']" height="r['image']['height']" boxWidth="658" boxHeight="764"/>
            </xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(result)

    def test_compile_xl_box_image_self_closing_in_span(self):
        """测试自闭合xl-box-image标签在xl-span中的编译"""
        xml = '''<xl-p>
    <xl-span>
        <xl-box-image rid="rId4" width="500" height="350" boxWidth="250" boxHeight="175"/>
    </xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 250' in result
        assert 'max_height = 175' in result
        assert 'original_width = 500' in result
        assert 'original_height = 350' in result
        assert '($ endwith $)' in result
        
        # 检查图片结构
        assert '<w:r>' in result
        assert '<w:pict>' in result
        assert 'r:id="rId4"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result

    def test_compile_mixed_xl_image_and_xl_box_image_in_spans(self):
        """测试xl-span中混合使用xl-image和xl-box-image标签的编译"""
        xml = '''<xl-p>
    <xl-span>普通图片: <xl-image rid="rId1" width="100" height="80"></xl-image></xl-span>
    <xl-span>缩放图片: <xl-box-image rid="rId2" width="400" height="300" boxWidth="200" boxHeight="150"></xl-box-image></xl-span>
</xl-p>'''
        
        result = ParagraphProcessor.compile(xml)
        
        # 检查段落结构
        assert '<w:p>' in result
        assert '<w:pPr>' in result
        
        # 检查普通图片
        assert 'r:id="rId1"' in result
        assert 'width:100px' in result
        assert 'height:80px' in result
        
        # 检查box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 200' in result
        assert 'max_height = 150' in result
        assert 'original_width = 400' in result
        assert 'original_height = 300' in result
        assert '($ endwith $)' in result
        
        # 检查缩放图片
        assert 'r:id="rId2"' in result
        assert 'width:((scaled_width))px' in result
        assert 'height:((scaled_height))px' in result
        
        # 检查文本内容
        assert '普通图片:' in result
        assert '缩放图片:' in result

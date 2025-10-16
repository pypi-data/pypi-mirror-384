from xl_docx.compiler.processors.paragraph.image import ImageProcessor


class TestImageProcessor:
    """测试ImageProcessor的功能"""
    
    def test_compile_xl_image_basic(self):
        """测试基本的xl-image标签编译"""
        processor = ImageProcessor()
        xml = '<xl-image rid="{{rid}}" width="{{width}}" height="{{height}}"></xl-image>'
        
        result = processor.compile(xml)
        
        expected = '''<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:{{width}}px;height:{{height}}px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="{{rid}}"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>'''
        
        assert result == expected
    
    def test_compile_xl_image_with_content(self):
        """测试包含内容的xl-image标签编译"""
        processor = ImageProcessor()
        xml = '<xl-image rid="rId1" width="200" height="150">Some content</xl-image>'
        
        result = processor.compile(xml)
        
        expected = '''<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:200px;height:150px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="rId1"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>'''
        
        assert result == expected
    
    def test_compile_xl_image_in_span(self):
        """测试xl-image标签在xl-span中的使用"""
        processor = ImageProcessor()
        xml = '''<xl-span>
    <xl-image rid="{{rid}}" width="{{width}}" height="{{height}}"></xl-image>
</xl-span>'''
        
        result = processor.compile(xml)
        
        expected = '''<xl-span>
    <w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:{{width}}px;height:{{height}}px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="{{rid}}"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>
</xl-span>'''
        
        assert result == expected
    
    def test_compile_multiple_xl_images(self):
        """测试多个xl-image标签的编译"""
        processor = ImageProcessor()
        xml = '''<div>
    <xl-image rid="rId1" width="100" height="80"></xl-image>
    <xl-image rid="rId2" width="200" height="150"></xl-image>
</div>'''
        
        result = processor.compile(xml)
        
        # 检查是否包含两个编译后的图片
        assert result.count('<w:r>') == 2
        assert result.count('<v:imagedata') == 2
        assert 'r:id="rId1"' in result
        assert 'r:id="rId2"' in result
        assert 'width:100px' in result
        assert 'width:200px' in result
    
    def test_compile_xl_image_no_match(self):
        """测试没有xl-image标签时的处理"""
        processor = ImageProcessor()
        xml = '<div>No image here</div>'
        
        result = processor.compile(xml)
        
        assert result == xml
    
    def test_compile_xl_image_missing_attributes(self):
        """测试缺少属性的xl-image标签"""
        processor = ImageProcessor()
        xml = '<xl-image rid="rId1"></xl-image>'
        
        result = processor.compile(xml)
        
        # 即使缺少width和height属性，也应该能编译
        assert '<w:r>' in result
        assert 'r:id="rId1"' in result
        assert 'width:Nonepx' in result
        assert 'height:Nonepx' in result
    
    def test_compile_xl_image_with_template_variables(self):
        """测试包含模板变量的xl-image标签"""
        processor = ImageProcessor()
        xml = '<xl-image rid="{{image_id}}" width="{{img_width}}" height="{{img_height}}"></xl-image>'
        
        result = processor.compile(xml)
        
        expected = '''<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:{{img_width}}px;height:{{img_height}}px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="{{image_id}}"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>'''
        
        assert result == expected
    
    def test_compile_xl_box_image_basic(self):
        """测试基本的xl-box-image标签编译"""
        processor = ImageProcessor()
        xml = '<xl-box-image rid="rId1" width="400" height="300" boxWidth="200" boxHeight="150"></xl-box-image>'
        
        result = processor.compile(xml)
        
        expected = '''($ with $)
($ set max_width = 200 $)
($ set max_height = 150 $)
($ set original_width = 400 $)
($ set original_height = 300 $)
($ set width_ratio = max_width / original_width $)
($ set height_ratio = max_height / original_height $)
($ set scale_ratio = min(width_ratio, height_ratio) $)
($ set scaled_width = original_width * scale_ratio $)
($ set scaled_height = original_height * scale_ratio $)
<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:((scaled_width))px;height:((scaled_height))px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="rId1"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>
($ endwith $)'''
        
        assert result == expected
    
    def test_compile_xl_box_image_self_closing(self):
        """测试自闭合的xl-box-image标签编译"""
        processor = ImageProcessor()
        xml = '<xl-box-image rid="rId2" width="800" height="600" boxWidth="300" boxHeight="200"/>'
        
        result = processor.compile(xml)
        
        expected = '''($ with $)
($ set max_width = 300 $)
($ set max_height = 200 $)
($ set original_width = 800 $)
($ set original_height = 600 $)
($ set width_ratio = max_width / original_width $)
($ set height_ratio = max_height / original_height $)
($ set scale_ratio = min(width_ratio, height_ratio) $)
($ set scaled_width = original_width * scale_ratio $)
($ set scaled_height = original_height * scale_ratio $)
<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:((scaled_width))px;height:((scaled_height))px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="rId2"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>
($ endwith $)'''
        
        assert result == expected
    
    def test_compile_xl_box_image_with_template_variables(self):
        """测试包含模板变量的xl-box-image标签"""
        processor = ImageProcessor()
        xml = '<xl-box-image rid="image_id" width="img_width" height="img_height" boxWidth="box_w" boxHeight="box_h"></xl-box-image>'
        
        result = processor.compile(xml)
        
        expected = '''($ with $)
($ set max_width = box_w $)
($ set max_height = box_h $)
($ set original_width = img_width $)
($ set original_height = img_height $)
($ set width_ratio = max_width / original_width $)
($ set height_ratio = max_height / original_height $)
($ set scale_ratio = min(width_ratio, height_ratio) $)
($ set scaled_width = original_width * scale_ratio $)
($ set scaled_height = original_height * scale_ratio $)
<w:r>
    <w:pict>
        <v:shape coordsize="21600,21600" filled="f" id="_x0000_s1026" o:spid="_x0000_s1026" o:spt="75" style="width:((scaled_width))px;height:((scaled_height))px" type="#_x0000_t75">
            <v:path/>
            <v:fill focussize="0,0" on="f"/>
            <v:stroke/>
            <v:imagedata o:title="" r:id="image_id"/>
            <o:lock v:ext="edit"/>
            <w10:wrap type="none"/>
            <w10:anchorlock/>
        </v:shape>
    </w:pict>
</w:r>
($ endwith $)'''
        
        assert result == expected
    
    def test_compile_xl_box_image_mixed_with_xl_image(self):
        """测试xl-box-image和xl-image混合使用"""
        processor = ImageProcessor()
        xml = '''<div>
    <xl-box-image rid="rId1" width="400" height="300" boxWidth="200" boxHeight="150"/>
    <xl-image rid="rId2" width="100" height="80"></xl-image>
</div>'''
        
        result = processor.compile(xml)
        
        # 检查是否包含box-image的模板代码
        assert '($ with $)' in result
        assert 'max_width = 200' in result
        assert 'max_height = 150' in result
        assert 'original_width = 400' in result
        assert 'original_height = 300' in result
        assert '($ endwith $)' in result
        
        # 检查是否包含普通image的编译结果
        assert '<w:r>' in result
        assert 'r:id="rId2"' in result
        assert 'width:100px' in result
        assert 'height:80px' in result
    
    def test_compile_xl_box_image_missing_attributes(self):
        """测试缺少属性的xl-box-image标签"""
        processor = ImageProcessor()
        xml = '<xl-box-image rid="rId1" width="400" height="300"></xl-box-image>'
        
        result = processor.compile(xml)
        
        # 即使缺少boxWidth和boxHeight属性，也应该能编译
        assert '($ with $)' in result
        assert 'r:id="rId1"' in result
        assert 'original_width = 400' in result
        assert 'original_height = 300' in result
        assert 'max_width = None' in result
        assert 'max_height = None' in result
from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphStyleProcessor:
    """测试段落样式功能"""

    def test_compile_paragraph_with_style(self):
        """测试编译带样式的段落"""
        xml = '<xl-p style="align:center;margin-top:10px;line-height:14pt;font-size:14px">content</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:jc w:val="center"/>' in result
        assert 'w:before="10px"' in result
        assert 'w:line="14pt"' in result
        assert 'w:val="14px"' in result
    
    def test_compile_paragraph_with_fonts(self): 
        """测试编译带字体的段落"""
        xml = '<xl-p style="english:Arial;chinese:SimSun;font-size:12px">content</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert 'w:ascii="Arial"' in result
        assert 'w:cs="SimSun"' in result
        assert 'w:val="12px"' in result
    
    def test_compile_paragraph_with_bold(self):
        """测试编译粗体段落"""
        xml = '<xl-p style="font-weight:bold">content</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:b/>' in result
    
    def test_compile_paragraph_complex_style(self):
        """测试编译复杂样式的段落"""
        xml = '''<xl-p style="align:right;margin-top:20px;margin-bottom:10px;english:Times New Roman;chinese:宋体;font-size:16px;font-weight:bold">content</xl-p>'''
        result = ParagraphProcessor.compile(xml)
        assert '<w:jc w:val="right"/>' in result
        assert 'w:before="20px"' in result
        assert 'w:after="10px"' in result
        assert 'w:ascii="Times New Roman"' in result
        assert 'w:cs="宋体"' in result
        assert 'w:val="16px"' in result
        assert '<w:b/>' in result
    
    def test_decompile_paragraph_with_alignment(self):
        """测试反编译带对齐的段落"""
        xml = '''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'align:center' in result
    
    def test_decompile_paragraph_with_spacing(self):
        """测试反编译带间距的段落"""
        xml = '''<w:p><w:pPr><w:spacing w:before="20px" w:after="10px"/></w:pPr><w:r><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'margin-top:20px' in result
        assert 'margin-bottom:10px' in result
        xml = '''
        <w:p>
            <w:pPr>
                <w:spacing w:before="240" w:line="18pt" w:lineRule="auto"/>
            </w:pPr>
            <w:r>
                <w:t>This is a paragraph with 12pt spacing above.</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert 'line-height:18pt' in result
    
    def test_decompile_paragraph_with_fonts(self):
        """测试反编译带字体的段落"""
        xml = '''<w:p><w:r><w:rPr><w:rFonts w:ascii="Arial" w:cs="SimSun"/></w:rPr><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'english:Arial' in result
        assert 'chinese:SimSun' in result
    
    def test_decompile_paragraph_with_font_size(self):
        """测试反编译带字体大小的段落"""
        xml = '''<w:p><w:r><w:rPr><w:sz w:val="16px"/></w:rPr><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'font-size:16px' in result
    
    def test_decompile_paragraph_with_bold(self):
        """测试反编译粗体段落"""
        xml = '''<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'font-weight:bold' in result
    
    def test_decompile_paragraph_with_underline(self):
        """测试反编译带下划线的段落"""
        xml = '''<w:p><w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'underline:single' in result
    
    def test_decompile_paragraph_complex(self):
        """测试反编译复杂段落"""
        xml = '''<w:p><w:pPr><w:jc w:val="right"/><w:spacing w:before="20px" w:after="10px"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Arial" w:cs="SimSun"/><w:sz w:val="16px"/><w:b/></w:rPr><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'align:right' in result
        assert 'margin-top:20px' in result
        assert 'margin-bottom:10px' in result
        assert 'english:Arial' in result
        assert 'chinese:SimSun' in result
        assert 'font-size:16px' in result
        assert 'font-weight:bold' in result

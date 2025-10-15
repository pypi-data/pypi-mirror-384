from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphSpanProcessor:
    """测试段落span功能"""

    def test_compile_paragraph_with_span(self):
        """测试编译包含span的段落"""
        xml = '<xl-p>text<xl-span style="underline:single;font-size:16px">span content</xl-span>more text</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:u w:val="single"/>' in result
        assert 'w:val="16px"' in result
        assert 'span content' in result
    
    def test_compile_paragraph_with_nested_spans(self):
        """测试编译包含嵌套span的段落"""
        xml = '''<xl-p><xl-span style="underline:double">span1</xl-span><xl-span style="font-weight:bold">span2</xl-span><xl-span>more text</xl-span></xl-p>'''
        result = ParagraphProcessor.compile(xml)
        assert '<w:u w:val="double"/>' in result
        assert '<w:b/>' in result
        assert 'span1' in result
        assert 'span2' in result
    
    def test_decompile_paragraph_with_span(self):
        """测试反编译包含span的段落"""
        xml = '''<w:p><w:r><w:t>text</w:t></w:r><w:r><w:rPr><w:u w:val="double"/></w:rPr><w:t>span content</w:t></w:r><w:r><w:t>more text</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-span' in result
        assert 'underline:double' in result
        assert 'span content' in result
    
    def test_decompile_paragraph_with_multiple_runs(self):
        """测试反编译包含多个运行的段落"""
        xml = '''<w:p><w:r><w:t>part1</w:t></w:r><w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>part2</w:t></w:r><w:r><w:t>part3</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'part1' in result
        assert 'part2' in result
        assert 'part3' in result
        assert '<xl-span' in result
        assert 'underline:single' in result
    
    def test_decompile_paragraph_with_nested_spans(self):
        """测试反编译包含嵌套span的段落"""
        xml = '''<w:p><w:r><w:t>text</w:t></w:r><w:r><w:rPr><w:u w:val="double"/></w:rPr><w:t>span1</w:t></w:r><w:r><w:rPr><w:u w:val="double"/><w:b/></w:rPr><w:t>span2</w:t></w:r><w:r><w:rPr><w:u w:val="double"/></w:rPr><w:t>span3</w:t></w:r><w:r><w:t>more text</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'text' in result
        assert 'span1' in result
        assert 'span2' in result
        assert 'span3' in result
        assert 'more text' in result
        assert '<xl-span' in result
        assert 'underline:double' in result
        assert 'font-weight:bold' in result
    
    def test_decompile_paragraph_no_runs(self):
        """测试反编译没有运行标签的段落"""
        xml = '''<w:p><w:pPr><w:jc w:val="center"/></w:pPr></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-p style="align:center"></xl-p>' in result  # 应该转换为xl-p格式
    
    def test_decompile_paragraph_with_empty_runs(self):
        """测试反编译包含空运行的段落"""
        xml = '''<w:p><w:r><w:t></w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-p><xl-span></xl-span></xl-p>' in result

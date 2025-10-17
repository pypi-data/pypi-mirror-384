from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphBasicProcessor:
    """测试基础段落功能"""

    def test_compile_simple_paragraph(self):
        """测试编译简单段落"""
        xml = '<xl-p style="align:center;english:SimSun;chinese:SimSun">检件名称</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:p>' in result
        assert '<w:r>' in result
        assert '<w:t' in result
        assert '检件名称' in result

        xml = '<xl-p style="align:left">检测结果及说明：</xl-p>'
        result = ParagraphProcessor.compile(xml)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(result)
    
    def test_compile_paragraph_no_style(self):
        """测试编译无样式的段落"""
        xml = '<xl-p>content</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:p>' in result
        assert '<w:r>' in result
        assert '<w:t' in result
        assert 'content' in result
    
    def test_compile_paragraph_empty_content(self):
        """测试编译空内容的段落"""
        xml = '<xl-p></xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:p>' in result
        assert '<w:r>' in result
        assert '<w:t' in result
    
    def test_compile_paragraph_with_whitespace(self):
        """测试编译包含空白字符的段落"""
        xml = '<xl-p>  content with spaces  </xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert 'content with spaces' in result
    
    def test_compile_paragraph_with_special_characters(self):
        """测试编译包含特殊字符的段落"""
        xml = '<xl-p>content with &lt;tags&gt; and "quotes"</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert 'content with &lt;tags&gt; and "quotes"' in result
    
    def test_decompile_simple_paragraph(self):
        """测试反编译简单段落"""
        xml = '''<w:p><w:r><w:t>content</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-p>' in result
        assert 'content' in result
    
    def test_decompile_paragraph_with_whitespace(self):
        """测试反编译包含空白字符的段落"""
        xml = '''<w:p><w:r><w:t xml:space="preserve">  content with spaces  </w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'content with spaces' in result
    
    def test_decompile_paragraph_with_special_characters(self):
        """测试反编译包含特殊字符的段落"""
        xml = '''<w:p><w:r><w:t>content with &lt;tags&gt; and "quotes"</w:t></w:r></w:p>'''
        result = ParagraphProcessor.decompile(xml)
        assert 'content with &lt;tags&gt; and "quotes"' in result

    def test_decompile_with_empty_space(self):
        xml = '''
        <w:p>
            <w:r>
                <w:t xml:space="preserve">  邮编：201700</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-p><xl-span>  邮编：201700</xl-span></xl-p>' in result

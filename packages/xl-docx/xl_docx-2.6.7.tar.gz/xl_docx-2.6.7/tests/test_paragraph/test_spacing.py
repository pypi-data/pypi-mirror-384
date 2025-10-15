from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphSpacingProcessor:
    """测试段落间距和边距功能"""

    def test_decompile_margin(self):
        xml = '''
        <w:p>
            <w:pPr>
                <w:ind w:start="21pt"/>
            </w:pPr>
            <w:r>
                <w:t>This is a paragraph with left indentation of 21pt.</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert 'margin-left:21pt' in result
        xml = '''
        <w:p>
            <w:pPr>
                <w:ind w:end="21pt"/>
            </w:pPr>
            <w:r>
                <w:t>This is a paragraph with right indentation of 21pt.</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert 'margin-right:21pt' in result
        xml = '''
        <w:p>
            <w:pPr>
                <w:ind w:start="21pt" w:end="22pt"/>
            </w:pPr>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert 'margin-left:21pt' in result
        assert 'margin-right:22pt' in result

    def test_compile_margin(self):
        xml = '<xl-p style="margin-left:21pt">This is a paragraph with left indentation of 21pt.</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:ind w:start="21pt"/>' in result
        xml = '<xl-p style="margin-right:21pt">This is a paragraph with right indentation of 21pt.</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:ind w:end="21pt"/>' in result
        xml = '<xl-p style="margin-left:21pt;margin-right:22pt">This is a paragraph with left and right indentation of 21pt and 22pt.</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert '<w:ind w:start="21pt" w:end="22pt"/>' in result

    def test_decompile_r_with_spacing(self):
        xml = '''
        <w:p>
            <w:r>
                <w:rPr>
                    <w:spacing w:val="45"/>
                </w:rPr>
                <w:t>器具名称</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert '<xl-span style="spacing:45">器具名称</xl-span>' in result

    def test_compile_r_with_spacing(self):
        xml = '''<xl-p><xl-span style="spacing:45">器具名称</xl-span></xl-p>'''
        result = ParagraphProcessor.compile(xml)
        assert '<w:spacing w:val="45"/>' in result

    def test_compile_paragraph_with_spacing(self):
        xml = '<xl-p style="spacing:240">This is a paragraph with 12pt spacing above.</xl-p>'
        result = ParagraphProcessor.compile(xml)
        assert 'w:spacing w:val="240"' in result

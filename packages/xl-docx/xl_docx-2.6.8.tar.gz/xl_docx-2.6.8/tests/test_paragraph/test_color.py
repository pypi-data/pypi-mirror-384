from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphColorProcessor:
    """测试段落颜色功能"""

    def test_decompile_with_color(self):
        xml = '''
        <w:p>
            <w:r>
                <w:rPr>
                    <w:color w:val="D7D7D7"/>
                </w:rPr>
                <w:t>content</w:t>
            </w:r>
        </w:p>
        '''
        result = ParagraphProcessor.decompile(xml)
        assert 'color:D7D7D7' in result

    def test_compile_with_color(self):
        xml = '''
        <xl-p style="font-size:12px;color:D7D7D7">content</xl-p>
        '''
        result = ParagraphProcessor.compile(xml)
        assert '<w:color w:val="D7D7D7"/>' in result
        xml = '''
        <xl-p style="color:D7D7D7;font-size:12px;">content</xl-p>
        '''
        result = ParagraphProcessor.compile(xml)
        assert '<w:color w:val="D7D7D7"/>' in result

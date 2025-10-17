from xl_docx.compiler.processors.paragraph import ParagraphProcessor


class TestParagraphBlockProcessor:
    """测试段落block功能"""

    def test_process_block_with_variable(self):
        """测试处理使用变量的xl-block标签"""
        xml = '<xl-block text="{{content}}" style="align:center"></xl-block>'
        result = ParagraphProcessor.process_block(xml)
        assert '($ with $)' in result
        assert '($ set paragraphs={{content}}.split(\'\\n\') $)' in result
        assert '($ for paragraph in paragraphs $)' in result
        assert '<xl-p style="align:center">' in result
        assert '<xl-span>((paragraph))</xl-span>' in result
        assert '($ endfor $)' in result
        assert '($ endwith $)' in result
        assert 'xl-block' not in result
        xml = '''
        <xl-p style="align:left;english:Calibri;chinese:SimSun"/>
        <xl-block text="data.get('purpose','')" style="align:left;english:Calibri;chinese:SimSun"/>
        <xl-p style="align:left;english:Calibri;chinese:SimSun"/>
        '''
        result = ParagraphProcessor.process_block(xml)
        assert 'xl-block' not in result

    def test_process_block_with_variable_and_style(self):
        """测试处理使用变量和样式的xl-block标签"""
        xml = '<xl-block text="{{text_content}}" style="align:center;font-size:14px"></xl-block>'
        result = ParagraphProcessor.process_block(xml)
        assert '($ with $)' in result
        assert '($ set paragraphs={{text_content}}.split(\'\\n\') $)' in result
        assert '($ for paragraph in paragraphs $)' in result
        assert '<xl-p style="align:center;font-size:14px">' in result
        assert '<xl-span>((paragraph))</xl-span>' in result
        assert '($ endfor $)' in result
        assert '($ endwith $)' in result

from xl_docx.compiler.processors.table import TableProcessor


class TestTablePaddingProcessor:
    """测试表格padding相关功能"""

    def test_compile_table_with_padding(self):
        """测试编译带padding的表格"""
        xml = '<xl-table style="padding-top:10;padding-bottom:20;padding-left:30;padding-right:40"><xl-tr><xl-tc>content</xl-tc></xl-tr></xl-table>'
        result = TableProcessor.compile(xml)
        assert '<w:top w:type="dxa" w:w="10"/>' in result
        assert '<w:bottom w:type="dxa" w:w="20"/>' in result
        assert '<w:left w:type="dxa" w:w="30"/>' in result
        assert '<w:right w:type="dxa" w:w="40"/>' in result

    def test_compile_table_with_partial_padding(self):
        """测试编译带部分padding的表格"""
        xml = '<xl-table style="padding-left:108;padding-right:108"><xl-tr><xl-tc>content</xl-tc></xl-tr></xl-table>'
        result = TableProcessor.compile(xml)
        assert '<w:top w:type="dxa" w:w="0"/>' in result
        assert '<w:bottom w:type="dxa" w:w="0"/>' in result
        assert '<w:left w:type="dxa" w:w="108"/>' in result
        assert '<w:right w:type="dxa" w:w="108"/>' in result

    def test_compile_table_with_mixed_style_and_padding(self):
        """测试编译带混合样式和padding的表格"""
        xml = '<xl-table style="align:center;padding-top:15;padding-bottom:25"><xl-tr><xl-tc>content</xl-tc></xl-tr></xl-table>'
        result = TableProcessor.compile(xml)
        assert '<w:jc w:val="center"/>' in result
        assert '<w:top w:type="dxa" w:w="15"/>' in result
        assert '<w:bottom w:type="dxa" w:w="25"/>' in result
        assert '<w:left w:type="dxa" w:w="100"/>' in result
        assert '<w:right w:type="dxa" w:w="100"/>' in result

    def test_compile_table_with_default_padding(self):
        """测试编译使用默认padding值的表格"""
        xml = '<xl-table><xl-tr><xl-tc>content</xl-tc></xl-tr></xl-table>'
        result = TableProcessor.compile(xml)
        assert '<w:top w:type="dxa" w:w="0"/>' in result
        assert '<w:bottom w:type="dxa" w:w="0"/>' in result
        assert '<w:left w:type="dxa" w:w="100"/>' in result
        assert '<w:right w:type="dxa" w:w="100"/>' in result

    def test_decompile_table_with_padding(self):
        """测试反编译带padding的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblCellMar>
                    <w:top w:type="dxa" w:w="10"/>
                    <w:left w:type="dxa" w:w="30"/>
                    <w:bottom w:type="dxa" w:w="20"/>
                    <w:right w:type="dxa" w:w="40"/>
                </w:tblCellMar>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        assert 'padding-top:10' in result
        assert 'padding-bottom:20' in result
        assert 'padding-left:30' in result
        assert 'padding-right:40' in result

    def test_decompile_table_with_partial_padding(self):
        """测试反编译带部分padding的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblCellMar>
                    <w:top w:type="dxa" w:w="0"/>
                    <w:left w:type="dxa" w:w="108"/>
                    <w:bottom w:type="dxa" w:w="0"/>
                    <w:right w:type="dxa" w:w="108"/>
                </w:tblCellMar>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        assert 'padding-left:108' in result
        assert 'padding-right:108' in result
        # 默认值0的padding不应该出现在结果中
        assert 'padding-top:0' not in result
        assert 'padding-bottom:0' not in result

    def test_decompile_table_with_zero_padding(self):
        """测试反编译全零padding的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblCellMar>
                    <w:top w:type="dxa" w:w="0"/>
                    <w:left w:type="dxa" w:w="0"/>
                    <w:bottom w:type="dxa" w:w="0"/>
                    <w:right w:type="dxa" w:w="0"/>
                </w:tblCellMar>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        # 全零padding不应该出现在结果中
        assert 'padding-top' not in result
        assert 'padding-bottom' not in result
        assert 'padding-left' not in result
        assert 'padding-right' not in result

    def test_decompile_table_with_default_padding(self):
        """测试反编译默认padding值的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblCellMar>
                    <w:top w:type="dxa" w:w="0"/>
                    <w:left w:type="dxa" w:w="100"/>
                    <w:bottom w:type="dxa" w:w="0"/>
                    <w:right w:type="dxa" w:w="100"/>
                </w:tblCellMar>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        # 默认的100 padding值不应该出现在结果中
        assert 'padding-top' not in result
        assert 'padding-bottom' not in result
        assert 'padding-left' not in result
        assert 'padding-right' not in result

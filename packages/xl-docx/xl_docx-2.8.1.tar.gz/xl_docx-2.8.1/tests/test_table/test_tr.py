from xl_docx.compiler.processors.table import TableProcessor


class TestTableTrProcessor:
    """测试表格行相关功能"""

    def test_compile_table_header(self):
        """测试编译表格头部"""
        xml = '<xl-th><xl-tc>header</xl-tc></xl-th>'
        result = TableProcessor.compile(xml)
        assert '<w:trPr>' in result
        assert '<w:tblHeader/>' in result
    
    def test_compile_table_header_with_attributes(self):
        """测试编译带属性的表格头部"""
        xml = '<xl-th height="500"><xl-tc>header</xl-tc></xl-th>'
        result = TableProcessor.compile(xml)
        assert '<w:trHeight w:val="500"/>' in result
        assert '<w:tblHeader/>' in result
    
    def test_compile_table_row(self):
        """测试编译表格行"""
        xml = '<xl-tr><xl-tc>content</xl-tc></xl-tr>'
        result = TableProcessor.compile(xml)
        assert '<w:tr>' in result
        assert '<w:trPr>' in result
    
    def test_compile_table_row_with_header(self):
        """测试编译带表头属性的行"""
        xml = '<xl-tr header="1"><xl-tc>content</xl-tc></xl-tr>'
        result = TableProcessor.compile(xml)
        assert '<w:tblHeader/>' in result
    
    def test_compile_table_row_with_cant_split(self):
        """测试编译不可分割的行"""
        xml = '<xl-tr cant-split="1"><xl-tc>content</xl-tc></xl-tr>'
        result = TableProcessor.compile(xml)
        assert '<w:cantSplit/>' in result
    
    def test_compile_table_row_with_height(self):
        """测试编译带高度的行"""
        xml = '<xl-tr height="300"><xl-tc>content</xl-tc></xl-tr>'
        result = TableProcessor.compile(xml)
        assert '<w:trHeight w:val="300"/>' in result
    
    def test_compile_table_row_with_multiple_attributes(self):
        """测试编译带多个属性的行"""
        xml = '<xl-tr header="1" cant-split="1" height="400" class="test"><xl-tc>content</xl-tc></xl-tr>'
        result = TableProcessor.compile(xml)
        assert '<w:tblHeader/>' in result
        assert '<w:cantSplit/>' in result
        assert '<w:trHeight w:val="400"/>' in result
        assert 'class="test"' in result

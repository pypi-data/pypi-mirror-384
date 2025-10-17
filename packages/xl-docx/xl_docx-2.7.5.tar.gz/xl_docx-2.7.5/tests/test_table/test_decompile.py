from xl_docx.compiler.processors.table import TableProcessor


class TestTableDecompileProcessor:
    """测试表格反编译功能"""

    def test_decompile_table_with_width(self):
        """测试反编译带宽度的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblW w:w="525.05pt" w:type="dxa"/>
                <w:jc w:val="center"/>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        assert '<xl-table width="525.05pt"' in result

    def test_decompile_table_with_margin(self):
        """测试反编译带高度的表格"""
        xml = '''
        <w:tbl>
            <w:tblPr>
                <w:tblInd w:w="19.60pt" w:type="dxa"/>
            </w:tblPr>
        </w:tbl>
        '''
        result = TableProcessor.decompile(xml)
        assert 'margin-left:19.60pt' in result

    def test_decompile_table_with_grid_column(self):
        """测试反编译网格列的表格"""
        xml = '<w:tblGrid><w:gridCol w:w="592"/><w:gridCol w:w="779"/><w:gridCol w:w="192"/></w:tblGrid>'
        result = TableProcessor.decompile(xml)
        assert '<xl-table grid="592/779/192"/>' in result

    def test_decompile_simple_table(self):
        """测试反编译简单表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert '<xl-table' in result
        assert '<xl-tr>' in result
        assert '<xl-tc>' in result
        assert 'content' in result
    
    def test_decompile_table_with_alignment(self):
        """测试反编译带对齐的表格"""
        xml = '''<w:tbl><w:tblPr><w:jc w:val="center"/></w:tblPr><w:tr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'align:center' in result
    
    def test_decompile_table_with_borders(self):
        """测试反编译带边框的表格"""
        xml = '''<w:tbl><w:tblPr><w:tblBorders><w:top w:val="none"/><w:bottom w:val="none"/><w:left w:val="none"/><w:right w:val="none"/></w:tblBorders></w:tblPr><w:tr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'border:none' in result
    
    def test_decompile_table_with_header(self):
        """测试反编译带表头的表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:trPr><w:tblHeader/></w:trPr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>header</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'header="1"' in result
    
    def test_decompile_table_with_cant_split(self):
        """测试反编译不可分割的表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'cant-split="1"' in result
    
    def test_decompile_table_with_height(self):
        """测试反编译带高度的表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:trPr><w:trHeight w:val="300"/></w:trPr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'height="300"' in result
    
    def test_decompile_table_cell_with_width(self):
        """测试反编译带宽度的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="2000"/></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'width="2000"' in result
    
    def test_decompile_table_cell_with_span(self):
        """测试反编译带跨列的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:gridSpan w:val="3"/></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'span="3"' in result
    
    def test_decompile_table_cell_with_align(self):
        """测试反编译带对齐的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:vAlign w:val="center"/></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'align="center"' in result
    
    def test_decompile_table_cell_with_merge(self):
        """测试反编译带合并的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:vMerge w:val="restart"/></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'merge="start"' in result
    
    def test_decompile_table_cell_with_continue_merge(self):
        """测试反编译继续合并的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:vMerge/></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'merge="continue"' in result
    
    def test_decompile_table_cell_with_borders(self):
        """测试反编译带边框的单元格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr><w:tcBorders><w:top w:val="nil"/><w:bottom w:val="nil"/></w:tcBorders></w:tcPr><w:p><w:r><w:t>content</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert 'border-top="none"' in result
        assert 'border-bottom="none"' in result
    
    def test_decompile_complex_table(self):
        """测试反编译复杂表格"""
        xml = '''<w:tbl><w:tblPr><w:jc w:val="center"/><w:tblBorders><w:top w:val="none"/></w:tblBorders></w:tblPr><w:tr><w:trPr><w:tblHeader/><w:trHeight w:val="500"/></w:trPr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="1000"/><w:vAlign w:val="center"/></w:tcPr><w:p><w:r><w:t>header</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        
        # 检查表格属性
        assert 'align:center' in result
        assert 'border:none' in result
        
        # 检查行属性
        assert 'header="1"' in result
        assert 'height="500"' in result
        
        # 检查单元格属性
        assert 'width="1000"' in result
        assert 'align="center"' in result

    def test_decompile_table_empty_cells(self):
        """测试反编译空单元格的表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr></w:tcPr><w:p></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert '<xl-tc>' in result

    def test_decompile_table_multiple_rows(self):
        """测试反编译多行表格"""
        xml = '''<w:tbl><w:tblPr></w:tblPr><w:tr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>row1</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:tcPr></w:tcPr><w:p><w:r><w:t>row2</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'''
        result = TableProcessor.decompile(xml)
        assert result.count('<xl-tr>') == 2
        assert 'row1' in result
        assert 'row2' in result

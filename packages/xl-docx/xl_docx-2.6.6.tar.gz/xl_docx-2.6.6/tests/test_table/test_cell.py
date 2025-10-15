from xl_docx.compiler.processors.table import TableProcessor


class TestTableCellProcessor:
    """测试单元格相关功能"""

    def test_compile_table_cell(self):
        """测试编译表格单元格"""
        xml = '<xl-tc>content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:tc>' in result
        assert '<w:tcPr>' in result
    
    def test_compile_table_cell_with_width(self):
        """测试编译带宽度的单元格"""
        xml = '<xl-tc width="2000">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:tcW w:type="dxa" w:w="2000"/>' in result
    
    def test_compile_table_cell_with_span(self):
        """测试编译带跨列的单元格"""
        xml = '<xl-tc span="2">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:gridSpan w:val="2"/>' in result
    
    def test_compile_table_cell_with_align(self):
        """测试编译带对齐的单元格"""
        xml = '<xl-tc align="center">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:vAlign w:val="center"/>' in result
        xml = '<xl-tc>content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:vAlign w:val="center"/>' in result
    
    def test_compile_table_cell_with_merge(self):
        """测试编译带合并的单元格"""
        xml = '<xl-tc merge="start">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:vMerge w:val="restart"/>' in result
    
    def test_compile_table_cell_with_continue_merge(self):
        """测试编译继续合并的单元格"""
        xml = '<xl-tc merge="continue">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:vMerge/>' in result  # 没有val属性
    
    def test_compile_table_cell_with_borders(self):
        """测试编译带边框的单元格"""
        xml = '<xl-tc border-top="none" border-bottom="none" border-left="none" border-right="none">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:top w:val="nil"/>' in result
        assert '<w:bottom w:val="nil"/>' in result
        assert '<w:left w:val="nil"/>' in result
        assert '<w:right w:val="nil"/>' in result
    
    def test_compile_table_cell_with_content_tags(self):
        """测试编译包含标签内容的单元格"""
        xml = '<xl-tc><xl-p>paragraph content</xl-p></xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<xl-p>paragraph content</xl-p>' in result  # 内容应该保持不变
    
    def test_compile_table_cell_complex_attributes(self):
        """测试编译带复杂属性的单元格"""
        xml = '<xl-tc width="1500" span="3" align="center" merge="start" border-top="none">content</xl-tc>'
        result = TableProcessor.compile(xml)
        assert '<w:tcW w:type="dxa" w:w="1500"/>' in result
        assert '<w:gridSpan w:val="3"/>' in result
        assert '<w:vAlign w:val="center"/>' in result
        assert '<w:vMerge w:val="restart"/>' in result
        assert '<w:top w:val="nil"/>' in result

    def test_compile_table_cell_style_merge_to_paragraph(self):
        """测试xl-tc的style属性合并到xl-p的style中"""
        xml = '<xl-tc style="align:center;font-size:14px"><xl-p style="color:red">content</xl-p></xl-tc>'
        result = TableProcessor.compile(xml)
        
        # 检查xl-p的style应该包含合并后的样式
        # 应该包含xl-tc的align:center和font-size:14px，以及xl-p的color:red
        assert 'align:center' in result
        assert 'font-size:14px' in result
        assert 'color:red' in result

    def test_compile_table_cell_style_override_paragraph_style(self):
        """测试xl-tc的style属性覆盖xl-p中相同的样式属性"""
        xml = '<xl-tc style="align:right;font-size:16px"><xl-p style="align:left;color:blue">content</xl-p></xl-tc>'
        result = TableProcessor.compile(xml)
        
        # xl-tc的align:right应该覆盖xl-p的align:left
        # xl-tc的font-size:16px应该覆盖xl-p的font-size（如果xl-p有的话）
        # xl-p的color:blue应该保留
        assert 'align:right' in result
        assert 'font-size:16px' in result
        assert 'color:blue' in result
        # 确保没有xl-p的align:left
        assert 'align:left' not in result

    def test_compile_table_cell_style_with_multiple_paragraphs(self):
        """测试xl-tc的style属性合并到多个xl-p标签中"""
        xml = '''<xl-tc style="align:center;font-size:14px">
    <xl-p style="color:red">paragraph1</xl-p>
    <xl-p style="color:blue">paragraph2</xl-p>
</xl-tc>'''
        result = TableProcessor.compile(xml)
        
        # 两个xl-p都应该包含合并后的样式
        assert 'align:center' in result
        assert 'font-size:14px' in result
        assert 'color:red' in result
        assert 'color:blue' in result

    def test_compile_table_cell_style_with_nested_spans(self):
        """测试xl-tc的style属性合并到嵌套的xl-span标签中"""
        xml = '''<xl-tc style="align:center;font-size:14px">
    <xl-p>
        <xl-span style="color:red">span content</xl-span>
    </xl-p>
</xl-tc>'''
        result = TableProcessor.compile(xml)
        
        # xl-p应该包含xl-tc的样式
        assert 'align:center' in result
        assert 'font-size:14px' in result
        # xl-span的样式应该保留
        assert 'color:red' in result

    def test_compile_table_cell_style_without_paragraph_style(self):
        """测试xl-tc有style但xl-p没有style的情况"""
        xml = '<xl-tc style="align:center;font-size:14px"><xl-p>content</xl-p></xl-tc>'
        result = TableProcessor.compile(xml)
        
        # xl-p应该继承xl-tc的样式
        assert 'align:center' in result
        assert 'font-size:14px' in result

    def test_compile_table_cell_style_without_tc_style(self):
        """测试xl-tc没有style但xl-p有style的情况"""
        xml = '<xl-tc><xl-p style="color:red;font-size:12px">content</xl-p></xl-tc>'
        result = TableProcessor.compile(xml)
        
        # xl-p的样式应该保持不变
        assert 'color:red' in result
        assert 'font-size:12px' in result
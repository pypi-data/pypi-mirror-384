from xl_docx.compiler.processors.table import TableProcessor


class TestTableRowProcessor:
    """测试xl-row相关功能"""

    def test_compile_xl_row_with_grid_and_span(self):
        """测试编译带grid和span的xl-row标签"""
        xml = '''<xl-table grid="592/779/192/964/1290/1215/780/120/704/669/866/850/809">
    <xl-row height="482" align="center" span="3/5/2/3" text="检件名称/{{sample_name}}/操作指导书/{{record_number}}"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了正确的xl-tr结构
        assert '<xl-tr height="482">' in result
        assert '<xl-tc align="center" span="3" width="1563">' in result
        assert '<xl-tc align="center" span="5" width="4369">' in result
        assert '<xl-tc align="center" span="2" width="1373">' in result
        assert '<xl-tc align="center" span="3" width="2525">' in result
        
        # 检查内容是否正确
        assert '<xl-p>检件名称</xl-p>' in result
        assert '<xl-p>{{sample_name}}</xl-p>' in result
        assert '<xl-p>操作指导书</xl-p>' in result
        assert '<xl-p>{{record_number}}</xl-p>' in result

    def test_compile_xl_row_with_different_spans(self):
        """测试编译不同span组合的xl-row"""
        xml = '''<xl-table grid="100/200/300/400/500">
    <xl-row span="2/1/2" text="A/B/C"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查宽度计算：100+200=300, 300=300, 400+500=900
        assert 'span="2" width="300"' in result
        assert 'span="1" width="300"' in result
        assert 'span="2" width="900"' in result
        
        # 检查内容
        assert '<xl-p>A</xl-p>' in result
        assert '<xl-p>B</xl-p>' in result
        assert '<xl-p>C</xl-p>' in result

    def test_compile_xl_row_without_span(self):
        """测试编译没有span属性的xl-row标签"""
        xml = '''<xl-table grid="100/200/300/400/500">
    <xl-row text="A/B/C"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了5个xl-tc（对应grid中的5列）
        assert result.count('<xl-tc') == 5
        
        # 检查宽度：每个xl-tc对应grid中的一列
        assert 'width="100"' in result
        assert 'width="200"' in result
        assert 'width="300"' in result
        assert 'width="400"' in result
        assert 'width="500"' in result
        
        # 检查内容：前3个有内容，后2个为空
        assert '<xl-p>A</xl-p>' in result
        assert '<xl-p>B</xl-p>' in result
        assert '<xl-p>C</xl-p>' in result
        assert '<xl-p></xl-p>' in result  # 空的xl-p

    def test_compile_xl_row_without_span_insufficient_text(self):
        """测试编译没有span属性且text数据不足的xl-row标签"""
        xml = '''<xl-table grid="100/200/300/400/500">
    <xl-row text="A"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了5个xl-tc（对应grid中的5列）
        assert result.count('<xl-tc') == 5
        
        # 检查内容：只有第一个有内容，其他4个为空
        assert '<xl-p>A</xl-p>' in result
        # 应该有4个空的xl-p
        assert result.count('<xl-p></xl-p>') == 4

    def test_compile_xl_row_without_span_no_text(self):
        """测试编译没有span属性且没有text的xl-row标签"""
        xml = '''<xl-table grid="100/200/300/400/500">
    <xl-row/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了5个xl-tc（对应grid中的5列）
        assert result.count('<xl-tc') == 5
        
        # 检查内容：所有xl-tc都为空
        assert result.count('<xl-p></xl-p>') == 5

    def test_compile_xl_row_with_style_attribute(self):
        """测试编译带style属性的xl-row标签，style应该传递给每个xl-tc"""
        xml = '''<xl-table grid="592/779/192/964/1290/1215/780/120/704/669/866/850/809">
    <xl-row height="482" align="center" span="3/5/2/3" style="align:center" text="检件名称/{{sample_name}}/操作指导书/{{record_number}}"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了正确的xl-tr结构
        assert '<xl-tr height="482">' in result
        
        # 检查每个xl-tc都包含style属性
        assert 'style="align:center"' in result
        
        # 检查具体的xl-tc标签
        assert '<xl-tc align="center" span="3" width="1563" style="align:center">' in result
        assert '<xl-tc align="center" span="5" width="4369" style="align:center">' in result
        assert '<xl-tc align="center" span="2" width="1373" style="align:center">' in result
        assert '<xl-tc align="center" span="3" width="2525" style="align:center">' in result
        
        # 检查内容是否正确
        assert '<xl-p>检件名称</xl-p>' in result
        assert '<xl-p>{{sample_name}}</xl-p>' in result
        assert '<xl-p>操作指导书</xl-p>' in result
        assert '<xl-p>{{record_number}}</xl-p>' in result

    def test_compile_xl_row_with_style_and_align_conflict(self):
        """测试xl-row中同时有align和style属性时的处理"""
        xml = '''<xl-table grid="100/200/300">
    <xl-row align="left" style="align:right" span="1/2" text="A/B"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # style属性应该覆盖align属性
        assert 'style="align:right"' in result
        assert '<xl-tc align="left" span="1" width="100" style="align:right">' in result
        assert '<xl-tc align="left" span="2" width="500" style="align:right">' in result
        
        # 检查内容
        assert '<xl-p>A</xl-p>' in result
        assert '<xl-p>B</xl-p>' in result

    def test_compile_xl_row_without_span_with_style(self):
        """测试没有span属性但有style属性的xl-row标签"""
        xml = '''<xl-table grid="100/200/300/400/500">
    <xl-row style="align:center;font-size:14px" text="A/B/C"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了5个xl-tc（对应grid中的5列）
        assert result.count('<xl-tc') == 5
        
        # 检查每个xl-tc都包含style属性
        assert 'style="align:center;font-size:14px"' in result
        
        # 检查宽度：每个xl-tc对应grid中的一列
        assert 'width="100"' in result
        assert 'width="200"' in result
        assert 'width="300"' in result
        assert 'width="400"' in result
        assert 'width="500"' in result
        
        # 检查内容：前3个有内容，后2个为空
        assert '<xl-p>A</xl-p>' in result
        assert '<xl-p>B</xl-p>' in result
        assert '<xl-p>C</xl-p>' in result
        assert '<xl-p></xl-p>' in result  # 空的xl-p

    def test_compile_xl_row_with_newline_in_text(self):
        """测试xl-row中text属性包含换行符时的处理"""
        xml = '''<xl-table grid="100/200/300">
    <xl-row text="你好\n啊/B/C"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了3个xl-tc（对应grid中的3列）
        assert result.count('<xl-tc') == 3
        
        # 检查宽度
        assert 'width="100"' in result
        assert 'width="200"' in result
        assert 'width="300"' in result
        
        # 检查内容：第一个单元格应该包含两个xl-p（你好和啊），第二个和第三个单元格各有一个xl-p
        assert '<xl-p>你好</xl-p>' in result
        assert '<xl-p>啊</xl-p>' in result
        assert '<xl-p>B</xl-p>' in result
        assert '<xl-p>C</xl-p>' in result

    def test_compile_xl_row_with_multiple_newlines_in_text(self):
        """测试xl-row中text属性包含多个换行符时的处理"""
        xml = '''<xl-table grid="100/200/300">
    <xl-row text="第一行\n第二行\n第三行"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了3个xl-tc（对应grid中的3列）
        assert result.count('<xl-tc') == 3
        
        # 检查内容：第一个单元格应该包含三个xl-p
        assert '<xl-p>第一行</xl-p>' in result
        assert '<xl-p>第二行</xl-p>' in result
        assert '<xl-p>第三行</xl-p>' in result

    def test_compile_xl_row_with_newline_and_span(self):
        """测试xl-row中同时有换行符和span属性时的处理"""
        xml = '''<xl-table grid="100/200/300/400">
    <xl-row span="2/2" text="第一行\n第二行/第三行\n第四行"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了2个xl-tc（对应span="2/2"）
        assert result.count('<xl-tc') == 2
        
        # 检查宽度：第一个span=2，第二个span=2
        assert 'span="2" width="300"' in result  # 100+200=300
        assert 'span="2" width="700"' in result  # 300+400=700
        
        # 检查内容：第一个单元格包含两个xl-p，第二个单元格包含两个xl-p
        assert '<xl-p>第一行</xl-p>' in result
        assert '<xl-p>第二行</xl-p>' in result
        assert '<xl-p>第三行</xl-p>' in result
        assert '<xl-p>第四行</xl-p>' in result

    def test_compile_xl_row_with_empty_lines_in_text(self):
        """测试xl-row中text属性包含空行时的处理"""
        xml = '''<xl-table grid="100/200">
    <xl-row text="第一行\n\n第三行"/>
</xl-table>'''
        result = TableProcessor._process_xl_row(xml)
        
        # 检查是否生成了2个xl-tc（对应grid中的2列）
        assert result.count('<xl-tc') == 2
        
        # 检查内容：第一个单元格包含三个xl-p（包括空行）
        assert '<xl-p>第一行</xl-p>' in result
        assert '<xl-p></xl-p>' in result  # 空行
        assert '<xl-p>第三行</xl-p>' in result


        xml = '''
        <xl-table grid="592/779/192/964/1290/1215/780/120/704/669/866/850/809" style="align:center">
            <xl-row height="482" span="1/3/1/1/1/2/2/1/1" style="align:center" text="序号/检测部位及编号/缺陷位置、\n编号/波幅\nSL±dB/深度\mm/指示长度\nmm/单个缺陷面积\nmm2/占比/级别/备注"/>
            <xl-row height="482" text="以下空白"/>
        </xl-table>
        '''
        result = TableProcessor._process_xl_row(xml)
   
    def test_new(self):
        pass
        xml = '''
        <xl-table grid="592/779/192/964/1290/1215/780/120/704/669/866/850/809" style="align:center">
  <xl-row height="482" span="13" style="align:center;font-weight:bold" text="超声波检测结果（其它见超声波检测记录续页）"/>
'''
        result = TableProcessor.compile(xml)
        print('result~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(result)
        assert 'xl-row' not in result




        


        

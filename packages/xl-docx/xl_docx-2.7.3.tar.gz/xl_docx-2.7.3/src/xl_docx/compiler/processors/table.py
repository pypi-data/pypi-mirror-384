from xl_docx.compiler.processors.base import BaseProcessor
import re


class TableProcessor(BaseProcessor):
    """处理表格相关的XML标签"""
    
    # 正则表达式模式常量，提高可读性
    XL_TABLE_PATTERN = r'''
        <xl-table                    # 开始标签
        ([^>]*)                     # 所有属性
        >                           # 标签结束
        (.*?)                       # 内容（非贪婪匹配）
        </xl-table>                 # 结束标签
    '''
    
    XL_TH_PATTERN = r'''
        <xl-th                       # 开始标签
        ([^>]*)                     # 属性
        >                           # 标签结束
        (.*?)                       # 内容（非贪婪匹配）
        </xl-th>                    # 结束标签
    '''
    
    XL_TR_PATTERN = r'''
        <xl-tr                       # 开始标签
        ([^>]*)                     # 属性
        >                           # 标签结束
        (.*?)                       # 内容（非贪婪匹配）
        </xl-tr>                    # 结束标签
    '''
    
    XL_ROW_PATTERN = r'''
        <xl-row                      # 开始标签
        ([^>]*)                     # 属性
        (?:/>|>.*?</xl-row>)        # 自闭合标签或完整标签
    '''
    
    XL_TC_PATTERN = r'''
        <xl-tc                       # 开始标签
        ([^>]*)                     # 属性
        >                           # 标签结束
        (.*?)                       # 内容（非贪婪匹配）
        </xl-tc>                    # 结束标签
    '''
    
    XL_P_PATTERN = r'''
        <xl-p                       # 开始标签
        [^>]*>                      # 其他属性
        .*?                         # 内容（非贪婪匹配）
        </xl-p>                     # 结束标签
    '''
    
    # Word文档相关模式
    W_TBL_PATTERN = r'<w:tbl>.*?</w:tbl>'
    W_TR_PATTERN = r'<w:tr(?!Pr)[^>]*>(.*?)</w:tr>'
    W_TC_PATTERN = r'<w:tc>(.*?)</w:tc>'
    W_TBLGRID_PATTERN = r'<w:tblGrid>(.*?)</w:tblGrid>'
    W_GRIDCOL_PATTERN = r'<w:gridCol\s+w:w="([^"]+)"/>'

    # Word文档属性模式
    W_JC_PATTERN = r'<w:jc\s+w:val="([^"]+)"/>'
    W_TBLBORDERS_PATTERN = r'<w:tblBorders>(.*?)</w:tblBorders>'
    W_TRPR_PATTERN = r'<w:trPr>(.*?)</w:trPr>'
    W_TRHEIGHT_PATTERN = r'<w:trHeight[^>]*?w:val="([^"]+)"[^>]*?/>'
    W_TCW_PATTERN = r'<w:tcW.*w:w="([^"]+)".*/>'
    W_GRIDSPAN_PATTERN = r'<w:gridSpan\s+w:val="([^"]+)"/>'
    W_VALIGN_PATTERN = r'<w:vAlign\s+w:val="([^"]+)"/>'
    W_VMERGE_PATTERN = r'<w:vMerge(?:\s+w:val="([^"]+)")?/>'
    W_TCPR_CONTENT_PATTERN = r'<w:tc>.*?<w:tcPr>.*?</w:tcPr>(.*?)</w:tc>'
    
    # 边框相关模式
    BORDER_TOP_PATTERN = r'<w:top[^>]*w:val="([^"]+)"/>'
    BORDER_BOTTOM_PATTERN = r'<w:bottom[^>]*w:val="([^"]+)"/>'
    BORDER_LEFT_PATTERN = r'<w:left[^>]*w:val="([^"]+)"/>'
    BORDER_RIGHT_PATTERN = r'<w:right[^>]*w:val="([^"]+)"/>'
    BORDER_SIZE_ZERO_PATTERN = r'<w:(?:top|bottom|left|right)[^>]*w:sz="0"[^>]*/>'
    
    @classmethod
    def compile(cls, xml: str) -> str:
        xml = cls._process_xl_row(xml)
        xml = cls._process_xl_table(xml)
        xml = cls._process_xl_th(xml)
        xml = cls._process_xl_tr(xml)
        xml = cls._process_xl_tc(xml)
        return xml
        
    @classmethod
    def _process_xl_table(cls, xml: str) -> str:
        def process_table(match):
            attrs, content = match.groups()
            content = content.strip()
            
            # 解析属性
            style_str = None
            grid_str = None
            width_str = None
            span_str = None
            
            # 提取 style 属性
            style_match = re.search(r'style="([^"]*)"', attrs)
            if style_match:
                style_str = style_match.group(1)
            
            # 提取 grid 属性
            grid_match = re.search(r'grid="([^"]*)"', attrs)
            if grid_match:
                grid_str = grid_match.group(1)
            
            # 提取 width 属性
            width_match = re.search(r'width="([^"]*)"', attrs)
            if width_match:
                width_str = width_match.group(1)
            
            # 提取 span 属性
            span_match = re.search(r'span="([^"]*)"', attrs)
            if span_match:
                span_str = span_match.group(1)
            
            # 解析样式
            styles = cls._parse_style_str(style_str) if style_str else {}
            tbl_props_str = ''
            
            # 处理对齐方式
            if 'align' in styles:
                tbl_props_str += f'<w:jc w:val="{styles["align"]}"/>'
            
            # 处理边框样式
            if styles.get('border') == 'none':
                tbl_props_str += '''<w:tblBorders>
                <w:top w:color="auto" w:space="0" w:sz="0" w:val="none"/>
                <w:left w:color="auto" w:space="0" w:sz="0" w:val="none"/>
                <w:bottom w:color="auto" w:space="0" w:sz="0" w:val="none"/>
                <w:right w:color="auto" w:space="0" w:sz="0" w:val="none"/>
                <w:insideH w:color="auto" w:space="0" w:sz="0" w:val="none"/>
                <w:insideV w:color="auto" w:space="0" w:sz="0" w:val="none"/>
            </w:tblBorders>'''
            else:
                tbl_props_str += '''<w:tblBorders>
                    <w:top w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                    <w:left w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                    <w:bottom w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                    <w:right w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                    <w:insideH w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                    <w:insideV w:color="auto" w:space="0" w:sz="4" w:val="single"/>
                </w:tblBorders>'''
            
            # 处理左边距设置
            margin_left = styles.get('margin-left', '0')
            tbl_props_str += f'<w:tblInd w:w="{margin_left}" w:type="dxa"/>'
            
            # 处理表格宽度
            if width_str:
                tbl_props_str += f'<w:tblW w:w="{width_str}" w:type="dxa"/>'
            else:
                tbl_props_str += '<w:tblW w:type="auto" w:w="0"/>'
            
            # 添加单元格边距设置
            padding_top = styles.get('padding-top', '0')
            padding_bottom = styles.get('padding-bottom', '0')
            padding_left = styles.get('padding-left', '100')
            padding_right = styles.get('padding-right', '100')
            
            tbl_props_str += f'''
                <w:tblCellMar>
                    <w:top w:type="dxa" w:w="{padding_top}"/>
                    <w:left w:type="dxa" w:w="{padding_left}"/>
                    <w:bottom w:type="dxa" w:w="{padding_bottom}"/>
                    <w:right w:type="dxa" w:w="{padding_right}"/>
                </w:tblCellMar>
            '''
            
            # 处理列宽设置
            tbl_grid_str = ''
            if span_str and width_str:
                # span属性优先，根据span和width自动计算grid
                calculated_grid = cls.calculate_grid_from_span(width_str, span_str)
                if calculated_grid:
                    col_widths = calculated_grid.split('/')
                    tbl_grid_str = '<w:tblGrid>'
                    for width in col_widths:
                        tbl_grid_str += f'<w:gridCol w:w="{width}"/>'
                    tbl_grid_str += '</w:tblGrid>'
            elif grid_str:
                # 如果没有span属性，使用grid属性
                col_widths = grid_str.split('/')
                tbl_grid_str = '<w:tblGrid>'
                for width in col_widths:
                    tbl_grid_str += f'<w:gridCol w:w="{width}"/>'
                tbl_grid_str += '</w:tblGrid>'
            
            return f'''<w:tbl><w:tblPr>{tbl_props_str}</w:tblPr>{tbl_grid_str}{content}</w:tbl>'''
            
        return cls._process_tag(xml, cls.XL_TABLE_PATTERN, process_table)

    @classmethod
    def _process_xl_th(cls, xml: str) -> str:
        def process_th(match):
            attrs, content = match.groups()
            return f'<xl-tr header="1" {attrs}>{content}</xl-tr>'
            
        return cls._process_tag(xml, cls.XL_TH_PATTERN, process_th)
    
    @classmethod
    def _process_xl_row(cls, xml: str) -> str:
        def process_row(match):
            attrs = match.group(1)
            
            # 提取属性
            height = cls._extract_attr(attrs, 'height')
            align = cls._extract_attr(attrs, 'align')
            style = cls._extract_attr(attrs, 'style')
            span_str = cls._extract_attr(attrs, 'span')
            text_str = cls._extract_attr(attrs, 'text')
            
            # 如果没有指定align，使用默认值center
            if not align:
                align = 'center'
            
            # 获取父级table的grid信息
            # 需要在整个xml中查找包含当前xl-row的table
            full_match = match.group(0)
            # 从当前位置向前查找最近的xl-table标签
            start_pos = match.start()
            table_start = xml.rfind('<xl-table', 0, start_pos)
            if table_start == -1:
                return match.group(0)
            
            # 找到对应的table标签
            table_end = xml.find('>', table_start)
            if table_end == -1:
                return match.group(0)
            
            table_tag = xml[table_start:table_end + 1]
            
            # 首先尝试获取grid属性
            grid_match = re.search(r'grid="([^"]*)"', table_tag)
            if grid_match:
                grid_str = grid_match.group(1)
                grid_widths = [int(w) for w in grid_str.split('/')]
            else:
                # 如果没有grid属性，尝试使用span和width属性计算grid
                span_match = re.search(r'span="([^"]*)"', table_tag)
                width_match = re.search(r'width="([^"]*)"', table_tag)
                
                if span_match and width_match:
                    span_str = span_match.group(1)
                    width_str = width_match.group(1)
                    calculated_grid = cls.calculate_grid_from_span(width_str, span_str)
                    if calculated_grid:
                        grid_widths = [int(w) for w in calculated_grid.split('/')]
                    else:
                        return match.group(0)
                else:
                    return match.group(0)
            
            # 解析span和text
            if span_str and text_str:
                # 有span属性的情况
                spans = span_str.split('/')
                texts = text_str.split('/')
                
                # 生成xl-tc标签
                tc_elements = []
                current_col = 0
                
                for i, (span, text) in enumerate(zip(spans, texts)):
                    span_count = int(span)
                    # 计算宽度：从current_col开始，取span_count个grid宽度
                    width = sum(grid_widths[current_col:current_col + span_count])
                    
                    tc_attrs = f'align="{align}" span="{span}" width="{width}"'
                    if style:
                        tc_attrs += f' style="{style}"'
                    tc_content = cls._process_text_with_newlines(text)
                    tc_elements.append(f'<xl-tc {tc_attrs}>{tc_content}</xl-tc>')
                    
                    current_col += span_count
            elif text_str:
                # 没有span属性，但有text属性的情况
                texts = text_str.split('/')
                tc_elements = []
                
                for i, width in enumerate(grid_widths):
                    # 如果text数据不够，使用空字符串
                    text = texts[i] if i < len(texts) else ''
                    tc_attrs = f'align="{align}" width="{width}"'
                    if style:
                        tc_attrs += f' style="{style}"'
                    tc_content = cls._process_text_with_newlines(text)
                    tc_elements.append(f'<xl-tc {tc_attrs}>{tc_content}</xl-tc>')
            else:
                # 既没有span也没有text属性的情况
                tc_elements = []
                
                for width in grid_widths:
                    tc_attrs = f'align="{align}" width="{width}"'
                    if style:
                        tc_attrs += f' style="{style}"'
                    tc_content = '<xl-p></xl-p>'
                    tc_elements.append(f'<xl-tc {tc_attrs}>{tc_content}</xl-tc>')
            
            # 构建xl-tr标签
            tr_attrs = []
            if height:
                tr_attrs.append(f'height="{height}"')
            
            tr_attrs_str = ' '.join(tr_attrs)
            tr_content = ''.join(tc_elements)
            
            if tr_attrs_str:
                return f'<xl-tr {tr_attrs_str}>{tr_content}</xl-tr>'
            else:
                return f'<xl-tr>{tr_content}</xl-tr>'
                
        return cls._process_tag(xml, cls.XL_ROW_PATTERN, process_row)
    
    @classmethod
    def _process_xl_tr(cls, xml: str) -> str:
        def process_tr(match):
            attrs, content = match.groups()
            tr_props_str = ''
            
            # 处理表头属性
            tr_props_str += '<w:tblHeader/>' if 'header' in attrs else ''
            # 处理不可分割属性
            tr_props_str += '<w:cantSplit/>' if 'cant-split' in attrs else ''
            
            # 处理高度属性
            height_match = re.search(r'height="([^"]*)"', attrs)
            if height_match:
                height = height_match.group(1)
                tr_props_str += f'<w:trHeight w:val="{height}"/>'
            
            # 过滤掉已处理的属性
            other_attrs = re.findall(r'(\w+)="([^"]*)"', attrs)
            filtered_attrs = [(k, v) for k, v in other_attrs if k not in ['header', 'cant-split']]
            attrs_str = ' '.join([f'{k}="{v}"' for k, v in filtered_attrs])
            tr_props_str = f'<w:trPr>{tr_props_str}</w:trPr>'
            
            return f'<w:tr{" " + attrs_str if attrs_str else ""}>{tr_props_str}{content}</w:tr>'
            
        return cls._process_tag(xml, cls.XL_TR_PATTERN, process_tr)

    @classmethod
    def _process_xl_tc(cls, xml: str) -> str:
        def process_tc(match):
            attrs, content = match.groups()
            width, span, align, merge, border_top, border_bottom, border_left, border_right, style = cls._extract_attrs(
                attrs, ['width', 'span', 'align', 'merge', 'border-top', 'border-bottom', 'border-left', 'border-right', 'style']
            )

            # 如果align为None，设置默认值为center
            if align is None:
                align = 'center'

            # 如果内容不包含标签，包装为段落
            if not re.search(r'<[^>]+>', content):
                content = f'<xl-p>{content}</xl-p>'
            
            # 如果xl-tc有style属性，需要合并到xl-p的style中
            if style:
                content = cls._merge_tc_style_to_content(content, style)

            tc_props_str = ''
            # 添加各种单元格属性
            tc_props_str += f'<w:tcW w:type="dxa" w:w="{width}"/>' if width else ''
            tc_props_str += f'<w:gridSpan w:val="{span}"/>' if span else ''
            tc_props_str += f'<w:vAlign w:val="{align}"/>' if align else ''
            tc_props_str += '<w:vMerge w:val="restart"/>' if merge == 'start' else ('<w:vMerge/>' if merge else '')
            tc_border_str = '<w:tcBorders>'
            tc_border_str += f'<w:top w:val="nil"/>' if border_top == 'none' else ''
            tc_border_str += f'<w:bottom w:val="nil"/>' if border_bottom == 'none' else ''
            tc_border_str += f'<w:left w:val="nil"/>' if border_left == 'none' else ''
            tc_border_str += f'<w:right w:val="nil"/>' if border_right == 'none' else ''
            tc_border_str += '</w:tcBorders>'
            tc_props_str += tc_border_str
            return f'<w:tc>\n                    <w:tcPr>{tc_props_str}</w:tcPr>{content}</w:tc>'
        
        data = cls._process_tag(xml, cls.XL_TC_PATTERN, process_tc)
        return data
    
    @classmethod
    def _merge_tc_style_to_content(cls, content: str, tc_style: str) -> str:
        """将xl-tc的style属性合并到内容中的xl-p标签"""
        def merge_style_to_p(match):
            p_attrs = match.group(1)
            p_content = match.group(2)
            
            # 提取xl-p的现有style
            existing_style = cls._extract_attr(p_attrs, 'style')
            
            # 合并样式：tc_style优先，existing_style作为补充
            merged_style = cls._merge_styles(tc_style, existing_style)
            
            # 构建新的xl-p标签
            if merged_style:
                # 移除原有的style属性，添加合并后的style
                p_attrs_clean = re.sub(r'\s*style="[^"]*"', '', p_attrs)
                return f'<xl-p{p_attrs_clean} style="{merged_style}">{p_content}</xl-p>'
            else:
                return match.group(0)
        
        # 查找并处理所有xl-p标签
        return re.sub(r'<xl-p([^>]*)>(.*?)</xl-p>', merge_style_to_p, content, flags=re.DOTALL)
    
    @classmethod
    def _merge_styles(cls, style1: str, style2: str) -> str:
        """合并两个style字符串，style1优先"""
        if not style1 and not style2:
            return ''
        if not style1:
            return style2
        if not style2:
            return style1
        
        # 解析样式
        styles1 = dict(item.split(':') for item in style1.split(';') if ':' in item)
        styles2 = dict(item.split(':') for item in style2.split(';') if ':' in item)
        
        # style1优先，但保留style2中style1没有的属性
        merged_styles = styles2.copy()
        merged_styles.update(styles1)
        
        # 构建合并后的样式字符串
        return ';'.join(f'{k}:{v}' for k, v in merged_styles.items())
    
    @classmethod
    def _process_text_with_newlines(cls, text: str) -> str:
        """处理包含换行符的文本，将其分割为多个xl-p标签"""
        if not text:
            return '<xl-p></xl-p>'
        
        # 按换行符分割文本
        lines = text.split('\n')
        
        # 为每一行创建xl-p标签
        p_elements = []
        for line in lines:
            p_elements.append(f'<xl-p>{line}</xl-p>')
        
        return ''.join(p_elements)
    
    @classmethod
    def decompile(cls, xml: str) -> str:
        """将w:tbl标签转换为xl-table标签"""
        xml = cls.decompile_tbl(xml)
        xml = cls.decompile_tr(xml)
        xml = cls.decompile_tblgrid(xml)
        return xml

    @classmethod
    def decompile_tbl(cls, xml: str) -> str:
        def process_word_table(match):
            full_tbl = match.group(0)
            styles = {}
            grid_str = ''
            width_str = ''
            
            # 提取对齐方式
            align_match = re.search(cls.W_JC_PATTERN, full_tbl)
            if align_match:
                styles['align'] = align_match.group(1)
            
            # 提取边框样式
            border_match = re.search(cls.W_TBLBORDERS_PATTERN, full_tbl, re.DOTALL)
            if border_match:
                border_content = border_match.group(1)
                # 检查是否所有边框都是none
                if re.search(r'w:val="none"', border_content) and not re.search(r'w:val="single"', border_content):
                    styles['border'] = 'none'
            
            # 提取左边距设置
            tbl_ind_match = re.search(r'<w:tblInd\s+w:w="([^"]+)"\s+w:type="dxa"/>', full_tbl)
            if tbl_ind_match:
                margin_left = tbl_ind_match.group(1)
                if margin_left != '0':
                    styles['margin-left'] = margin_left
            
            # 提取单元格边距设置
            tbl_cell_mar_match = re.search(r'<w:tblCellMar>(.*?)</w:tblCellMar>', full_tbl, re.DOTALL)
            if tbl_cell_mar_match:
                cell_mar_content = tbl_cell_mar_match.group(1)
                
                # 提取各个方向的padding值
                padding_top_match = re.search(r'<w:top[^>]*w:w="([^"]+)"[^>]*/>', cell_mar_content)
                if padding_top_match and padding_top_match.group(1) != '0':
                    styles['padding-top'] = padding_top_match.group(1)
                
                padding_bottom_match = re.search(r'<w:bottom[^>]*w:w="([^"]+)"[^>]*/>', cell_mar_content)
                if padding_bottom_match and padding_bottom_match.group(1) != '0':
                    styles['padding-bottom'] = padding_bottom_match.group(1)
                
                padding_left_match = re.search(r'<w:left[^>]*w:w="([^"]+)"[^>]*/>', cell_mar_content)
                if padding_left_match and padding_left_match.group(1) not in ['0', '100']:
                    styles['padding-left'] = padding_left_match.group(1)
                
                padding_right_match = re.search(r'<w:right[^>]*w:w="([^"]+)"[^>]*/>', cell_mar_content)
                if padding_right_match and padding_right_match.group(1) not in ['0', '100']:
                    styles['padding-right'] = padding_right_match.group(1)
            
            # 提取表格宽度
            tbl_w_match = re.search(r'<w:tblW\s+w:w="([^"]+)"\s+w:type="dxa"/>', full_tbl)
            if tbl_w_match:
                width_str = tbl_w_match.group(1)
            
            # 提取列宽设置
            grid_match = re.search(cls.W_TBLGRID_PATTERN, full_tbl, re.DOTALL)
            if grid_match:
                grid_content = grid_match.group(1)
                col_widths = re.findall(cls.W_GRIDCOL_PATTERN, grid_content)
                if col_widths:
                    grid_str = '/'.join(col_widths)
            
            # 提取表格内容
            content_match = re.search(r'<w:tbl>.*?<w:tblPr>.*?</w:tblPr>(.*?)</w:tbl>', full_tbl, re.DOTALL)
            content = content_match.group(1) if content_match else ""
            
            # 移除tblGrid内容，避免重复处理
            content = re.sub(cls.W_TBLGRID_PATTERN, '', content, flags=re.DOTALL)
            
            style_str = cls._build_style_str(styles)
            grid_attr = f' grid="{grid_str}"' if grid_str else ""
            width_attr = f' width="{width_str}"' if width_str else ""
            style_attr = f' style="{style_str}"' if style_str else ""
            return f'<xl-table{width_attr}{grid_attr}{style_attr}>{content}</xl-table>'
        
        return cls._process_tag(xml, cls.W_TBL_PATTERN, process_word_table)

    @classmethod
    def decompile_tblgrid(cls, xml: str) -> str:
        """将单独的w:tblGrid标签转换为xl-table标签"""
        def process_tblgrid(match):
            grid_content = match.group(0)
            col_widths = re.findall(cls.W_GRIDCOL_PATTERN, grid_content)
            if col_widths:
                grid_str = '/'.join(col_widths)
                return f'<xl-table grid="{grid_str}"/>'
            return match.group(0)
        
        return cls._process_tag(xml, cls.W_TBLGRID_PATTERN, process_tblgrid)

    @classmethod
    def decompile_tr(cls, xml: str) -> str:
        def process_w_tr(match):
            full_tr = match.group(0)
            content = match.group(1)
            attrs = {}

            # 提取行属性
            tr_pr_match = re.search(cls.W_TRPR_PATTERN, full_tr, flags=re.DOTALL)
            tr_pr_str = tr_pr_match.group(1) if tr_pr_match else ''

            # 检查表头属性
            if '<w:tblHeader/>' in tr_pr_str:
                attrs['header'] = '1'
            
            # 检查不可分割属性
            if '<w:cantSplit/>' in tr_pr_str:
                attrs['cant-split'] = '1'
            
            # 提取高度属性
            height_match = re.search(cls.W_TRHEIGHT_PATTERN, tr_pr_str)
            if height_match:
                attrs['height'] = height_match.group(1)

            # 提取对齐属性
            align_match = re.search(cls.W_JC_PATTERN, tr_pr_str)
            if align_match:
                attrs['align'] = align_match.group(1)
            
            attrs_str = cls._build_attr_str(attrs)

            def process_w_tc(match):
                full_tc = match.group(0)

                tc_pr_match = re.search(r'<w:tcPr>(.*?)</w:tcPr>', full_tc, re.DOTALL)
                tc_pr_str = tc_pr_match.group(1) if tc_pr_match else ''

                attrs = {}
                
                width_match = re.search(r'<w:tcW.*w:w="([^"]+)".*/>', tc_pr_str)
                if width_match:
                    attrs['width'] = width_match.group(1)

                # 提取边框属性
                border_top = cls._extract(cls.BORDER_TOP_PATTERN, tc_pr_str)
                if border_top in ['nil', 'none'] or re.search(cls.BORDER_SIZE_ZERO_PATTERN, tc_pr_str):
                    attrs['border-top'] = 'none'

                border_bottom = cls._extract(cls.BORDER_BOTTOM_PATTERN, tc_pr_str)
                if border_bottom in ['nil', 'none'] or re.search(cls.BORDER_SIZE_ZERO_PATTERN, tc_pr_str):
                    attrs['border-bottom'] = 'none'

                border_left = cls._extract(cls.BORDER_LEFT_PATTERN, tc_pr_str)
                if border_left in ['nil', 'none'] or re.search(cls.BORDER_SIZE_ZERO_PATTERN, tc_pr_str):
                    attrs['border-left'] = 'none'

                border_right = cls._extract(cls.BORDER_RIGHT_PATTERN, tc_pr_str)
                if border_right in ['nil', 'none'] or re.search(cls.BORDER_SIZE_ZERO_PATTERN, tc_pr_str):
                    attrs['border-right'] = 'none'

                span_match = re.search(r'<w:gridSpan\s+w:val="([^"]+)"/>', tc_pr_str)
                if span_match:
                    attrs['span'] = span_match.group(1)
                
                align_match = re.search(r'<w:vAlign\s+w:val="([^"]+)"/>', tc_pr_str)
                if align_match:
                    attrs['align'] = align_match.group(1)
                
                vmerge_match = re.search(r'<w:vMerge(?:\s+w:val="([^"]+)")?/>', tc_pr_str)
                if vmerge_match:
                    val = vmerge_match.group(1)
                    if val == "restart":
                        attrs['merge'] = 'start'
                    else:
                        attrs['merge'] = 'continue'
                
                content_match = re.search(r'<w:tc>.*?<w:tcPr>.*?</w:tcPr>(.*?)</w:tc>', full_tc, re.DOTALL)
                content = content_match.group(1) if content_match else ""
                
                attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()]) if attrs else ""
                if attrs_str:
                    return f'<xl-tc {attrs_str}>{content}</xl-tc>'
                else:
                    return f'<xl-tc>{content}</xl-tc>'
        
            # 处理所有表格单元格
            matches = list(re.finditer(cls.W_TC_PATTERN, content, re.DOTALL))
            content = ''
            for match in matches:
                full_tc = match.group(0)
                full_tc = cls._process_tag(full_tc, cls.W_TC_PATTERN, process_w_tc)
                content += full_tc
            
            # 根据是否为表头返回不同的标签
            if 'header' in attrs:
                if attrs_str:
                    return f'<xl-th {attrs_str}>{content}</xl-th>'
                else:
                    return f'<xl-th>{content}</xl-th>'
            else:
                if attrs_str:
                    return f'<xl-tr {attrs_str}>{content}</xl-tr>'
                else:
                    return f'<xl-tr>{content}</xl-tr>'
        
        return cls._process_tag(xml, cls.W_TR_PATTERN, process_w_tr)
    
    @classmethod
    def calculate_grid_from_span(cls, width_str: str, span_str: str) -> str:
        """
        根据width和span属性计算grid值
        
        Args:
            width_str: 表格宽度，如 "1000pt" 或 "1000"
            span_str: span比例，如 "10/25/65"
            
        Returns:
            计算后的grid字符串，如 "100/250/650"
        """
        if not width_str or not span_str:
            return ""
        
        # 提取宽度数值，去除单位
        width_value = float(width_str.replace('pt', ''))
        
        # 解析span比例
        span_ratios = [float(ratio) for ratio in span_str.split('/')]
        total_ratio = sum(span_ratios)
        
        # 计算每列的宽度
        col_widths = []
        for ratio in span_ratios:
            calculated_width = round(width_value * ratio / total_ratio)
            col_widths.append(str(calculated_width))
        
        return '/'.join(col_widths)

    @classmethod
    def _extract_attr(cls, attrs: str, attr_name: str) -> str:
        """从属性字符串中提取指定属性的值"""
        match = re.search(rf'{attr_name}="([^"]*)"', attrs)
        if match:
            value = match.group(1)
            # 处理XML转义字符
            value = value.replace('\\n', '\n')
            value = value.replace('\\t', '\t')
            value = value.replace('\\r', '\r')
            return value
        return None

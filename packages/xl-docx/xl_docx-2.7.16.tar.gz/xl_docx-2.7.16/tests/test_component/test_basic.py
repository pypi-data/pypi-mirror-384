from xl_docx.compiler.processors.component import ComponentProcessor



def test_new():
    processor = ComponentProcessor()
    xml = '<xl-check condition="2>1">content</xl-check>'
    result = processor.compile(xml)
    expected = '($ if 2>1 $)content($ endif $)'
    assert result == expected


def test_basic_component():
    """Test basic component functionality"""
    # Process XML
    processor = ComponentProcessor()

    xml = '''<xl-text content="123" style="color: red"/>'''
    result = processor.compile(xml)
    assert result == '<xl-p style="color: red">123</xl-p>'


    xml = '''<xl-text content="123"/>'''
    result = processor.compile(xml)
    assert result == '<xl-p>123</xl-p>'


    xml = '''<xl-text style="color: red"/>'''
    result = processor.compile(xml)
    assert result == '<xl-p style="color: red"></xl-p>'

    
    
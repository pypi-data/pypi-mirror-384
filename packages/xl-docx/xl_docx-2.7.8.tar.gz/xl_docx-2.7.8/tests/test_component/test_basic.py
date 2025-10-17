from xl_docx.mixins.component import ComponentMixin



def test_new():
    processor = ComponentMixin()
    xml = '<xl-check condition="2>1">content</xl-check>'
    result = processor.process_components(xml)
    expected = '($ if 2>1 $)content($ endif $)'
    assert result == expected


def test_basic_component():
    """Test basic component functionality"""
    # Process XML
    processor = ComponentMixin()

    xml = '''<xl-text content="123" style="color: red"/>'''
    result = processor.process_components(xml)
    assert result == '<xl-p style="color: red">123</xl-p>'


    xml = '''<xl-text content="123"/>'''
    result = processor.process_components(xml)
    assert result == '<xl-p>123</xl-p>'


    xml = '''<xl-text style="color: red"/>'''
    result = processor.process_components(xml)
    assert result == '<xl-p style="color: red"></xl-p>'

    
    
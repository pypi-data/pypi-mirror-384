from xl_docx.mixins.component import ComponentMixin



def test_new():
    ComponentMixin._load_all_components()
    xml = '<xl-check condition="2>1">content</xl-check>'
    result = ComponentMixin.process_components(xml)
    expected = '($ if 2>1 $)content($ endif $)'
    assert result == expected


def test_basic_component():
    """Test basic component functionality"""
    # Process XML
    ComponentMixin._load_all_components()

    xml = '''<xl-text content="123" style="color: red"/>'''
    result = ComponentMixin.process_components(xml)
    assert result == '<xl-p style="color: red">123</xl-p>'


    xml = '''<xl-text content="123"/>'''
    result = ComponentMixin.process_components(xml)
    assert result == '<xl-p>123</xl-p>'


    xml = '''<xl-text style="color: red"/>'''
    result = ComponentMixin.process_components(xml)
    assert result == '<xl-p style="color: red"></xl-p>'

    
    
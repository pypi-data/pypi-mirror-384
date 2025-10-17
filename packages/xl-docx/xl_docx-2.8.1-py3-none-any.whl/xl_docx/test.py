#!/usr/bin/env python3
"""
Example usage of the automate_word function from word_mcp module.
This file demonstrates how to use the word automation functionality.
"""

from word_mcp import automate_word


def main():
    """
    Example usage of the automate_word function.
    """
    try:
        result = automate_word(
            command="创建一份租房合同，字数在1500字以上，中文字体为SimSun，非中文字体为Times New Roman，合同标题字体大小为30号， 除了合同标题外，其他文字字体大小设为22，要求排版合理美观，出租方是张三，身份证号是随机的身份证号，承租方是李四，身份证号是随机身份证号",
            template_path="h.docx",  # Update with your template path
            output_path="output/contract.docx"  # Update with your desired output path
        )
        print("Document created successfully!")
        print(f"Output: {result['output_path']}")
        print(f"Generated XML: {result['generated_xml']}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

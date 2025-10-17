
import os
from dotenv import load_dotenv
from xl_docx.sheet import Sheet
import openai
import re

# Load environment variables from .env file
load_dotenv()

def automate_word(command: str, template_path: str, output_path: str):
    """
    Receives a natural language command to automate a Word document.
    
    Args:
        command (str): Natural language command for document automation
        template_path (str): Path to the template .docx file
        output_path (str): Path where the output .docx file will be saved
    
    Returns:
        dict: Result containing status, output_path, and generated_xml
    
    Raises:
        ValueError: If API key is missing or template file not found
        Exception: For other unexpected errors
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set it in the .env file.")

    try:
        # 1. Initialize the Sheet object with the template
        if not os.path.exists(template_path):
            raise ValueError(f"Template file not found: {template_path}")
        
        sheet = Sheet(tpl_path=template_path)

        # 2. Load the XML syntax reference from external file
        reference_file_path = os.path.join(os.path.dirname(__file__), "xml_syntax_reference.txt")
        try:
            with open(reference_file_path, 'r', encoding='utf-8') as f:
                xml_reference = f.read().strip()
        except FileNotFoundError:
            raise ValueError(f"XML syntax reference file not found: {reference_file_path}")
        
        # 3. Define the AI's "manual" for the custom XML syntax
        system_prompt = f"""
        You are an expert assistant that generates a custom XML structure for a .docx file based on user commands.
        Your output MUST be only the raw XML, with no explanations, comments, or markdown formatting.
        The user will provide a command, and you will translate it into the following XML format.

        {xml_reference}

        Now, generate the XML for the user's command. Remember, ONLY output the XML code.
        """

        # 4. Call OpenAI API to generate the xl-xml
        client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.laozhang.ai/v1"
        )
        response = client.chat.completions.create(
            model="qwen-turbo-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            temperature=0.1,
        )
        ai_generated_xml = response.choices[0].message.content.strip()
        
        # Clean up potential markdown code fences
        if ai_generated_xml.startswith("```xml"):
            ai_generated_xml = ai_generated_xml[6:]
        if ai_generated_xml.startswith("```"):
            ai_generated_xml = ai_generated_xml[3:]
        if ai_generated_xml.endswith("```"):
            ai_generated_xml = ai_generated_xml[:-3]
        ai_generated_xml = ai_generated_xml.strip()


        # 5. Compile the AI-generated XML to WordprocessingML
        wrapped_xml = f"<root>{ai_generated_xml}</root>"
        compiled_body_content = sheet.render_template(wrapped_xml, {})
        compiled_body_content = compiled_body_content.replace("<root>", "").replace("</root>", "").strip()
        doc_xml_str = sheet['word/document.xml'].decode('utf-8')
        
        # Find the body tag and replace its content
        body_pattern = re.compile(r'(<w:body>)(.*)(</w:body>)', re.DOTALL)
        if body_pattern.search(doc_xml_str):
            new_doc_xml_str = body_pattern.sub(f'{compiled_body_content}', doc_xml_str)
        else:
            # If no body tag, something is wrong with the template
            raise ValueError("Invalid template: <w:body> tag not found in document.xml.")

        sheet['word/document.xml'] = new_doc_xml_str.encode('utf-8')

        # 7. Save the final document
        sheet.save(output_path)

        return {
            "status": "success",
            "output_path": output_path,
            "generated_xml": ai_generated_xml
        }

    except ValueError as e:
        # Re-raise ValueError exceptions
        raise e
    except Exception as e:
        # Catch any other error and raise as generic exception
        raise Exception(f"An unexpected error occurred: {str(e)}")



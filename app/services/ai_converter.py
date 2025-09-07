from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIConverter:
    def __init__(self):
        """Initialize the AI converter with OpenAI credentials"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        self.client = OpenAI(
            api_key=self.api_key
        )

    async def convert_to_markdown(self, doc_content: Dict) -> str:
        """
        Convert Google Docs content to Markdown using OpenAI's GPT-4o-mini model
        
        Args:
            doc_content (Dict): The Google Doc content dictionary
            
        Returns:
            str: Converted Markdown content
        """
        try:
            # Extract the text content
            if isinstance(doc_content, dict):
                content = self._extract_structured_content(doc_content)
            else:
                content = str(doc_content)

            # Prepare the prompt for GPT
            system_prompt = """
            You are a document converter that transforms Google Docs content into clean, well-formatted Markdown.
            Follow these rules:
            1. Maintain the document structure (headings, lists, etc.)
            2. Preserve all content and formatting
            3. Use proper Markdown syntax
            4. Handle special elements like code blocks, tables, and links correctly
            5. Return only the converted Markdown without any explanations
            """

            user_prompt = f"Convert this Google Docs content to Markdown:\n\n{content}"

            # Make API call to OpenAI
            response = await self._call_openai(system_prompt, user_prompt)
            
            return response

        except Exception as e:
            logger.error(f"Error in convert_to_markdown: {str(e)}")
            raise

    def _extract_structured_content(self, doc_content: Dict) -> str:
        """
        Extract structured content from Google Docs JSON
        
        Args:
            doc_content (Dict): The Google Doc content dictionary
            
        Returns:
            str: Extracted text content with basic structure
        """
        try:
            content = []
            body = doc_content.get('body', {})
            
            for element in body.get('content', []):
                # Handle paragraphs
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    
                    # Check for heading level
                    style = paragraph.get('paragraphStyle', {}).get('namedStyleType', '')
                    heading_level = 0
                    if 'HEADING' in style:
                        try:
                            heading_level = int(style.split('_')[1])
                        except (IndexError, ValueError):
                            heading_level = 0

                    # Extract text
                    text_elements = []
                    for elem in paragraph.get('elements', []):
                        if 'textRun' in elem:
                            text = elem['textRun'].get('content', '')
                            text_elements.append(text)
                    
                    text = ''.join(text_elements)
                    
                    # Add appropriate markdown syntax
                    if heading_level > 0:
                        content.append(f"{'#' * heading_level} {text}")
                    else:
                        content.append(text)

                # Handle tables (simplified)
                elif 'table' in element:
                    content.append("\n[Table content here]\n")

            return '\n'.join(content)

        except Exception as e:
            logger.error(f"Error in _extract_structured_content: {str(e)}")
            return str(doc_content)

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Make an API call to OpenAI
        
        Args:
            system_prompt (str): The system instruction
            user_prompt (str): The user content to convert
            
        Returns:
            str: The converted markdown content
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as requested
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error in OpenAI API call: {str(e)}")
            raise

    async def check_service(self):
        """Check if AI converter service is working"""
        try:
            # Test with a simple conversion to verify the service works
            test_content = "Test content for service check"
            system_prompt = "Convert this to markdown:"
            user_prompt = test_content
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            # If we get a response, the service is working
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI converter service check failed: {str(e)}")
            return False

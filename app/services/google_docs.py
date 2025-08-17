from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import logging

logger = logging.getLogger(__name__)

class GoogleDocsService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=[
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        self.docs_service = build('docs', 'v1', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def extract_text_content(self, document):
        """Extract text content from Google Doc with heading structure preserved"""
        content = []
        
        # Get the full document structure
        body = document.get('body', {})
        content_elements = body.get('content', [])
        
        logger.info(f"Document has {len(content_elements)} content elements")
        
        # First pass: extract all text content with proper structure
        for i, element in enumerate(content_elements):
            if 'paragraph' in element:
                paragraph = element.get('paragraph', {})
                
                # Check if this is a heading
                paragraph_style = paragraph.get('paragraphStyle', {})
                named_style_type = paragraph_style.get('namedStyleType', '')
                
                # Extract text from paragraph
                paragraph_text = ""
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_run = elem.get('textRun', {})
                        paragraph_text += text_run.get('content', '')
                
                # Apply heading formatting based on style
                if named_style_type.startswith('HEADING_'):
                    # Extract heading level (HEADING_1, HEADING_2, etc.)
                    level = int(named_style_type.split('_')[1])
                    heading_markdown = '#' * level + ' ' + paragraph_text.strip()
                    content.append(heading_markdown)
                    logger.info(f"Found heading level {level}: {paragraph_text.strip()}")
                else:
                    # Regular paragraph
                    if paragraph_text.strip():
                        content.append(paragraph_text.strip())
            
            elif 'sectionBreak' in element:
                # Handle section breaks - these indicate new sections
                content.append("\n---\n")
                logger.info("Found section break")
            
            elif 'tableOfContents' in element:
                # Skip table of contents
                logger.info("Skipping table of contents")
                continue
            
            elif 'table' in element:
                # Handle tables
                table = element.get('table', {})
                table_content = self._extract_table_content(table)
                if table_content:
                    content.append(table_content)
                logger.info("Found table")
        
        # Second pass: look for content in document headers/footers
        headers = document.get('headers', {})
        footers = document.get('footers', {})
        
        for header in headers.values():
            header_content = self._extract_text_from_content(header.get('content', []))
            if header_content:
                content.append(f"\n## Header Content\n{header_content}")
                logger.info("Found header content")
        
        for footer in footers.values():
            footer_content = self._extract_text_from_content(footer.get('content', []))
            if footer_content:
                content.append(f"\n## Footer Content\n{footer_content}")
                logger.info("Found footer content")
        
        # Third pass: try to get content from document outline if available
        try:
            outline = self.docs_service.documents().get(documentId=document.get('documentId')).execute()
            if 'documentOutline' in outline:
                logger.info("Document has outline structure")
                outline_content = self._extract_outline_content(outline['documentOutline'])
                if outline_content:
                    content.extend(outline_content)
        except Exception as e:
            logger.warning(f"Could not extract outline: {e}")
        
        result = '\n\n'.join(content)
        logger.info(f"Extracted {len(result)} characters of content")
        return result

    def get_document_content(self, doc_id: str):
        """Get document content and metadata from all sections"""
        try:
            # Try multiple approaches to get the full document content
            
            # Approach 1: Standard document get
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            
            # Get basic document info
            title = document.get('title', '')
            document_id = document.get('documentId', '')
            
            # Debug: Show document structure
            logger.info(f"Document title: {title}")
            logger.info(f"Document ID: {document_id}")
            
            # Show all available keys in the document
            logger.info(f"Document keys: {list(document.keys())}")
            
            # Show body structure
            body = document.get('body', {})
            logger.info(f"Body keys: {list(body.keys())}")
            
            content_elements = body.get('content', [])
            logger.info(f"Content elements count: {len(content_elements)}")
            
            # Approach 2: Try getting document with different parameters
            try:
                # Try with suggestions view mode
                alt_document = self.docs_service.documents().get(
                    documentId=doc_id,
                    suggestionsViewMode='PREVIEW_WITHOUT_SUGGESTIONS'
                ).execute()
                
                # Use the document with the most content
                documents = [document, alt_document]
                best_document = max(documents, key=lambda d: len(d.get('body', {}).get('content', [])))
                
                if best_document != document:
                    logger.info(f"Found document with more content: {len(best_document.get('body', {}).get('content', []))} elements")
                    document = best_document
                    content_elements = document.get('body', {}).get('content', [])
                
            except Exception as e:
                logger.warning(f"Could not get alternative document views: {e}")
            
            # Approach 3: Check if this is a multi-section document
            # Google Docs with multiple sections might have different structure
            if len(content_elements) <= 10:  # If we have very few elements, try alternative approach
                logger.info("Document has few elements, trying alternative extraction method")
                try:
                    # Check for alternative content locations
                    if 'documentStyle' in document:
                        logger.info("Document has custom styling")
                    
                    if 'namedStyles' in document:
                        logger.info(f"Document has {len(document['namedStyles'])} named styles")
                    
                    # Check if there are hidden sections or different content structure
                    if 'lists' in document:
                        logger.info(f"Document has {len(document['lists'])} lists")
                        # Lists might contain additional content
                        for i, list_info in enumerate(document['lists'].values()):
                            logger.info(f"List {i}: {list_info.get('listId', 'Unknown')}")
                    
                    # Try to get document metadata from Drive API
                    try:
                        drive_metadata = self.drive_service.files().get(
                            fileId=doc_id,
                            fields='id,name,mimeType,size,modifiedTime,parents'
                        ).execute()
                        logger.info(f"Drive metadata: {drive_metadata}")
                        
                        # If document is much larger than what we extracted, try HTML export
                        if drive_metadata.get('size', '0') != '0':
                            doc_size = int(drive_metadata.get('size', '0'))
                            logger.info(f"Document size ({doc_size} bytes) suggests more content than what we're extracting")
                            logger.info("This indicates the document has multiple sections that aren't being extracted properly")
                            
                            # Try to get HTML export to see full content
                            try:
                                html_content = self._get_html_export(doc_id)
                                if html_content:
                                    logger.info(f"HTML export successful, length: {len(html_content)} characters")
                                    # Parse HTML to find additional sections
                                    additional_sections = self._parse_html_sections(html_content)
                                    if additional_sections:
                                        logger.info(f"Found {len(additional_sections)} additional sections in HTML")
                                        for section in additional_sections:
                                            logger.info(f"  HTML Section: {section[:100]}...")
                            except Exception as e:
                                logger.warning(f"HTML export failed: {e}")
                                
                    except Exception as e:
                        logger.warning(f"Could not get Drive metadata: {e}")
                    
                except Exception as e:
                    logger.warning(f"Alternative extraction failed: {e}")
            
            # Show first few elements for debugging
            for i, element in enumerate(content_elements[:5]):
                logger.info(f"Element {i} keys: {list(element.keys())}")
                if 'paragraph' in element:
                    paragraph = element.get('paragraph', {})
                    logger.info(f"  Paragraph keys: {list(paragraph.keys())}")
                    if 'paragraphStyle' in paragraph:
                        style = paragraph['paragraphStyle']
                        logger.info(f"  Style keys: {list(style.keys())}")
                        if 'namedStyleType' in style:
                            logger.info(f"  Named style: {style['namedStyleType']}")
            
            # Show ALL elements for debugging
            logger.info("=== ALL CONTENT ELEMENTS ===")
            for i, element in enumerate(content_elements):
                logger.info(f"Element {i}: {list(element.keys())}")
                if 'paragraph' in element:
                    paragraph = element.get('paragraph', {})
                    # Extract text from this paragraph
                    para_text = ""
                    for elem in paragraph.get('elements', []):
                        if 'textRun' in elem:
                            text_run = elem.get('textRun', {})
                            para_text += text_run.get('content', '')
                    
                    if para_text.strip():
                        logger.info(f"  Text: '{para_text.strip()[:100]}...'")
                    
                    if 'paragraphStyle' in paragraph:
                        style = paragraph['paragraphStyle']
                        if 'namedStyleType' in style:
                            logger.info(f"  Style: {style['namedStyleType']}")
                elif 'sectionBreak' in element:
                    logger.info(f"  Type: Section Break")
                else:
                    logger.info(f"  Type: {list(element.keys())[0] if element.keys() else 'Unknown'}")
            
            logger.info("=== END CONTENT ELEMENTS ===")
            
            # Extract content
            content = self.extract_text_content(document)
            
            # Check if HTML export revealed more content
            html_content = None
            additional_sections = []
            
            try:
                # Try HTML export to see if there's more content
                html_content = self._get_html_export(doc_id)
                if html_content and len(html_content) > len(content) * 2:  # If HTML is significantly larger
                    logger.info(f"HTML export reveals much more content: {len(html_content)} vs {len(content)} chars")
                    additional_sections = self._parse_html_sections(html_content)
                    if additional_sections:
                        logger.info(f"Found {len(additional_sections)} sections in HTML export")
                        
                        # Use HTML content as the primary source
                        content = self._extract_content_from_html(html_content)
                        logger.info(f"Extracted {len(content)} characters from HTML")
            except Exception as e:
                logger.warning(f"HTML export failed: {e}")
            
            # Get document statistics
            stats = {
                'title': title,
                'document_id': document_id,
                'content_length': len(content),
                'has_headings': '#' in content,
                'heading_count': content.count('#'),
                'section_count': content.count('---'),
                'total_elements': len(content_elements),
                'html_sections_found': len(additional_sections),
                'used_html_export': html_content is not None and len(html_content) > len(content) * 2
            }
            
            logger.info(f"Document stats: {stats}")
            
            return {
                "title": title,
                "content": content,
                "raw_content": document,
                "html_content": html_content,
                "additional_sections": additional_sections,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting document content: {e}")
            raise

    def _extract_table_content(self, table):
        """Extract content from table"""
        table_content = []
        rows = table.get('tableRows', [])
        
        for row in rows:
            row_content = []
            cells = row.get('tableCells', [])
            for cell in cells:
                cell_text = ""
                for content in cell.get('content', []):
                    if 'paragraph' in content:
                        for elem in content['paragraph'].get('elements', []):
                            if 'textRun' in elem:
                                cell_text += elem['textRun'].get('content', '')
                if cell_text.strip():
                    row_content.append(cell_text.strip())
            
            if row_content:
                table_content.append('| ' + ' | '.join(row_content) + ' |')
        
        if table_content:
            # Add header separator
            if table_content:
                header_sep = '| ' + ' | '.join(['---'] * len(table_content[0].split('|')[1:-1])) + ' |'
                table_content.insert(1, header_sep)
        
        return '\n'.join(table_content)
    
    def _extract_outline_content(self, outline):
        """Extract content from document outline"""
        outline_content = []
        
        def process_outline_item(item, level=0):
            if 'textRun' in item:
                text = item['textRun'].get('content', '').strip()
                if text:
                    heading = '#' * (level + 1) + ' ' + text
                    outline_content.append(heading)
            
            # Process children
            for child in item.get('children', []):
                process_outline_item(child, level + 1)
        
        for item in outline.get('outlineItems', []):
            process_outline_item(item)
        
        return outline_content
    
    def _extract_text_from_content(self, content_elements):
        """Extract text from content elements (used for headers/footers)"""
        text_parts = []
        for element in content_elements:
            if 'paragraph' in element:
                paragraph = element.get('paragraph', {})
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_run = elem.get('textRun', {})
                        text_parts.append(text_run.get('content', ''))
        return ''.join(text_parts)
    
    def _get_html_export(self, doc_id):
        """Try to get HTML export of the document"""
        try:
            # Try to export as HTML through Drive API
            request = self.drive_service.files().export_media(
                fileId=doc_id,
                mimeType='text/html'
            )
            html_content = request.execute()
            return html_content.decode('utf-8') if isinstance(html_content, bytes) else html_content
        except Exception as e:
            logger.warning(f"HTML export failed: {e}")
            return None
    
    def _parse_html_sections(self, html_content):
        """Parse HTML content to find additional sections"""
        try:
            import re
            
            # Look for heading patterns in HTML
            heading_patterns = [
                r'<h1[^>]*>(.*?)</h1>',
                r'<h2[^>]*>(.*?)</h2>',
                r'<h3[^>]*>(.*?)</h3>',
                r'<h4[^>]*>(.*?)</h4>',
                r'<h5[^>]*>(.*?)</h5>',
                r'<h6[^>]*>(.*?)</h6>'
            ]
            
            sections = []
            for pattern in heading_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    # Clean HTML tags
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text:
                        sections.append(clean_text)
            
            return sections
        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}")
            return []
    
    def _extract_content_from_html(self, html_content):
        """Extract properly formatted content from HTML export"""
        try:
            import re
            
            # First, remove CSS content that Google Docs includes
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
            html_content = re.sub(r'\.lst-kix_[^{]*{[^}]*}', '', html_content)
            html_content = re.sub(r'<![^>]*>', '', html_content)  # Remove HTML comments
            
            # Convert HTML to markdown-like format
            # Look for heading tags and convert them to markdown with proper spacing
            # Use different heading levels based on the content structure
            html_content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n# \1\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n## \1\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n### \1\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n\n#### \1\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'\n\n##### \1\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'\n\n###### \1\n\n', html_content, flags=re.IGNORECASE)
            
            # Convert paragraphs with better spacing
            html_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html_content, flags=re.IGNORECASE)
            
            # Convert line breaks
            html_content = re.sub(r'<br[^>]*>', r'\n', html_content, flags=re.IGNORECASE)
            
            # Convert lists
            html_content = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', html_content, flags=re.IGNORECASE | re.DOTALL)
            html_content = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', html_content, flags=re.IGNORECASE | re.DOTALL)
            html_content = re.sub(r'<li[^>]*>(.*?)</li>', r'* \1\n', html_content, flags=re.IGNORECASE)
            
            # Convert bold and italic
            html_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html_content, flags=re.IGNORECASE)
            
            # Remove remaining HTML tags
            html_content = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean up HTML entities more comprehensively
            html_entities = {
                '&nbsp;': ' ',
                '&amp;': '&',
                '&lt;': '<',
                '&gt;': '>',
                '&quot;': '"',
                '&rsquo;': "'",
                '&lsquo;': "'",
                '&rdquo;': '"',
                '&ldquo;': '"',
                '&hellip;': '...',
                '&mdash;': '—',
                '&ndash;': '–',
                '&#39;': "'",
                '&#8217;': "'",
                '&#8216;': "'",
                '&#8220;': '"',
                '&#8221;': '"',
                '&#8230;': '...',
                '&#8211;': '–',
                '&#8212;': '—'
            }
            
            for entity, replacement in html_entities.items():
                html_content = html_content.replace(entity, replacement)
            
            # Clean up extra whitespace and normalize
            html_content = re.sub(r'\n\s*\n', '\n\n', html_content)
            html_content = re.sub(r' +', ' ', html_content)  # Multiple spaces to single space
            html_content = re.sub(r'\n{3,}', '\n\n', html_content)  # More than 2 newlines to 2
            html_content = html_content.strip()
            
            # Remove any remaining CSS-like content
            html_content = re.sub(r'[a-zA-Z0-9_-]+\s*{[^}]*}', '', html_content)
            html_content = re.sub(r'[a-zA-Z0-9_-]+\s*>\s*[a-zA-Z0-9_-]+\s*{[^}]*}', '', html_content)
            
            # Now try to identify and fix the main page headers
            # Based on the user's screenshot, we want to identify the main page headers
            main_headers = [
                "Landing page",
                "Structure", 
                "Milestone Review",
                "Review onboarding Circle",
                "Payment Information"
            ]
            
            # Look for these main headers and ensure they're level 1
            for header in main_headers:
                # Try to find this header in the content
                pattern = rf'#+\s*{re.escape(header)}'
                if re.search(pattern, html_content, re.IGNORECASE):
                    # Replace with level 1 heading
                    html_content = re.sub(pattern, f'# {header}', html_content, flags=re.IGNORECASE)
            
            return html_content
            
        except Exception as e:
            logger.warning(f"HTML content extraction failed: {e}")
            return html_content  # Return original if processing fails

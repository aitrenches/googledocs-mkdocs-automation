import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NavigationSection:
    """Represents a navigation section with its content and metadata"""
    title: str
    level: int
    content: str
    file_path: str
    children: List['NavigationSection']
    metadata: Dict

class NavigationManager:
    """
    Manages MkDocs navigation structure based on Google Docs content
    Implements the Single Document with Sections approach
    """
    
    def __init__(self):
        # Default navigation templates
        self.navigation_templates = {
            "standard_docs": {
                "structure": [
                    {"title": "Home", "file": "index.md"},
                    {"title": "About", "file": "about/index.md"},
                    {"title": "Team", "file": "team/index.md"},
                    {"title": "Operations", "file": "operations/index.md"},
                    {"title": "Tools", "file": "tools/index.md"},
                    {"title": "FAQ", "file": "faq.md"}
                ]
            },
            "technical_docs": {
                "structure": [
                    {"title": "Overview", "file": "index.md"},
                    {"title": "Getting Started", "file": "getting-started.md"},
                    {"title": "API Reference", "file": "api/index.md"},
                    {"title": "Examples", "file": "examples/index.md"},
                    {"title": "Configuration", "file": "configuration.md"},
                    {"title": "Troubleshooting", "file": "troubleshooting.md"}
                ]
            },
            "project_docs": {
                "structure": [
                    {"title": "Home", "file": "index.md"},
                    {"title": "About", "file": "about.md"},
                    {"title": "Goals", "file": "goals.md"},
                    {"title": "Processes", "file": "processes.md"},
                    {"title": "Team", "file": "team.md"},
                    {"title": "Progress", "file": "progress.md"}
                ]
            }
        }

    def analyze_document_structure(self, doc_content: str) -> Dict:
        """
        Analyze Google Doc content and extract navigation structure
        
        Args:
            doc_content: Raw content from Google Docs
            
        Returns:
            Dict containing analyzed structure
        """
        try:
            logger.info("Analyzing document structure...")
            
            # Parse the content into sections
            sections = self._parse_content(doc_content)
            
            # Generate navigation structure
            navigation = self._generate_navigation_structure(sections)
            
            # Analyze relationships and dependencies
            relationships = self._analyze_relationships(sections)
            
            # Suggest file organization
            file_organization = self._suggest_file_organization(sections)
            
            structure = {
                "sections": sections,
                "navigation": navigation,
                "relationships": relationships,
                "file_organization": file_organization,
                "suggested_template": self._suggest_template(sections),
                "metadata": self._extract_metadata(doc_content)
            }
            
            logger.info(f"Document structure analyzed: {len(sections)} sections found")
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {str(e)}")
            raise

    def _parse_content(self, content: str) -> List[NavigationSection]:
        """Parse content into sections based on heading structure"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a heading
            heading_match = re.match(r'^(#+)\s+(.+)$', line)
            if heading_match:
                # Save previous section if exists
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                
                # Start new section
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # Clean up title (remove any content that might have run together)
                if len(title) > 100:  # If title is too long, it probably contains content
                    # Try to find a natural break point
                    break_points = ['.', '!', '?', '\n']
                    for bp in break_points:
                        if bp in title:
                            title = title.split(bp)[0].strip()
                            break
                    
                    # If still too long, truncate
                    if len(title) > 100:
                        title = title[:100].strip()
                
                current_section = NavigationSection(
                    title=title,
                    level=level,
                    content="",
                    file_path=self._generate_file_path(title, level, "standard_docs"),
                    children=[],
                    metadata={}
                )
                current_content = []
            else:
                # Add line to current section content
                if current_section:
                    current_content.append(line)
        
        # Add the last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        return sections

    def _generate_file_path(self, title: str, level: int, template: str) -> str:
        """Generate a file path for a section"""
        # Clean the title for file naming
        clean_title = title.strip()
        
        # Remove any content after the first line break or excessive length
        if '\n' in clean_title:
            clean_title = clean_title.split('\n')[0]
        
        # Limit title length for file naming
        if len(clean_title) > 50:
            clean_title = clean_title[:50].strip()
        
        # Generate a clean filename
        filename = self._clean_filename(clean_title)
        
        # Add .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        # For top-level sections, create direct files
        if level == 1:
            return filename
        elif level == 2:
            # Create subdirectory structure
            clean_parent = self._clean_filename(title.split('\n')[0][:30])
            return f"{clean_parent}/{filename}"
        else:
            # For deeper levels, create nested structure
            clean_parent = self._clean_filename(title.split('\n')[0][:30])
            return f"{clean_parent}/{filename}"
    
    def _clean_filename(self, title: str) -> str:
        """Clean a title to create a valid filename"""
        import re
        
        # Remove special characters and replace with hyphens
        clean = re.sub(r'[^\w\s-]', '', title)
        clean = re.sub(r'[-\s]+', '-', clean)
        clean = clean.strip('-').lower()
        
        # Ensure it's not empty
        if not clean:
            clean = 'section'
        
        return clean

    def _generate_navigation_structure(self, sections: List[NavigationSection]) -> List[Dict]:
        """Generate MkDocs navigation structure from sections"""
        navigation = []
        
        for section in sections:
            nav_item = {
                "title": section.title,
                "file": section.file_path,
                "children": []
            }
            
            # Add children (subsections)
            for child in section.children:
                child_item = {
                    "title": child.title,
                    "file": child.file_path,
                    "children": []
                }
                
                # Add grandchildren
                for grandchild in child.children:
                    grandchild_item = {
                        "title": grandchild.title,
                        "file": grandchild.file_path
                    }
                    child_item["children"].append(grandchild_item)
                
                nav_item["children"].append(child_item)
            
            navigation.append(nav_item)
        
        return navigation

    def _analyze_relationships(self, sections: List[NavigationSection]) -> Dict:
        """Analyze relationships between sections"""
        relationships = {
            "cross_references": [],
            "dependencies": [],
            "suggested_links": []
        }
        
        # Look for cross-references in content
        for section in sections:
            # Find links and references
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', section.content)
            for link_text, link_url in links:
                relationships["cross_references"].append({
                    "from": section.title,
                    "to": link_text,
                    "url": link_url
                })
        
        return relationships

    def _suggest_file_organization(self, sections: List[NavigationSection]) -> Dict:
        """Suggest file organization structure"""
        organization = {
            "files": [],
            "directories": [],
            "suggestions": []
        }
        
        for section in sections:
            if section.level == 1:
                organization["files"].append(section.file_path)
            elif section.level == 2:
                # Create directory for level 2 sections
                dir_name = section.file_path.replace("/index.md", "")
                organization["directories"].append(dir_name)
                organization["files"].append(section.file_path)
        
        return organization

    def _suggest_template(self, sections: List[NavigationSection]) -> str:
        """Suggest the best navigation template based on content"""
        # Count different types of sections
        section_titles = [s.title.lower() for s in sections]
        
        # Analyze patterns to suggest template
        if any(word in " ".join(section_titles) for word in ["api", "reference", "technical", "code"]):
            return "technical_docs"
        elif any(word in " ".join(section_titles) for word in ["team", "process", "project", "goals"]):
            return "project_docs"
        else:
            return "standard_docs"

    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from document content"""
        metadata = {
            "total_sections": 0,
            "max_depth": 0,
            "estimated_pages": 0
        }
        
        # Count sections and depth
        lines = content.split('\n')
        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s*(.+)$', line.strip())
            if heading_match:
                metadata["total_sections"] += 1
                metadata["max_depth"] = max(metadata["max_depth"], len(heading_match.group(1)))
        
        # Estimate number of pages
        metadata["estimated_pages"] = max(1, metadata["total_sections"] // 3)
        
        return metadata

    def generate_mkdocs_navigation(self, structure: Dict, template: str = None) -> str:
        """Generate MkDocs navigation YAML from document structure"""
        try:
            sections = structure.get('sections', [])
            
            # Start with just the nav: header
            navigation_lines = ['nav:']
            
            # Only create navigation for the main document sections
            # Based on the user's screenshot, we want only the top-level sections
            main_sections = []
            
            for section in sections:
                # Only include level 1 sections as main pages
                if section.level == 1:
                    main_sections.append(section)
            
            # If we don't have level 1 sections, look for the main document structure
            if not main_sections:
                # Try to identify the main sections based on content analysis
                main_sections = self._identify_main_sections(sections)
            
            # Generate navigation for main sections only
            for section in main_sections:
                nav_line = f"  - {section.title}: {section.file_path}"
                navigation_lines.append(nav_line)
            
            return '\n'.join(navigation_lines)
            
        except Exception as e:
            logger.error(f"Error generating navigation: {e}")
            raise
    
    def _identify_main_sections(self, sections: List[NavigationSection]) -> List[NavigationSection]:
        """Identify the main document sections based on the big title headers"""
        # Look for level 1 headings - these are the main page headers
        main_sections = []
        
        for section in sections:
            # Only level 1 headings create separate pages
            if section.level == 1:
                # Clean up the title to get just the main header
                clean_title = section.title.strip()
                if '\n' in clean_title:
                    clean_title = clean_title.split('\n')[0]
                if len(clean_title) > 100:
                    # If title is too long, it probably contains content
                    # Look for natural break points
                    for char in ['.', '!', '?', ':', ';']:
                        if char in clean_title:
                            clean_title = clean_title.split(char)[0].strip()
                            break
                
                # Create a new section with the clean title
                main_section = NavigationSection(
                    title=clean_title,
                    level=1,
                    content=section.content,
                    file_path=self._generate_file_path(clean_title, 1, "standard_docs"),
                    children=[],
                    metadata={}
                )
                main_sections.append(main_section)
        
        # If we don't have level 1 sections, try to identify them by content analysis
        if not main_sections:
            # Look for sections that might be main headers based on their content
            for section in sections:
                section_title = section.title.strip()
                
                # Check if this looks like a main page header
                # Main headers are usually short, descriptive, and don't contain detailed content
                if (len(section_title) < 50 and 
                    not any(word in section_title.lower() for word in ['how', 'what', 'when', 'where', 'why', 'guide', 'flow', 'tracking', 'compensation'])):
                    
                    clean_title = section_title
                    if '\n' in clean_title:
                        clean_title = clean_title.split('\n')[0]
                    
                    main_section = NavigationSection(
                        title=clean_title,
                        level=1,
                        content=section.content,
                        file_path=self._generate_file_path(clean_title, 1, "standard_docs"),
                        children=[],
                        metadata={}
                    )
                    main_sections.append(main_section)
        
        return main_sections
    
    def _create_navigation_line(self, section: NavigationSection, indent_level: int) -> str:
        """Create a single navigation line with proper indentation"""
        indent = '  ' * indent_level
        
        # Clean up the title - use only the first line if it contains content
        title = section.title.strip()
        if '\n' in title or len(title) > 100:
            # If title is too long or contains newlines, extract just the heading
            lines = title.split('\n')
            title = lines[0].strip()
            
            # If it still contains content, try to find the actual heading
            if len(title) > 50:
                # Look for natural break points
                for char in ['.', '!', '?', ':', ';']:
                    if char in title:
                        title = title.split(char)[0].strip()
                        break
        
        # Create the navigation line
        if indent_level == 0:
            return f"{indent}- {title}: {section.file_path}"
        else:
            return f"{indent}- {title}: {section.file_path}"

    def validate_navigation(self, navigation_yaml: str) -> Dict:
        """
        Validate generated navigation structure
        
        Args:
            navigation_yaml: YAML navigation string
            
        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            lines = navigation_yaml.split('\n')
            
            # Check basic structure
            if not lines[0].strip().startswith('nav:'):
                validation["is_valid"] = False
                validation["errors"].append("Navigation must start with 'nav:'")
            
            # Check indentation consistency
            for i, line in enumerate(lines[1:], 1):
                if line.strip() and not line.startswith('  '):
                    validation["warnings"].append(f"Line {i+1}: Inconsistent indentation")
            
            # Check for duplicate entries
            entries = [line.strip() for line in lines[1:] if line.strip()]
            if len(entries) != len(set(entries)):
                validation["warnings"].append("Duplicate navigation entries detected")
            
            # Check file extensions
            for line in lines[1:]:
                if '.md' in line and not line.strip().endswith('.md'):
                    validation["suggestions"].append("Consider using .md extension for all files")
            
        except Exception as e:
            validation["is_valid"] = False
            validation["errors"].append(f"Validation error: {str(e)}")
        
        return validation

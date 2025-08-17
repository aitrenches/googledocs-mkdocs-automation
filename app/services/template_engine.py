import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    Manages document templates for different types of documentation
    Provides consistent formatting and structure
    """
    
    def __init__(self):
        self.templates = self._load_default_templates()
        self.custom_templates = {}
        
    def _load_default_templates(self) -> Dict:
        """Load default templates for different document types"""
        return {
            "standard_docs": {
                "name": "Standard Documentation",
                "description": "General purpose documentation template",
                "structure": {
                    "frontmatter": True,
                    "toc": True,
                    "breadcrumbs": True,
                    "edit_uri": True
                },
                "sections": [
                    {"level": 1, "title": "Home", "required": True},
                    {"level": 1, "title": "About", "required": False},
                    {"level": 1, "title": "Team", "required": False},
                    {"level": 1, "title": "Operations", "required": False},
                    {"level": 1, "title": "Tools", "required": False},
                    {"level": 1, "title": "FAQ", "required": False}
                ],
                "formatting": {
                    "heading_style": "atx",  # # style
                    "code_blocks": True,
                    "admonitions": True,
                    "tables": True
                }
            },
            "technical_docs": {
                "name": "Technical Documentation",
                "description": "API and technical reference documentation",
                "structure": {
                    "frontmatter": True,
                    "toc": True,
                    "breadcrumbs": True,
                    "edit_uri": True,
                    "search": True
                },
                "sections": [
                    {"level": 1, "title": "Overview", "required": True},
                    {"level": 1, "title": "Getting Started", "required": True},
                    {"level": 1, "title": "API Reference", "required": False},
                    {"level": 1, "title": "Examples", "required": False},
                    {"level": 1, "title": "Configuration", "required": False},
                    {"level": 1, "title": "Troubleshooting", "required": False}
                ],
                "formatting": {
                    "heading_style": "atx",
                    "code_blocks": True,
                    "admonitions": True,
                    "tables": True,
                    "syntax_highlighting": True
                }
            },
            "project_docs": {
                "name": "Project Documentation",
                "description": "Project management and process documentation",
                "structure": {
                    "frontmatter": True,
                    "toc": True,
                    "breadcrumbs": True,
                    "edit_uri": False
                },
                "sections": [
                    {"level": 1, "title": "Home", "required": True},
                    {"level": 1, "title": "About", "required": False},
                    {"level": 1, "title": "Goals", "required": False},
                    {"level": 1, "title": "Processes", "required": False},
                    {"level": 1, "title": "Team", "required": False},
                    {"level": 1, "title": "Progress", "required": False}
                ],
                "formatting": {
                    "heading_style": "atx",
                    "code_blocks": False,
                    "admonitions": True,
                    "tables": True
                }
            },
            "minimal": {
                "name": "Minimal Documentation",
                "description": "Simple, minimal documentation template",
                "structure": {
                    "frontmatter": False,
                    "toc": False,
                    "breadcrumbs": False,
                    "edit_uri": False
                },
                "sections": [
                    {"level": 1, "title": "Home", "required": True}
                ],
                "formatting": {
                    "heading_style": "atx",
                    "code_blocks": True,
                    "admonitions": False,
                    "tables": True
                }
            }
        }
    
    def get_template(self, template_name: str) -> Dict:
        """Get a template by name"""
        if template_name in self.custom_templates:
            return self.custom_templates[template_name]
        return self.templates.get(template_name, self.templates["standard_docs"])
    
    def list_templates(self) -> List[Dict]:
        """List all available templates"""
        all_templates = []
        
        # Add default templates
        for name, template in self.templates.items():
            all_templates.append({
                "name": name,
                "display_name": template["name"],
                "description": template["description"],
                "type": "default"
            })
        
        # Add custom templates
        for name, template in self.custom_templates.items():
            all_templates.append({
                "name": name,
                "display_name": template["name"],
                "description": template["description"],
                "type": "custom"
            })
        
        return all_templates
    
    def create_custom_template(self, name: str, template_data: Dict) -> bool:
        """Create a custom template"""
        try:
            # Validate template structure
            if self._validate_template(template_data):
                self.custom_templates[name] = template_data
                logger.info(f"Custom template '{name}' created successfully")
                return True
            else:
                logger.error(f"Invalid template structure for '{name}'")
                return False
        except Exception as e:
            logger.error(f"Error creating custom template '{name}': {str(e)}")
            raise
    
    def _validate_template(self, template: Dict) -> bool:
        """Validate template structure"""
        required_keys = ["name", "description", "structure", "sections", "formatting"]
        
        # Check required keys
        for key in required_keys:
            if key not in template:
                logger.error(f"Missing required key: {key}")
                return False
        
        # Check structure keys
        structure_keys = ["frontmatter", "toc", "breadcrumbs", "edit_uri"]
        for key in structure_keys:
            if key not in template["structure"]:
                logger.error(f"Missing structure key: {key}")
                return False
        
        # Check sections
        if not isinstance(template["sections"], list):
            logger.error("Sections must be a list")
            return False
        
        # Check formatting
        formatting_keys = ["heading_style", "code_blocks", "admonitions", "tables"]
        for key in formatting_keys:
            if key not in template["formatting"]:
                logger.error(f"Missing formatting key: {key}")
                return False
        
        return True
    
    def apply_template(self, content: str, template_name: str, metadata: Dict = None) -> str:
        """
        Apply a template to content
        
        Args:
            content: Raw content to format
            template_name: Name of template to apply
            metadata: Additional metadata for the document
            
        Returns:
            Formatted content according to template
        """
        try:
            template = self.get_template(template_name)
            logger.info(f"Applying template '{template_name}' to content")
            
            # Apply template formatting
            formatted_content = self._format_content(content, template)
            
            # Add frontmatter if required
            if template["structure"]["frontmatter"]:
                frontmatter = self._generate_frontmatter(template, metadata)
                formatted_content = frontmatter + "\n\n" + formatted_content
            
            # Add table of contents if required
            if template["structure"]["toc"]:
                toc = self._generate_toc(formatted_content)
                formatted_content = formatted_content + "\n\n" + toc
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error applying template '{template_name}': {str(e)}")
            raise
    
    def _format_content(self, content: str, template: Dict) -> str:
        """Format content according to template rules"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Apply heading formatting
            if line.strip().startswith('#'):
                formatted_line = self._format_heading(line, template)
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_heading(self, line: str, template: Dict) -> str:
        """Format heading according to template rules"""
        # Extract heading level and title
        match = re.match(r'^(#{1,6})\s*(.+)$', line.strip())
        if not match:
            return line
        
        level = len(match.group(1))
        title = match.group(2).strip()
        
        # Apply heading style
        if template["formatting"]["heading_style"] == "atx":
            return f"{'#' * level} {title}"
        else:
            # Setext style (underlined)
            underline = "=" if level == 1 else "-"
            return f"{title}\n{underline * len(title)}"
    
    def _generate_frontmatter(self, template: Dict, metadata: Dict = None) -> str:
        """Generate YAML frontmatter for the document"""
        frontmatter = {
            "title": metadata.get("title", "Documentation"),
            "description": metadata.get("description", ""),
            "template": template["name"],
            "created": metadata.get("created", ""),
            "updated": metadata.get("updated", ""),
            "author": metadata.get("author", ""),
            "tags": metadata.get("tags", [])
        }
        
        # Remove empty values
        frontmatter = {k: v for k, v in frontmatter.items() if v}
        
        return yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    
    def _generate_toc(self, content: str) -> str:
        """Generate table of contents from content"""
        lines = content.split('\n')
        toc_lines = ["## Table of Contents", ""]
        
        for line in lines:
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()
                
                # Create TOC entry
                indent = "  " * (level - 1)
                anchor = self._create_anchor(title)
                toc_lines.append(f"{indent}- [{title}](#{anchor})")
        
        return '\n'.join(toc_lines)
    
    def _create_anchor(self, title: str) -> str:
        """Create anchor link from title"""
        # Convert to lowercase and replace spaces with hyphens
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'\s+', '-', anchor).strip('-')
        return anchor
    
    def save_template(self, template_name: str, file_path: str) -> bool:
        """Save template to file"""
        try:
            template = self.get_template(template_name)
            if not template:
                return False
            
            with open(file_path, 'w') as f:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Template '{template_name}' saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving template '{template_name}': {str(e)}")
            return False
    
    def load_template(self, file_path: str) -> Optional[Dict]:
        """Load template from file"""
        try:
            with open(file_path, 'r') as f:
                template = yaml.safe_load(f)
            
            if self._validate_template(template):
                logger.info(f"Template loaded from {file_path}")
                return template
            else:
                logger.error(f"Invalid template in {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {str(e)}")
            return None

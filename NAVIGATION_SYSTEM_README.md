# 🧭 Navigation Management System

## Overview

The Navigation Management System implements the **Single Document with Sections** approach for organizing Google Docs content into structured MkDocs documentation. This system automatically analyzes document structure, applies templates, and generates appropriate navigation.

## 🏗️ Architecture

### Single Document with Sections Approach

Instead of managing multiple separate Google Docs, this system uses **one master document** with clear section hierarchy:

```
📄 Master Documentation Document
├── 🏠 Home Section
├── 📚 About Section
│   ├── 🎯 Strategic Pillars
│   └── 🛠️ Main Tools
├── 👥 Team Management
│   ├── 🏆 Awarded Teams
│   └── 🔍 Review Process
├── 📋 Operations
└── ❓ FAQ
```

### Key Benefits

- **Single Source of Truth**: One document to maintain
- **Automatic Structure Analysis**: System detects sections and hierarchy
- **Template-Based Formatting**: Consistent styling across all content
- **Smart Navigation Generation**: Automatic MkDocs navigation creation
- **Cross-Reference Management**: Handles links and dependencies

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file with your credentials:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your-org/your-repo

# Google Docs Configuration (if using)
GOOGLE_CREDENTIALS_FILE=google_credentials.json
```

### 3. Configure Repositories

Create a `repositories.yml` file:

```yaml
repositories:
  - name: "main-docs"
    url: "https://github.com/your-org/main-docs"
    branch: "main"
    mkdocs_config: "mkdocs.yml"
    deployment: "github-pages"
```

## 📋 Available Templates

### Standard Documentation (`standard_docs`)
- General purpose documentation
- Includes frontmatter, TOC, and emojis
- Suitable for most documentation needs

### Technical Documentation (`technical_docs`)
- API and technical reference docs
- Enhanced code block support
- Syntax highlighting features

### Project Documentation (`project_docs`)
- Project management and process docs
- Simplified structure
- Focus on workflows and procedures

### Minimal (`minimal`)
- Simple, clean documentation
- No extra formatting
- Fastest processing

## 🛠️ Usage

### CLI Commands

#### List Available Templates
```bash
python cli.py list-templates
```

#### Apply Template to Content
```bash
python cli.py apply-template sample_document.md --template standard_docs
```

#### Analyze Document Structure
```bash
python cli.py analyze-structure sample_document.md
```

#### Complete Document Processing
```bash
python cli.py process-document sample_document.md --template auto
```

#### Validate Configuration
```bash
python cli.py validate-config
```

### Python API

```python
from app.services.navigation_manager import NavigationManager
from app.services.template_engine import TemplateEngine

# Initialize services
nav_manager = NavigationManager()
template_engine = TemplateEngine()

# Analyze document structure
structure = nav_manager.analyze_document_structure(content)

# Apply template
formatted_content = template_engine.apply_template(
    content, 
    "standard_docs",
    metadata={"title": "My Document"}
)

# Generate navigation
navigation_yaml = nav_manager.generate_mkdocs_navigation(structure)
```

## 📝 Google Docs Best Practices

### 1. Use Consistent Heading Structure

```
# 🏠 Main Title (Level 1)
## 📚 Section Title (Level 2)
### 🎯 Subsection Title (Level 3)
#### Detail Title (Level 4)
```

### 2. Include Emojis for Section Identification

- **🏠 Home/Overview**: Main page content
- **📚 About**: Background and context
- **👥 Team**: People and roles
- **📋 Operations**: Processes and workflows
- **🛠️ Tools**: Software and applications
- **❓ FAQ**: Questions and answers

### 3. Maintain Clear Hierarchy

- Keep main sections at Level 1
- Use Level 2 for major subsections
- Use Level 3+ for detailed breakdowns
- Avoid skipping levels (e.g., # to ###)

### 4. Use Descriptive Section Names

```
✅ Good: "## 🏆 Awarded Teams Management"
❌ Bad: "## Teams"
```

## 🔧 Configuration Options

### Template Customization

You can create custom templates by modifying the `TemplateEngine` class:

```python
custom_template = {
    "name": "My Custom Template",
    "description": "Custom template for my needs",
    "structure": {
        "frontmatter": True,
        "toc": True,
        "breadcrumbs": True,
        "edit_uri": False
    },
    "sections": [
        {"level": 1, "emoji": "🏠", "title": "Home", "required": True}
    ],
    "formatting": {
        "use_emojis": True,
        "heading_style": "atx",
        "code_blocks": True,
        "admonitions": True,
        "tables": True
    }
}

template_engine.create_custom_template("my_template", custom_template)
```

### Navigation Templates

Customize navigation generation by modifying the `NavigationManager`:

```python
# Add custom emoji patterns
nav_manager.emoji_patterns["🎨"] = "Design"

# Add custom navigation templates
nav_manager.navigation_templates["my_template"] = {
    "structure": [
        {"emoji": "🏠", "title": "Home", "file": "index.md"}
    ]
}
```

## 📊 Output Files

The system generates several output files:

### 1. Formatted Content (`*_formatted.md`)
- Content with applied template formatting
- Includes frontmatter and TOC if enabled
- Ready for MkDocs processing

### 2. Navigation (`navigation.yml`)
- YAML navigation structure for MkDocs
- Hierarchical organization
- Ready to copy into `mkdocs.yml`

### 3. Structure Analysis (`structure_analysis.json`)
- Detailed analysis of document structure
- Section hierarchy and metadata
- Useful for debugging and optimization

## 🔍 Testing the System

### Run the Test Script

```bash
python test_navigation_system.py
```

This will:
1. Test all available templates
2. Analyze the sample document
3. Generate navigation
4. Apply formatting
5. Save all outputs

### Test with Your Own Content

1. Create a markdown file with your content
2. Use the CLI commands to process it
3. Review the generated outputs
4. Adjust your document structure if needed

## 🚨 Troubleshooting

### Common Issues

#### Template Not Found
```
Error: Template 'my_template' not found
```
**Solution**: Check template name or create custom template

#### Invalid Navigation Structure
```
Error: Navigation validation failed
```
**Solution**: Review heading structure in your document

#### Configuration Errors
```
Error: Missing required configuration
```
**Solution**: Check your `.env` file and `repositories.yml`

### Debug Mode

Enable debug logging for detailed information:

```bash
python cli.py --debug list-templates
```

## 🔮 Future Enhancements

### Planned Features

1. **Multi-Document Support**: Handle multiple Google Docs
2. **Advanced Templates**: More sophisticated formatting options
3. **Navigation Optimization**: AI-powered navigation suggestions
4. **Cross-Repository Sync**: Update multiple docs sites simultaneously
5. **Version Control**: Track changes and rollback capabilities

### Contributing

To contribute to the navigation system:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📚 Additional Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Google Docs API](https://developers.google.com/docs/api)
- [OpenAI API](https://platform.openai.com/docs)

---

*This system is designed to make documentation management as simple as possible while maintaining professional quality and consistency.*

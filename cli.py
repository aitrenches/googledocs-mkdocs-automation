#!/usr/bin/env python3
"""
CLI tool for Google Docs to MkDocs conversion
Tests the navigation management and template system
"""

import click
import asyncio
import logging
from pathlib import Path
from app.services.navigation_manager import NavigationManager
from app.services.template_engine import TemplateEngine
from app.config.settings import get_config_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
def cli(debug):
    """Google Docs to MkDocs Converter CLI"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        click.echo("Debug mode enabled")

@cli.command()
@click.option('--template', '-t', default='standard_docs', help='Template to use')
@click.option('--output', '-o', default='output', help='Output directory')
def list_templates(template, output):
    """List available templates"""
    template_engine = TemplateEngine()
    templates = template_engine.list_templates()
    
    click.echo("Available Templates:")
    click.echo("=" * 50)
    
    for template_info in templates:
        click.echo(f"📋 {template_info['display_name']} ({template_info['name']})")
        click.echo(f"   Type: {template_info['type']}")
        click.echo(f"   Description: {template_info['description']}")
        click.echo()
    
    if template != 'standard_docs':
        click.echo(f"Selected template: {template}")
        template_details = template_engine.get_template(template)
        if template_details:
            click.echo(f"Template details: {template_details['description']}")

@cli.command()
@click.argument('content_file', type=click.Path(exists=True))
@click.option('--template', '-t', default='standard_docs', help='Template to apply')
@click.option('--output', '-o', default='output', help='Output directory')
def apply_template(content_file, template, output):
    """Apply a template to content"""
    try:
        # Read content file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply template
        template_engine = TemplateEngine()
        formatted_content = template_engine.apply_template(
            content, 
            template, 
            metadata={
                "title": Path(content_file).stem,
                "description": f"Content from {content_file}",
                "template": template
            }
        )
        
        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save formatted content
        output_file = output_path / f"{Path(content_file).stem}_formatted.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        click.echo(f"✅ Template applied successfully!")
        click.echo(f"📁 Output saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error applying template: {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('content_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='output', help='Output directory')
def analyze_structure(content_file, output):
    """Analyze document structure and generate navigation"""
    try:
        # Read content file
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Analyze structure
        nav_manager = NavigationManager()
        structure = nav_manager.analyze_document_structure(content)
        
        # Display analysis results
        click.echo("📊 Document Structure Analysis")
        click.echo("=" * 50)
        
        click.echo(f"📄 Total sections: {structure['metadata']['total_sections']}")
        click.echo(f"📊 Max depth: {structure['metadata']['max_depth']}")
        click.echo(f"📚 Estimated pages: {structure['metadata']['estimated_pages']}")
        click.echo(f"🎯 Suggested template: {structure['suggested_template']}")
        
        click.echo("\n📋 Sections found:")
        for section in structure['sections']:
            indent = "  " * (section.level - 1)
            click.echo(f"{indent}📄 {section.title} -> {section.file_path}")
        
        # Generate navigation
        navigation_yaml = nav_manager.generate_mkdocs_navigation(structure)
        
        # Validate navigation
        validation = nav_manager.validate_navigation(navigation_yaml)
        
        click.echo(f"\n✅ Navigation validation: {'PASS' if validation['is_valid'] else 'FAIL'}")
        if validation['warnings']:
            click.echo("⚠️  Warnings:")
            for warning in validation['warnings']:
                click.echo(f"   {warning}")
        
        if validation['suggestions']:
            click.echo("💡 Suggestions:")
            for suggestion in validation['suggestions']:
                click.echo(f"   {suggestion}")
        
        # Save navigation
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        nav_file = output_path / "navigation.yml"
        with open(nav_file, 'w', encoding='utf-8') as f:
            f.write(navigation_yaml)
        
        click.echo(f"\n📁 Navigation saved to: {nav_file}")
        click.echo("\n📝 Generated Navigation:")
        click.echo(navigation_yaml)
        
    except Exception as e:
        click.echo(f"❌ Error analyzing structure: {str(e)}")
        raise click.Abort()

@cli.command()
@click.option('--config-file', '-c', default='repositories.yml', help='Configuration file')
def validate_config(config_file, output):
    """Validate configuration"""
    try:
        config_manager = get_config_manager()
        validation = config_manager.validate_config()
        
        click.echo("🔧 Configuration Validation")
        click.echo("=" * 50)
        
        if validation['is_valid']:
            click.echo("✅ Configuration is valid!")
        else:
            click.echo("❌ Configuration has errors:")
            for error in validation['errors']:
                click.echo(f"   {error}")
        
        if validation['missing_required']:
            click.echo("\n❌ Missing required fields:")
            for field in validation['missing_required']:
                click.echo(f"   {field}")
        
        if validation['warnings']:
            click.echo("\n⚠️  Warnings:")
            for warning in validation['warnings']:
                click.echo(f"   {warning}")
        
        # Show current configuration
        settings = config_manager.settings
        click.echo(f"\n📋 Current Configuration:")
        click.echo(f"   App Name: {settings.app_name}")
        click.echo(f"   Version: {settings.app_version}")
        click.echo(f"   Default Template: {settings.default_template}")
        click.echo(f"   Repositories: {len(settings.repositories)}")
        
        for repo in settings.repositories:
            click.echo(f"     - {repo.name}: {repo.url}")
        
    except Exception as e:
        click.echo(f"❌ Error validating config: {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('content_file', type=click.Path(exists=True))
@click.option('--template', '-t', default='standard_docs', help='Template to use')
@click.option('--output', '-o', default='output', help='Output directory')
def process_document(content_file, template, output):
    """Complete document processing: analyze, template, and generate navigation"""
    try:
        click.echo("🚀 Starting complete document processing...")
        
        # Step 1: Analyze structure
        click.echo("\n📊 Step 1: Analyzing document structure...")
        nav_manager = NavigationManager()
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        structure = nav_manager.analyze_document_structure(content)
        click.echo(f"✅ Structure analyzed: {len(structure['sections'])} sections found")
        
        # Step 2: Apply template
        click.echo("\n🎨 Step 2: Applying template...")
        template_engine = TemplateEngine()
        
        # Auto-detect template if enabled
        if template == 'auto':
            template = structure['suggested_template']
            click.echo(f"🎯 Auto-detected template: {template}")
        
        formatted_content = template_engine.apply_template(
            content, 
            template, 
            metadata={
                "title": Path(content_file).stem,
                "description": f"Processed content from {content_file}",
                "template": template
            }
        )
        click.echo(f"✅ Template applied: {template}")
        
        # Step 3: Generate navigation
        click.echo("\n🧭 Step 3: Generating navigation...")
        navigation_yaml = nav_manager.generate_mkdocs_navigation(structure, template)
        click.echo("✅ Navigation generated")
        
        # Step 4: Save outputs
        click.echo("\n💾 Step 4: Saving outputs...")
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save formatted content
        formatted_file = output_path / f"{Path(content_file).stem}_formatted.md"
        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        # Save navigation
        nav_file = output_path / "navigation.yml"
        with open(nav_file, 'w', encoding='utf-8') as f:
            f.write(navigation_yaml)
        
        # Save structure analysis
        import json
        structure_file = output_path / "structure_analysis.json"
        with open(structure_file, 'w', encoding='utf-8') as f:
            # Convert dataclass to dict for JSON serialization
            structure_dict = {
                "sections": [
                    {
                        "title": s.title,
                        "level": s.level,
                        "file_path": s.file_path,
                        "children_count": len(s.children)
                    }
                    for s in structure["sections"]
                ],
                "suggested_template": structure["suggested_template"],
                "metadata": structure["metadata"]
            }
            json.dump(structure_dict, f, indent=2)
        
        click.echo("✅ All outputs saved successfully!")
        click.echo(f"\n📁 Output files:")
        click.echo(f"   📄 Formatted content: {formatted_file}")
        click.echo(f"   🧭 Navigation: {nav_file}")
        click.echo(f"   📊 Structure analysis: {structure_file}")
        
        # Show summary
        click.echo(f"\n📋 Processing Summary:")
        click.echo(f"   Template used: {template}")
        click.echo(f"   Sections processed: {len(structure['sections'])}")
        click.echo(f"   Files generated: 3")
        
    except Exception as e:
        click.echo(f"❌ Error processing document: {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('doc_id')
@click.option('--template', '-t', default='auto', help='Template to use (or "auto" for auto-detection)')
@click.option('--output', '-o', default='output', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Analyze and show structure without creating files')
def process_google_doc(doc_id, template, output, dry_run):
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    """Process a Google Doc by document ID"""
    try:
        click.echo(f"🚀 Processing Google Doc: {doc_id}")
        
        # Import services
        from app.services.google_docs import GoogleDocsService
        from app.services.ai_converter import AIConverter
        from app.services.navigation_manager import NavigationManager
        from app.services.template_engine import TemplateEngine
        
        # Step 1: Fetch Google Doc content
        click.echo("\n📄 Step 1: Fetching Google Doc content...")
        docs_service = GoogleDocsService()
        doc_content = docs_service.get_document_content(doc_id)
        click.echo(f"✅ Retrieved: '{doc_content['title']}'")
        
        # Debug: Show content preview
        click.echo(f"\n🔍 Content Preview (first 500 chars):")
        click.echo("-" * 50)
        click.echo(doc_content['content'][:500])
        click.echo("-" * 50)
        click.echo(f"Total content length: {len(doc_content['content'])} characters")
        
        # Step 2: Analyze structure
        click.echo("\n🧭 Step 2: Analyzing document structure...")
        nav_manager = NavigationManager()
        structure = nav_manager.analyze_document_structure(doc_content['content'])
        
        click.echo(f"📊 Analysis Results:")
        click.echo(f"   📄 Total sections: {structure['metadata']['total_sections']}")
        click.echo(f"   📊 Max depth: {structure['metadata']['max_depth']}")
        click.echo(f"   📚 Estimated pages: {structure['metadata']['estimated_pages']}")
        click.echo(f"   🎯 Suggested template: {structure['suggested_template']}")
        
        # Auto-detect template if requested
        if template == 'auto':
            template = structure['suggested_template']
            click.echo(f"🎯 Auto-detected template: {template}")
        
        # Step 3: Show structure
        click.echo("\n📋 Document Structure:")
        for section in structure['sections']:
            indent = "  " * (section.level - 1)
            click.echo(f"{indent}📄 {section.title} -> {section.file_path}")
            
            # Show subsections
            for child in section.children:
                child_indent = "  " * (child.level - 1)
                click.echo(f"{child_indent}📄 {child.title} -> {child.file_path}")
        
        # Step 4: Generate navigation
        click.echo("\n🧭 Step 3: Generating navigation...")
        navigation_yaml = nav_manager.generate_mkdocs_navigation(structure, template)
        click.echo("✅ Navigation generated")
        
        # Validate navigation
        validation = nav_manager.validate_navigation(navigation_yaml)
        if validation['is_valid']:
            click.echo("✅ Navigation validation passed")
        else:
            click.echo("⚠️ Navigation validation issues:")
            for error in validation['errors']:
                click.echo(f"   ❌ {error}")
        
        if validation['warnings']:
            click.echo("⚠️ Warnings:")
            for warning in validation['warnings']:
                click.echo(f"   ⚠️ {warning}")
        
        # Step 5: Convert to Markdown (if not dry run)
        if not dry_run:
            click.echo("\n🔄 Step 4: Converting to Markdown...")
            ai_converter = AIConverter()
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                markdown_content = loop.run_until_complete(
                    ai_converter.convert_to_markdown(doc_content['raw_content'])
                )
                click.echo("✅ Content converted to Markdown")
            finally:
                loop.close()
            
            # Apply template
            template_engine = TemplateEngine()
            formatted_content = template_engine.apply_template(
                markdown_content,
                template,
                metadata={
                    "title": doc_content['title'],
                    "description": f"Documentation from Google Doc: {doc_content['title']}",
                    "template": template,
                    "source": f"Google Doc ID: {doc_id}"
                }
            )
            click.echo(f"✅ Template '{template}' applied")
            
            # Save outputs
            output_path = Path(output)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save formatted content
            formatted_file = output_path / f"{doc_id}_formatted.md"
            with open(formatted_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            # Save navigation
            nav_file = output_path / f"{doc_id}_navigation.yml"
            with open(nav_file, 'w', encoding='utf-8') as f:
                f.write(navigation_yaml)
            
            # Save structure analysis
            import json
            structure_file = output_path / f"{doc_id}_structure.json"
            with open(structure_file, 'w', encoding='utf-8') as f:
                structure_dict = {
                    "title": doc_content['title'],
                    "doc_id": doc_id,
                    "sections": [
                        {
                            "title": s.title,
                            "level": s.level,
                            "file_path": s.file_path,
                            "children_count": len(s.children)
                        }
                        for s in structure["sections"]
                    ],
                    "suggested_template": structure["suggested_template"],
                    "metadata": structure["metadata"]
                }
                json.dump(structure_dict, f, indent=2)
            
            click.echo(f"\n💾 Outputs saved to: {output_path}")
            click.echo(f"   📄 Formatted content: {formatted_file}")
            click.echo(f"   🧭 Navigation: {nav_file}")
            click.echo(f"   📊 Structure analysis: {structure_file}")
        
        # Show navigation preview
        click.echo(f"\n📝 Generated Navigation Preview:")
        click.echo(navigation_yaml)
        
        click.echo(f"\n🎉 Processing completed!")
        if dry_run:
            click.echo("🔍 This was a dry run - no files were created")
            click.echo("💡 Run without --dry-run to create actual files")
        
    except Exception as e:
        click.echo(f"❌ Error processing Google Doc: {str(e)}")
        raise click.Abort()

if __name__ == '__main__':
    cli()

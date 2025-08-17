#!/usr/bin/env python3
"""
Test script for the Navigation Management and Template System
Demonstrates the Single Document with Sections approach
"""

import asyncio
import logging
from pathlib import Path
from app.services.navigation_manager import NavigationManager
from app.services.template_engine import TemplateEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_navigation_system():
    """Test the complete navigation management system"""
    
    print("🚀 Testing Navigation Management System")
    print("=" * 60)
    
    # Initialize services
    nav_manager = NavigationManager()
    template_engine = TemplateEngine()
    
    # Test 1: List available templates
    print("\n📋 Test 1: Available Templates")
    print("-" * 40)
    templates = template_engine.list_templates()
    for template in templates:
        print(f"  📋 {template['display_name']} ({template['name']})")
        print(f"     Type: {template['type']}")
        print(f"     Description: {template['description']}")
    
    # Test 2: Analyze sample document
    print("\n📊 Test 2: Document Structure Analysis")
    print("-" * 40)
    
    sample_file = Path("sample_document.md")
    if not sample_file.exists():
        print("❌ Sample document not found. Please create sample_document.md first.")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Analyze structure
    structure = nav_manager.analyze_document_structure(content)
    
    print(f"📄 Total sections: {structure['metadata']['total_sections']}")
    print(f"📊 Max depth: {structure['metadata']['max_depth']}")
    print(f"📚 Estimated pages: {structure['metadata']['estimated_pages']}")
    print(f"🎯 Suggested template: {structure['suggested_template']}")
    
    # Display sections
    print("\n📋 Sections found:")
    for section in structure['sections']:
        indent = "  " * (section.level - 1)
        print(f"{indent}📄 {section.title} -> {section.file_path}")
        
        # Show subsections
        for child in section.children:
            child_indent = "  " * (child.level - 1)
            print(f"{child_indent}📄 {child.title} -> {child.file_path}")
            
            # Show sub-subsections
            for grandchild in child.children:
                grandchild_indent = "  " * (grandchild.level - 1)
                print(f"{grandchild_indent}📄 {grandchild.title} -> {grandchild.file_path}")
    
    # Test 3: Generate navigation
    print("\n🧭 Test 3: Navigation Generation")
    print("-" * 40)
    
    navigation_yaml = nav_manager.generate_mkdocs_navigation(structure)
    print("Generated Navigation:")
    print(navigation_yaml)
    
    # Test 4: Validate navigation
    print("\n✅ Test 4: Navigation Validation")
    print("-" * 40)
    
    validation = nav_manager.validate_navigation(navigation_yaml)
    print(f"Validation: {'PASS' if validation['is_valid'] else 'FAIL'}")
    
    if validation['warnings']:
        print("⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   {warning}")
    
    if validation['suggestions']:
        print("💡 Suggestions:")
        for suggestion in validation['suggestions']:
            print(f"   {suggestion}")
    
    # Test 5: Apply template
    print("\n🎨 Test 5: Template Application")
    print("-" * 40)
    
    template_name = structure['suggested_template']
    print(f"Using template: {template_name}")
    
    formatted_content = template_engine.apply_template(
        content, 
        template_name, 
        metadata={
            "title": "Deep Funding Operations Documentation",
            "description": "Comprehensive documentation for Deep Funding operations",
            "template": template_name,
            "author": "Deep Funding Documentation Circle"
        }
    )
    
    print(f"✅ Template applied successfully!")
    print(f"📄 Original content length: {len(content)} characters")
    print(f"📄 Formatted content length: {len(formatted_content)} characters")
    
    # Test 6: Save outputs
    print("\n💾 Test 6: Save Outputs")
    print("-" * 40)
    
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save formatted content
    formatted_file = output_dir / "formatted_document.md"
    with open(formatted_file, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    # Save navigation
    nav_file = output_dir / "navigation.yml"
    with open(nav_file, 'w', encoding='utf-8') as f:
        f.write(navigation_yaml)
    
    # Save structure analysis
    import json
    structure_file = output_dir / "structure_analysis.json"
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
    
    print("✅ All outputs saved successfully!")
    print(f"📁 Output directory: {output_dir}")
    print(f"   📄 Formatted content: {formatted_file}")
    print(f"   🧭 Navigation: {nav_file}")
    print(f"   📊 Structure analysis: {structure_file}")
    
    # Test 7: File organization suggestions
    print("\n📁 Test 7: File Organization Suggestions")
    print("-" * 40)
    
    file_org = structure['file_organization']
    print(f"📄 Files to create: {len(file_org['files'])}")
    for file_path in file_org['files']:
        print(f"   📄 {file_path}")
    
    print(f"📁 Directories to create: {len(file_org['directories'])}")
    for directory in file_org['directories']:
        print(f"   📁 {directory}")
    
    # Test 8: Cross-references
    print("\n🔗 Test 8: Cross-References Analysis")
    print("-" * 40)
    
    relationships = structure['relationships']
    print(f"🔗 Cross-references found: {len(relationships['cross_references'])}")
    for ref in relationships['cross_references']:
        print(f"   {ref['from']} -> {ref['to']} ({ref['url']})")
    
    print(f"📋 Dependencies: {len(relationships['dependencies'])}")
    print(f"💡 Suggested links: {len(relationships['suggested_links'])}")
    
    print("\n🎉 Navigation Management System Test Completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_navigation_system())

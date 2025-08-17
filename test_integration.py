import asyncio
import os
from dotenv import load_dotenv
from app.services.google_docs import GoogleDocsService
from app.services.ai_converter import AIConverter
from app.services.github_service import GitHubService
from app.services.navigation_manager import NavigationManager
from app.services.template_engine import TemplateEngine
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_documentation_update():
    """
    End-to-end POC demonstration of automated documentation update:
    Google Docs → Markdown → MkDocs → Deployed Site
    
    Now enhanced with intelligent navigation management and structure analysis
    """
    try:
        logger.info("🚀 Starting automated documentation update process...")
        
        # 1. Get content from Google Docs
        logger.info("\n📄 Step 1: Fetching Google Docs content...")
        docs_service = GoogleDocsService()
        doc_id = os.getenv('DOCUMENT_ID')  # Your test doc
        doc_content = docs_service.get_document_content(doc_id)
        logger.info(f"✅ Retrieved document: '{doc_content['title']}'")

        # 2. Analyze document structure and generate navigation
        logger.info("\n🧭 Step 2: Analyzing document structure and generating navigation...")
        nav_manager = NavigationManager()
        template_engine = TemplateEngine()
        
        # Analyze the Google Docs content structure
        structure = nav_manager.analyze_document_structure(doc_content['raw_content'])
        logger.info(f"✅ Document structure analyzed: {len(structure['sections'])} sections found")
        logger.info(f"📊 Max depth: {structure['metadata']['max_depth']}")
        logger.info(f"🎯 Suggested template: {structure['suggested_template']}")
        
        # Generate MkDocs navigation
        navigation_yaml = nav_manager.generate_mkdocs_navigation(structure)
        logger.info("✅ Navigation structure generated")
        
        # Validate navigation
        validation = nav_manager.validate_navigation(navigation_yaml)
        if not validation['is_valid']:
            logger.warning(f"⚠️ Navigation validation issues: {validation['errors']}")
        else:
            logger.info("✅ Navigation validation passed")

        # 3. Convert to Markdown with template
        logger.info("\n🔄 Step 3: Converting to Markdown with template...")
        ai_converter = AIConverter()
        
        # First convert raw content to markdown
        markdown_content = await ai_converter.convert_to_markdown(doc_content['raw_content'])
        logger.info("✅ Content converted to Markdown")
        
        # Apply template for consistent formatting
        template_name = structure['suggested_template']
        formatted_content = template_engine.apply_template(
            markdown_content, 
            template_name, 
            metadata={
                "title": doc_content['title'],
                "description": f"Documentation from Google Doc: {doc_content['title']}",
                "template": template_name,
                "created": datetime.now().isoformat(),
                "source": f"Google Doc ID: {doc_id}"
            }
        )
        logger.info(f"✅ Template '{template_name}' applied")

        # 4. Create GitHub Branch and Updates
        logger.info("\n📦 Step 4: Creating GitHub updates...")
        github_service = GitHubService()
        
        # Create a new branch for this update
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"doc_update_{timestamp}"
        await github_service.create_branch(branch_name)
        logger.info(f"✅ Created new branch: {branch_name}")

        # Create multiple files based on document structure
        logger.info("\n📁 Step 4a: Creating documentation files...")
        created_files = []
        
        # Create main document file
        main_file_path = f"docs/{structure['sections'][0].file_path}"
        main_file_url = await github_service.commit_markdown_file(
            file_path=main_file_path,
            content=formatted_content,
            commit_message=f"Add main documentation: {doc_content['title']}",
            branch=branch_name
        )
        created_files.append(main_file_path)
        logger.info(f"✅ Created main file: {main_file_path}")

        # Create individual section files if they have substantial content
        for section in structure['sections']:
            if section.content.strip() and len(section.content.strip()) > 100:  # Only create files for sections with content
                section_file_path = f"docs/{section.file_path}"
                
                # Extract section content and format it
                section_content = f"# {section.title}\n\n{section.content.strip()}"
                section_formatted = template_engine.apply_template(
                    section_content,
                    template_name,
                    metadata={
                        "title": section.title,
                        "description": f"Section: {section.title}",
                        "template": template_name
                    }
                )
                
                try:
                    section_file_url = await github_service.commit_markdown_file(
                        file_path=section_file_path,
                        content=section_formatted,
                        commit_message=f"Add section: {section.title}",
                        branch=branch_name
                    )
                    created_files.append(section_file_path)
                    logger.info(f"✅ Created section file: {section_file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create section file {section_file_path}: {e}")

        # 5. Update mkdocs.yml navigation with the new structure
        logger.info("\n🧭 Step 5: Updating MkDocs navigation...")
        
        # Generate a clean navigation structure for the new content
        clean_navigation = nav_manager.generate_mkdocs_navigation(structure, template_name)
        
        # Update the mkdocs.yml file with the new navigation
        nav_url = await github_service.update_mkdocs_nav(
            new_file_path=main_file_path,
            title=doc_content['title'],
            branch=branch_name
        )
        logger.info("✅ Updated MkDocs navigation")

        # 6. Create Pull Request
        logger.info("\n🔃 Step 6: Creating Pull Request...")
        
        # Generate detailed PR description
        pr_body = f"""
## Automated Documentation Update

This PR contains updates from Google Docs document: **{doc_content['title']}**

### 📊 Document Analysis
- **Total Sections**: {structure['metadata']['total_sections']}
- **Max Depth**: {structure['metadata']['max_depth']}
- **Estimated Pages**: {structure['metadata']['estimated_pages']}
- **Suggested Template**: {structure['suggested_template']}

### 📁 Files Created/Updated
"""
        
        for file_path in created_files:
            pr_body += f"- `{file_path}`\n"
        
        pr_body += f"""
### 🧭 Navigation Structure
The document structure has been analyzed and navigation has been automatically generated based on the heading hierarchy.

### 📝 Source Information
- **Google Doc ID**: `{doc_id}`
- **Processing Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Template Applied**: {template_name}

### 🔍 What This Does
1. Analyzes the Google Doc structure using heading levels
2. Generates appropriate file paths and navigation
3. Applies consistent formatting using the {template_name} template
4. Creates a Pull Request for review and deployment

Please review the changes and merge to update the documentation site.
        """.strip()

        pr_url = await github_service.create_pull_request(
            branch_name=branch_name,
            title=f"Documentation Update: {doc_content['title']}",
            body=pr_body
        )
        logger.info(f"✅ Created Pull Request: {pr_url}")

        # 7. Display summary and next steps
        logger.info("\n🎉 Documentation update process completed successfully!")
        logger.info("\n📋 Summary:")
        logger.info(f"   📄 Document: {doc_content['title']}")
        logger.info(f"   🧭 Sections analyzed: {len(structure['sections'])}")
        logger.info(f"   📁 Files created: {len(created_files)}")
        logger.info(f"   🎨 Template used: {template_name}")
        
        logger.info("\n📝 Generated Navigation Structure:")
        logger.info(clean_navigation)
        
        logger.info("\n🚀 Next Steps:")
        logger.info("1. Review the Pull Request: " + pr_url)
        logger.info("2. Merge the PR to trigger MkDocs deployment")
        logger.info("3. Wait for GitHub Actions to complete")
        logger.info("4. View the updated documentation site")
        
        return {
            "status": "success",
            "doc_title": doc_content['title'],
            "structure": structure,
            "created_files": created_files,
            "template_used": template_name,
            "navigation": clean_navigation,
            "pr_url": pr_url
        }

    except Exception as e:
        logger.error(f"❌ Error in documentation update process: {str(e)}")
        raise

if __name__ == "__main__":
    print("\n=== Google Docs to MkDocs Automation POC (Enhanced) ===\n")
    print("🚀 Now with intelligent navigation management and structure analysis!")
    print("=" * 70)
    load_dotenv()
    asyncio.run(run_documentation_update())

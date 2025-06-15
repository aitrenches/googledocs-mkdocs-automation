import asyncio
import os
from dotenv import load_dotenv
from app.services.google_docs import GoogleDocsService
from app.services.ai_converter import AIConverter
from app.services.github_service import GitHubService
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_documentation_update():
    """
    End-to-end POC demonstration of automated documentation update:
    Google Docs → Markdown → MkDocs → Deployed Site
    """
    try:
        logger.info("🚀 Starting automated documentation update process...")
        
        # 1. Get content from Google Docs
        logger.info("\n📄 Step 1: Fetching Google Docs content...")
        docs_service = GoogleDocsService()
        doc_id = os.getenv('DOCUMENT_ID')  # Your test doc
        doc_content = docs_service.get_document_content(doc_id)
        logger.info(f"✅ Retrieved document: '{doc_content['title']}'")

        # 2. Convert to Markdown
        logger.info("\n🔄 Step 2: Converting to Markdown format...")
        ai_converter = AIConverter()
        markdown_content = await ai_converter.convert_to_markdown(doc_content['raw_content'])
        logger.info("✅ Content converted to Markdown")
        
        # 3. Create GitHub Branch and Updates
        logger.info("\n📦 Step 3: Creating GitHub updates...")
        github_service = GitHubService()
        
        # Create a new branch for this update
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"doc_update_{timestamp}"
        await github_service.create_branch(branch_name)
        logger.info(f"✅ Created new branch: {branch_name}")

        # Simplified file path
        file_path = "docs/auto_page.md"
        
        # Commit the markdown file
        file_url = await github_service.commit_markdown_file(
            file_path=file_path,
            content=markdown_content,
            commit_message=f"Update documentation from Google Doc: {doc_content['title']}",
            branch=branch_name
        )
        logger.info(f"✅ Committed markdown file: {file_url}")

        # Update mkdocs.yml navigation
        nav_url = await github_service.update_mkdocs_nav(
            new_file_path=file_path,
            title="Automated Page",
            branch=branch_name
        )
        logger.info("✅ Updated MkDocs navigation")

        # 4. Create Pull Request
        logger.info("\n🔃 Step 4: Creating Pull Request...")
        pr_url = await github_service.create_pull_request(
            branch_name=branch_name,
            title=f"Documentation Update: {doc_content['title']}",
            body=f"""
## Automated Documentation Update

This PR contains updates from Google Docs document: {doc_content['title']}

### Changes:
- Added/Updated: `{file_path}`
- Updated MkDocs navigation
- Source: Google Doc ID `{doc_id}`

Please review the changes and merge to update the documentation site.
            """.strip()
        )
        logger.info(f"✅ Created Pull Request: {pr_url}")

        logger.info("\n🎉 Documentation update process completed successfully!")
        logger.info("\nNext Steps:")
        logger.info("1. Review the Pull Request: " + pr_url)
        logger.info("2. Merge the PR to trigger MkDocs deployment")
        logger.info("3. Wait for GitHub Actions to complete")
        logger.info("4. View the updated documentation site")
        
        return {
            "status": "success",
            "doc_title": doc_content['title'],
            "file_url": file_url,
            "pr_url": pr_url
        }

    except Exception as e:
        logger.error(f"❌ Error in documentation update process: {str(e)}")
        raise

if __name__ == "__main__":
    print("\n=== Google Docs to MkDocs Automation POC ===\n")
    load_dotenv()
    asyncio.run(run_documentation_update())

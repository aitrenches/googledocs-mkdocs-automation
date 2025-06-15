from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
import logging
from .services.google_docs import GoogleDocsService
from .services.ai_converter import AIConverter
from .services.github_service import GitHubService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Pydantic models for request/response validation
class DocumentRequest(BaseModel):
    doc_id: str
    target_path: Optional[str] = None
    branch_name: Optional[str] = None
    create_pr: bool = True

class ConversionResponse(BaseModel):
    status: str
    title: str
    github_url: Optional[HttpUrl] = None
    pr_url: Optional[HttpUrl] = None
    message: str

class DocumentInfo(BaseModel):
    title: str
    last_modified: datetime
    url: HttpUrl

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Google Docs to MkDocs Converter",
    description="""
    An API service that automatically converts Google Docs content to MkDocs documentation.
    Features:
    - Fetch Google Docs content
    - Convert to Markdown using AI
    - Update MkDocs documentation
    - Create GitHub Pull Requests
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
docs_service = GoogleDocsService()
ai_converter = AIConverter()
github_service = GitHubService()

@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Google Docs to MkDocs Converter",
        "version": "1.0.0"
    }

@app.get("/api/docs/{doc_id}", 
         response_model=DocumentInfo,
         tags=["Google Docs"])
async def get_document_info(
    doc_id: str = Path(..., description="The Google Document ID")
):
    """
    Get metadata about a Google Document without converting it
    """
    try:
        doc_info = docs_service.get_document_info(doc_id)
        return DocumentInfo(
            title=doc_info["title"],
            last_modified=doc_info["last_modified"],
            url=f"https://docs.google.com/document/d/{doc_id}"
        )
    except Exception as e:
        logger.error(f"Error fetching document info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert", 
          response_model=ConversionResponse,
          tags=["Conversion"])
async def convert_document(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
):
    """
    Convert a Google Doc to Markdown and update MkDocs documentation
    """
    try:
        # Get document content
        doc_content = docs_service.get_document_content(request.doc_id)
        
        # Generate branch name if not provided
        branch_name = request.branch_name or f"doc_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Determine target path
        target_path = request.target_path
        if not target_path:
            clean_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                                for c in doc_content["title"]).lower()
            target_path = f"docs/{clean_title}.md"

        # Convert to markdown
        markdown_content = await ai_converter.convert_to_markdown(doc_content['raw_content'])

        # Create new branch
        await github_service.create_branch(branch_name)

        # Commit changes
        file_url = await github_service.commit_markdown_file(
            file_path=target_path,
            content=markdown_content,
            commit_message=f"Update documentation: {doc_content['title']}",
            branch=branch_name
        )

        # Update navigation
        await github_service.update_mkdocs_nav(
            new_file_path=target_path,
            title=doc_content['title'],
            branch=branch_name
        )

        # Create PR if requested
        pr_url = None
        if request.create_pr:
            pr_url = await github_service.create_pull_request(
                branch_name=branch_name,
                title=f"Documentation Update: {doc_content['title']}",
                body=f"""
## Automated Documentation Update

This PR contains updates from Google Docs document: {doc_content['title']}

### Changes:
- Added/Updated: `{target_path}`
- Updated MkDocs navigation
- Source: Google Doc ID `{request.doc_id}`

Please review the changes and merge to update the documentation site.
                """.strip()
            )

        return ConversionResponse(
            status="success",
            title=doc_content['title'],
            github_url=file_url,
            pr_url=pr_url,
            message="Documentation update completed successfully"
        )

    except Exception as e:
        logger.error(f"Error in conversion process: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "doc_id": request.doc_id,
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/status", tags=["Health"])
async def get_service_status():
    """
    Get the status of all connected services
    """
    try:
        status = {
            "google_docs": await docs_service.check_service(),
            "github": await github_service.check_service(),
            "ai_converter": await ai_converter.check_service(),
        }
        return {
            "status": "healthy" if all(status.values()) else "degraded",
            "services": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-pr", 
          response_model=ConversionResponse,
          tags=["GitHub"])
async def create_pull_request(
    doc_id: str = Query(..., description="The Google Document ID"),
    branch_name: Optional[str] = Query(None, description="Custom branch name (optional)"),
    pr_title: Optional[str] = Query(None, description="Custom PR title (optional)")
):
    """
    Create a GitHub Pull Request for documentation updates.
    This endpoint:
    1. Fetches the Google Doc content
    2. Converts it to Markdown
    3. Creates a new branch
    4. Commits the changes
    5. Creates a Pull Request
    """
    try:
        # Get document content
        doc_content = docs_service.get_document_content(doc_id)
        
        # Generate branch name if not provided
        branch_name = branch_name or f"doc_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Convert to markdown
        markdown_content = await ai_converter.convert_to_markdown(doc_content['raw_content'])

        # Create file path from document title
        clean_title = "".join(c if c.isalnum() or c in ('-', '_') else '_' 
                            for c in doc_content["title"]).lower()
        file_path = f"docs/{clean_title}.md"

        # Create new branch
        await github_service.create_branch(branch_name)

        # Commit changes
        file_url = await github_service.commit_markdown_file(
            file_path=file_path,
            content=markdown_content,
            commit_message=f"Update documentation: {doc_content['title']}",
            branch=branch_name
        )

        # Update navigation
        await github_service.update_mkdocs_nav(
            new_file_path=file_path,
            title=doc_content['title'],
            branch=branch_name
        )

        # Create PR with custom or default title
        pr_title = pr_title or f"Documentation Update: {doc_content['title']}"
        pr_url = await github_service.create_pull_request(
            branch_name=branch_name,
            title=pr_title,
            body=f"""
## Automated Documentation Update

This PR contains updates from Google Docs document: {doc_content['title']}

### Changes:
- Added/Updated: `{file_path}`
- Updated MkDocs navigation
- Source: Google Doc ID `{doc_id}`

### Preview
Once this PR is merged, the documentation will be automatically deployed.

### Automated Changes
- Created new branch: `{branch_name}`
- Converted Google Doc to Markdown
- Updated MkDocs navigation
- Created Pull Request
            """.strip()
        )

        return ConversionResponse(
            status="success",
            title=doc_content['title'],
            github_url=file_url,
            pr_url=pr_url,
            message=f"Pull Request created successfully: {pr_url}"
        )

    except Exception as e:
        logger.error(f"Error creating pull request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "doc_id": doc_id,
                "timestamp": datetime.now().isoformat()
            }
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

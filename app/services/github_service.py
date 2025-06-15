from github import Github
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GitHubService:
    def __init__(self):
        """Initialize GitHub service with credentials"""
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        
        if not all([self.token, self.repo_name]):
            raise ValueError("GitHub credentials not found in environment variables")
        
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)

    async def commit_markdown_file(self, file_path: str, content: str, commit_message: str = None, branch: str = "main") -> str:
        """
        Commit a markdown file to the specified branch
        
        Args:
            file_path (str): Path where the file should be saved in the repo
            content (str): Markdown content to commit
            commit_message (str, optional): Custom commit message
            branch (str): Name of the branch to commit to
            
        Returns:
            str: URL of the committed file
        """
        try:
            # Ensure the file path ends with .md
            if not file_path.endswith('.md'):
                file_path += '.md'

            # Generate commit message if not provided
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Update documentation: {file_path} at {timestamp}"

            try:
                # Try to get the file first to update it
                file = self.repo.get_contents(file_path, ref=branch)
                self.repo.update_file(
                    file_path,
                    commit_message,
                    content,
                    file.sha,
                    branch=branch
                )
                logger.info(f"Updated file {file_path}")
            except Exception:
                # File doesn't exist, create it
                self.repo.create_file(
                    file_path,
                    commit_message,
                    content,
                    branch=branch
                )
                logger.info(f"Created new file {file_path}")

            # Return the URL to the file
            return f"https://github.com/{self.repo_name}/blob/{branch}/{file_path}"

        except Exception as e:
            logger.error(f"Error in commit_markdown_file: {str(e)}")
            raise

    async def create_pull_request(self, branch_name: str, title: str, body: str) -> str:
        """
        Create a pull request for the changes
        
        Args:
            branch_name (str): Name of the branch with changes
            title (str): PR title
            body (str): PR description
            
        Returns:
            str: URL of the created pull request
        """
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base="main"
            )
            return pr.html_url
        except Exception as e:
            logger.error(f"Error in create_pull_request: {str(e)}")
            raise

    async def update_mkdocs_nav(self, new_file_path: str, title: str, branch: str = "main") -> str:
        """
        Update mkdocs.yml navigation with new file
        """
        try:
            # Get current mkdocs.yml
            config_file = self.repo.get_contents("mkdocs.yml", ref=branch)
            current_config = config_file.decoded_content.decode()
            
            # Remove 'docs/' from the file path for nav
            nav_path = new_file_path.replace('docs/', '')
            
            # Simple nav update - ensure proper formatting
            if 'nav:' in current_config:
                nav_lines = current_config.split('\n')
                new_lines = []
                nav_added = False
                
                for line in nav_lines:
                    if line.strip().startswith('nav:'):
                        new_lines.append(line)
                        new_lines.append(f"  - {title}: {nav_path}")
                        nav_added = True
                    elif not nav_added and line.strip().startswith('- Home:'):
                        new_lines.append(f"  - {title}: {nav_path}")
                        new_lines.append(line)
                        nav_added = True
                    else:
                        new_lines.append(line)
                
                new_config = '\n'.join(new_lines)
                
                # Update mkdocs.yml
                self.repo.update_file(
                    "mkdocs.yml",
                    f"Update navigation: add {title}",
                    new_config,
                    config_file.sha,
                    branch=branch
                )
                
            return f"https://github.com/{self.repo_name}/blob/{branch}/mkdocs.yml"
        except Exception as e:
            logger.error(f"Error updating mkdocs.yml: {str(e)}")
            raise

    async def create_branch(self, branch_name: str) -> str:
        """
        Create a new branch from main
        """
        try:
            # Get main branch's HEAD
            main_branch = self.repo.get_branch("main")
            
            # Create new branch
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_branch.commit.sha
            )
            return branch_name
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            raise

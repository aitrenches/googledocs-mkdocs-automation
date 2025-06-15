from github import Github
import os
from dotenv import load_dotenv

load_dotenv()

def test_github_access():
    token = os.getenv('GITHUB_TOKEN')
    repo_name = os.getenv('GITHUB_REPO')
    
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        print(f"✅ Successfully accessed repository: {repo.full_name}")
        print(f"✅ Repository permissions: {repo.permissions}")
        return True
    except Exception as e:
        print(f"❌ Error accessing repository: {str(e)}")
        return False

if __name__ == "__main__":
    test_github_access()

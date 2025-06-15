# Google Docs to MkDocs Automation Setup Guide

This guide explains how to set up and configure the automated documentation system that converts Google Docs content to MkDocs pages.

## Prerequisites

- Python 3.8+
- A Google Cloud Project
- An Azure OpenAI account
- A GitHub repository
- MkDocs with Material theme

## 1. Google Cloud Setup

### 1.1 Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Name it (e.g., "docs-to-mkdocs")
4. Click "Create"

### 1.2 Enable Required APIs
1. Go to "APIs & Services" → "Library"
2. Search for and enable these APIs:
   - Google Docs API
   - Google Drive API
   - Google Sheets API (optional)

### 1.3 Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in:
   - Name: "docs-to-mkdocs-service"
   - Description: "Service account for MkDocs automation"
4. Click "Create and Continue"
5. For Role, select "Basic" → "Editor"
6. Click "Continue" → "Done"

### 1.4 Generate JSON Key
1. Find your service account in the list
2. Click on it → "Keys" tab
3. "Add Key" → "Create new key"
4. Choose JSON format
5. Download and rename to `google_credentials.json`

## 2. Azure OpenAI Setup

1. Access your Azure OpenAI service
2. Note down:
   - API Key
   - Endpoint URL
   - Deployment name

## 3. GitHub Setup

### 3.1 Create Personal Access Token
1. Go to GitHub.com → Settings → Developer Settings
2. Personal Access Tokens → Tokens (classic)
3. Generate new token (classic)
4. Name it "MkDocs Documentation Automation"
5. Select scopes:
   - `repo` (all)
   - `workflow`
6. Copy the token immediately

### 3.2 Repository Setup
1. Create or select your documentation repository
2. Enable GitHub Pages:
   - Go to repository Settings → Pages
   - Source: GitHub Actions

## 4. Local Environment Setup

### 4.1 Clone and Install
```bash
git clone <your-repo-url>
cd <repo-name>
python -m venv env
source env/bin/activate  # or `env\\Scripts\\activate` on Windows
pip install -r requirements.txt
```

### 4.2 Environment Variables
Create a `.env` file in your project root:

```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=./google_credentials.json

# Azure OpenAI
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# GitHub
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=username/repository
```

## 5. Getting Document ID

1. Open your Google Doc
2. Share it with the service account email (found in `google_credentials.json`)
3. From the URL:
   ```
   https://docs.google.com/document/d/YOUR_DOCUMENT_ID/edit
   ```
   Copy `YOUR_DOCUMENT_ID`

## 6. Testing the Setup

Run the integration test:
```bash
python test_integration.py
```

You should see:
1. Content fetched from Google Docs
2. Conversion to Markdown
3. GitHub branch creation
4. Pull request creation
5. Links to review the changes

## 7. MkDocs Configuration

Ensure your `mkdocs.yml` has the basic configuration:

```yaml
site_name: Your Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest

nav:
  - Home: index.md

plugins:
  - search
```

## Troubleshooting

### Common Issues

1. **Google API Error**
   - Check if credentials file is properly located
   - Verify APIs are enabled
   - Ensure document is shared with service account

2. **Azure OpenAI Error**
   - Verify API key and endpoint
   - Check deployment name
   - Confirm service is active

3. **GitHub Error**
   - Verify token permissions
   - Check repository name format
   - Ensure token hasn't expired

4. **MkDocs Build Error**
   - Verify mkdocs.yml syntax
   - Check file paths in navigation
   - Ensure all referenced files exist

## Security Notes

1. Never commit `.env` or `google_credentials.json`
2. Rotate GitHub tokens periodically
3. Use minimal required permissions
4. Monitor API usage

## Next Steps

1. Customize the markdown conversion
2. Add more error handling
3. Set up automated triggers
4. Implement content validation

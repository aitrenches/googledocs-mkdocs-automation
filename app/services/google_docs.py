from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

class GoogleDocsService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        self.service = build('docs', 'v1', credentials=credentials)

    def extract_text_content(self, document):
        """Extract plain text content from Google Doc"""
        content = []
        for element in document.get('body').get('content'):
            if 'paragraph' in element:
                paragraph = element.get('paragraph')
                for elem in paragraph.get('elements'):
                    if 'textRun' in elem:
                        content.append(elem.get('textRun').get('content'))
        return ''.join(content)

    def get_document_content(self, doc_id: str):
        """Get document content and metadata"""
        document = self.service.documents().get(documentId=doc_id).execute()
        return {
            "title": document.get('title', ''),
            "content": self.extract_text_content(document),
            "raw_content": document
        }

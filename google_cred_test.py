from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
import json

def test_google_setup():
    print("\n=== Google API Setup Test ===\n")
    
    # 1. Check if credentials file exists
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"Looking for credentials file...")
    if not creds_path or not os.path.exists(creds_path):
        print("❌ Error: Credentials file not found!")
        print(f"Expected path: {creds_path}")
        return False
    print("✅ Credentials file found")

    try:
        # 2. Load credentials
        print("\nTesting credentials loading...")
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=[
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        print("✅ Credentials loaded successfully")

        # 3. Test building services
        print("\nTesting service creation...")
        docs_service = build('docs', 'v1', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Services created successfully")

        # 4. Test basic API call
        print("\nTesting API access...")
        # List first 5 files in Drive to test access
        results = drive_service.files().list(
            pageSize=5,
            fields="nextPageToken, files(id, name)"
        ).execute()
        files = results.get('files', [])
        
        if not files:
            print("No files found in Drive (this might be normal for a new service account)")
        else:
            print("✅ Successfully accessed Google Drive")
            print("\nFound these files:")
            for file in files:
                print(f"- {file['name']} ({file['id']})")

        print("\n✅ All basic tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    print("Loading environment variables...")
    load_dotenv()
    test_google_setup()
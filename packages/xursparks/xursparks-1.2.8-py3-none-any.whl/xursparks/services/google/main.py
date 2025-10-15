from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import base64
import pickle
from typing import Optional, Dict, Any, Union
import json
import os
import io

class XGoogleDriveReader:
    """Class to handle Google Drive operations and read Google Sheets"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, auth_file_path: str = 'auth/service-account-gdrive.json',
                 scopes: list = SCOPES):
        """
        Initialize GoogleDriveReader with service account credentials
        
        Args:
            auth_file_path: Path to service account JSON file (relative or absolute)
        """
        try:
            # Get absolute path if relative path provided
            if not os.path.isabs(auth_file_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                auth_file_path = os.path.join(current_dir, auth_file_path)
            
            # Load credentials from JSON file
            with open(auth_file_path, 'r') as f:
                self.credentials = json.load(f)
                
            self.creds = None
            self.service = None
            self.sheets_service = None
            self.scopes = scopes
            
        except Exception as e:
            raise ValueError(f"Failed to load authentication file: {str(e)}")

    def authenticate(self) -> bool:
        """Authenticate with Google Drive API using service account"""
        try:

            self.creds = service_account.Credentials.from_service_account_info(
                self.credentials,
                scopes=self.scopes
            )
            
            self.service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
            print("Successfully authenticated with service account")
            return True
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            return False
    
    def get_file_id(self, file_path: str, mime_type: str = None) -> Optional[str]:
        """
        Get Google Drive file ID by path
        
        Args:
            file_path: Full path to the file in Google Drive (e.g. 'folder1/folder2/filename')
            mime_type: Optional MIME type filter
            
        Returns:
            str: File ID if found, None otherwise
        """
        try:
            path_parts = file_path.strip('/').split('/')
            file_name = path_parts[-1]
            parent_path = '/'.join(path_parts[:-1])
            
            # Build query
            query = f"name='{file_name}'"
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            # Add parent folder constraints if path provided
            if parent_path:
                parent_id = self._get_folder_id(parent_path)
                if parent_id:
                    query += f" and '{parent_id}' in parents"
                    
            results = self.service.files().list(
                q=query,
                fields="files(id, name)").execute()
            items = results.get('files', [])
            
            if not items:
                print(f"File '{file_path}' not found")
                return None
                
            return items[0]['id']
            
        except Exception as e:
            print(f"Error getting file ID: {str(e)}")
            return None

    def _get_folder_id(self, folder_path: str) -> Optional[str]:
        """
        Get folder ID from path
        
        Args:
            folder_path: Path to folder (e.g. 'folder1/folder2')
            
        Returns:
            str: Folder ID if found, None otherwise
        """
        try:
            current_parent = 'root'
            
            for folder in folder_path.split('/'):
                query = f"name='{folder}' and mimeType='application/vnd.google-apps.folder'"
                if current_parent != 'root':
                    query += f" and '{current_parent}' in parents"
                    
                results = self.service.files().list(
                    q=query,
                    fields="files(id)").execute()
                items = results.get('files', [])
                
                if not items:
                    print(f"Folder '{folder}' not found in path '{folder_path}'")
                    return None
                    
                current_parent = items[0]['id']
                
            return current_parent
            
        except Exception as e:
            print(f"Error getting folder ID: {str(e)}")
            return None

    def read_sheet(self, 
                   file_path: str, 
                   sheet_name: Optional[str] = None,
                   range_name: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Read Google Sheet into pandas DataFrame
        
        Args:
            file_path: Full path to the file in Google Drive (e.g. 'folder1/folder2/filename')
            sheet_name: Optional sheet name (default: first sheet)
            range_name: Optional range to read (default: all)
            
        Returns:
            pd.DataFrame: DataFrame containing sheet data
        """
        try:
            # Get file ID - Updated method name
            file_id = self.get_file_id(file_path)
            if not file_id:
                return None
            
            # Get sheet properties
            sheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=file_id).execute()
            
            if not sheet_name:
                sheet_name = sheet_metadata['sheets'][0]['properties']['title']
            
            # Construct range
            range_str = f"'{sheet_name}'"
            if range_name:
                range_str += f"!{range_name}"
            
            # Read data
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=file_id,
                range=range_str).execute()
            
            values = result.get('values', [])
            if not values:
                print("No data found in sheet")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
            
        except Exception as e:
            print(f"Error reading sheet: {str(e)}")
            return None

    def download_file(self, 
                     file_path: str, 
                     local_path: str,
                     mime_type: str = None) -> bool:
        """
        Download file from Google Drive
        
        Args:
            file_path: Full path to file in Google Drive (e.g. 'folder1/folder2/filename')
            local_path: Local path where to save the file
            mime_type: Optional MIME type for export (for Google Docs, Sheets etc.)
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # Get file ID using the new method
            file_id = self.get_file_id(file_path)
            if not file_id:
                print(f"File not found: {file_path}")
                return False

            # Create local directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download the file
            if mime_type:
                # Export Google Workspace files
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=mime_type
                )
            else:
                # Download regular files
                request = self.service.files().get_media(
                    fileId=file_id
                )

            # Stream the file content
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download progress: {int(status.progress() * 100)}%")

            # Save the file
            fh.seek(0)
            with open(local_path, 'wb') as f:
                f.write(fh.read())
                f.flush()

            print(f"File downloaded successfully to: {local_path}")
            return True

        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False

    def list_files(self, folder_path: str = '') -> Optional[list]:
        """
        List all files and subfolders in the specified Google Drive folder
        
        Args:
            folder_path: Path to folder in Google Drive (e.g. 'folder1/folder2')
                        Empty string '' means root folder
            
        Returns:
            list: List of dictionaries containing file/folder information with structure:
                  [{'name': str, 'id': str, 'type': str, 'path': str}, ...]
            None: If error occurs
        """
        try:
            # Get folder ID for the path
            folder_id = 'root' if not folder_path else self._get_folder_id(folder_path)
            if folder_path and not folder_id:
                return None

            # Build query to list all files/folders in the directory
            query = f"'{folder_id}' in parents and trashed=false"
            
            # Get list of all files/folders
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType)',
                    pageToken=page_token
                ).execute()
                
                for file in response.get('files', []):
                    file_type = 'folder' if file['mimeType'] == 'application/vnd.google-apps.folder' else 'file'
                    file_path = os.path.join(folder_path, file['name']) if folder_path else file['name']
                    
                    results.append({
                        'name': file['name'],
                        'id': file['id'],
                        'type': file_type,
                        'path': file_path
                    })
                    
                    # Recursively list files in subfolders
                    if file_type == 'folder':
                        sub_files = self.list_files(file_path)
                        if sub_files:
                            results.extend(sub_files)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return results
            
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return None

# Example usage
def read_sheet_from_gdrive():
    # Initialize reader with default auth file path
    reader = XGoogleDriveReader()
    
    # Or specify a different path
    # reader = XGoogleDriveReader('path/to/different/auth.json')
    
    # Authenticate
    if reader.authenticate():
        df = reader.read_sheet(
            file_path="DSWD-Sheets/Chill",
            sheet_name="0825_DS",
            range_name="B2:E16"
        )
        
        if df is not None:
            print(df.head())

def download_file_from_gdrive():
    reader = XGoogleDriveReader("/home/hadoop/tests/hpmeis-7784af30c873.json")
    
    if reader.authenticate():
        # Download Google Sheet as Excel
        success = reader.download_file(
            file_path="HPMEIS/AICS.xlsx",
            local_path="/home/hadoop/poc/my_sheet.xlsx"
        )
    print(f"Download success: {success}")

def list_files_from_gdrive():
    """Example usage of list_files function"""
    reader = XGoogleDriveReader("/home/hadoop/tests/hpmeis-7784af30c873.json")
    
    if reader.authenticate():
        # List all files in a specific folder
        files = reader.list_files("HPMEIS")
        
        if files:
            print("\nFiles found:")
            for file in files:
                prefix = "📁" if file['type'] == 'folder' else "📄"
                print(f"{prefix} {file['path']}")
                
if __name__ == "__main__":
    # read_sheet_from_gdrive()
    list_files_from_gdrive()
    download_file_from_gdrive()
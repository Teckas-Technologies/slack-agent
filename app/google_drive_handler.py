# google_drive_handler.py
import os
import io
import logging
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import json
import mimetypes

# Disable Google API discovery cache warnings
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


class GoogleDriveHandler:
    """Handle Google Drive document operations"""

    # Supported MIME types and their handlers
    SUPPORTED_TYPES = {
        # Google Workspace documents
        'application/vnd.google-apps.document': 'google_doc',
        'application/vnd.google-apps.spreadsheet': 'google_sheet',
        'application/vnd.google-apps.presentation': 'google_slides',

        # Microsoft Office documents
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        'application/msword': 'doc',
        'application/vnd.ms-excel': 'xls',
        'application/vnd.ms-powerpoint': 'ppt',

        # PDF and text
        'application/pdf': 'pdf',
        'text/plain': 'txt',
        'text/markdown': 'markdown',
        'text/csv': 'csv',

        # Other formats
        'application/json': 'json',
        'application/xml': 'xml',
        'text/html': 'html'
    }

    def __init__(self):
        self.service = self._initialize_drive_service()

    def _initialize_drive_service(self):
        """Initialize Google Drive service"""
        try:
            # Try service account first (for production)
            if os.path.exists(os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY', '')):
                credentials = ServiceAccountCredentials.from_service_account_file(
                    os.environ['GOOGLE_SERVICE_ACCOUNT_KEY'],
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            else:
                # Use OAuth2 credentials (for development)
                creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
                if os.path.exists(creds_path):
                    with open(creds_path, 'r') as f:
                        creds_data = json.load(f)

                    credentials = Credentials.from_authorized_user_info(
                        creds_data,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                else:
                    raise FileNotFoundError("No Google credentials found")

            return build('drive', 'v3', credentials=credentials)

        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            raise

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all supported documents from Google Drive"""
        try:
            documents = []
            page_token = None

            while True:
                # Build query for supported file types
                mime_types = list(self.SUPPORTED_TYPES.keys())
                query_parts = [f"mimeType='{mime_type}'" for mime_type in mime_types]
                query = " or ".join(query_parts)
                query += " and trashed=false"

                results = self.service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, parents, webViewLink)",
                    pageToken=page_token,
                    pageSize=100
                ).execute()

                files = results.get('files', [])
                for file in files:
                    doc_info = {
                        'id': file['id'],
                        'name': file['name'],
                        'mime_type': file['mimeType'],
                        'modified_time': file['modifiedTime'],
                        'size': file.get('size', 0),
                        'source': 'google_drive',
                        'url': file.get('webViewLink', ''),
                        'parents': file.get('parents', [])
                    }
                    documents.append(doc_info)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            logger.info(f"Found {len(documents)} documents in Google Drive")
            return documents

        except Exception as e:
            logger.error(f"Error fetching documents from Google Drive: {str(e)}")
            return []

    def get_document_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from a document based on its type"""
        try:
            mime_type = document['mime_type']
            file_id = document['id']

            if mime_type not in self.SUPPORTED_TYPES:
                logger.warning(f"Unsupported file type: {mime_type}")
                return {'content': '', 'error': f'Unsupported file type: {mime_type}'}

            handler_type = self.SUPPORTED_TYPES[mime_type]

            # Route to appropriate handler
            if handler_type == 'google_doc':
                return self._extract_google_doc(file_id)
            elif handler_type == 'google_sheet':
                return self._extract_google_sheet(file_id)
            elif handler_type == 'google_slides':
                return self._extract_google_slides(file_id)
            elif handler_type == 'pdf':
                return self._extract_pdf(file_id)
            elif handler_type in ['docx', 'doc']:
                return self._extract_word_doc(file_id)
            elif handler_type in ['xlsx', 'xls']:
                return self._extract_excel(file_id)
            elif handler_type == 'csv':
                return self._extract_csv(file_id)
            elif handler_type in ['txt', 'markdown', 'html', 'xml', 'json']:
                return self._extract_text_file(file_id)
            else:
                return self._extract_generic_file(file_id)

        except Exception as e:
            logger.error(f"Error extracting content from {document['name']}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _download_file(self, file_id: str, mime_type: str = None) -> bytes:
        """Download file content"""
        if mime_type and mime_type.startswith('application/vnd.google-apps'):
            # For Google Workspace files, export to appropriate format
            export_formats = {
                'application/vnd.google-apps.document': 'text/plain',
                'application/vnd.google-apps.spreadsheet': 'text/csv',
                'application/vnd.google-apps.presentation': 'text/plain'
            }
            export_mime = export_formats.get(mime_type, 'text/plain')
            request = self.service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            request = self.service.files().get_media(fileId=file_id)

        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        return file_io.getvalue()

    def _extract_google_doc(self, file_id: str) -> Dict[str, Any]:
        """Extract content from Google Doc"""
        try:
            content_bytes = self._download_file(file_id, 'application/vnd.google-apps.document')
            content = content_bytes.decode('utf-8')
            return {'content': content, 'type': 'text'}
        except Exception as e:
            logger.error(f"Error extracting Google Doc {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_google_sheet(self, file_id: str) -> Dict[str, Any]:
        """Extract content from Google Sheet"""
        try:
            content_bytes = self._download_file(file_id, 'application/vnd.google-apps.spreadsheet')
            content = content_bytes.decode('utf-8')
            return {'content': content, 'type': 'structured'}
        except Exception as e:
            logger.error(f"Error extracting Google Sheet {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_google_slides(self, file_id: str) -> Dict[str, Any]:
        """Extract content from Google Slides"""
        try:
            content_bytes = self._download_file(file_id, 'application/vnd.google-apps.presentation')
            content = content_bytes.decode('utf-8')
            return {'content': content, 'type': 'text'}
        except Exception as e:
            logger.error(f"Error extracting Google Slides {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_pdf(self, file_id: str) -> Dict[str, Any]:
        """Extract content from PDF"""
        try:
            import PyPDF2
            content_bytes = self._download_file(file_id)

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            text_content = []

            for page in pdf_reader.pages:
                text_content.append(page.extract_text())

            content = '\n\n'.join(text_content)
            return {'content': content, 'type': 'text'}

        except ImportError:
            logger.warning("PyPDF2 not installed, falling back to basic extraction")
            try:
                # Fallback: try to extract as text (may not work for all PDFs)
                content_bytes = self._download_file(file_id)
                content = content_bytes.decode('utf-8', errors='ignore')
                return {'content': content, 'type': 'text'}
            except Exception as e:
                return {'content': '', 'error': f'PDF extraction failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Error extracting PDF {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_word_doc(self, file_id: str) -> Dict[str, Any]:
        """Extract content from Word document"""
        try:
            from docx import Document
            content_bytes = self._download_file(file_id)

            doc = Document(io.BytesIO(content_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = '\n\n'.join(paragraphs)

            return {'content': content, 'type': 'text'}

        except ImportError:
            logger.warning("python-docx not installed, cannot extract Word documents")
            return {'content': '', 'error': 'python-docx not installed'}
        except Exception as e:
            logger.error(f"Error extracting Word doc {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_excel(self, file_id: str) -> Dict[str, Any]:
        """Extract content from Excel file"""
        try:
            import pandas as pd
            content_bytes = self._download_file(file_id)

            # Read all sheets
            excel_file = pd.ExcelFile(io.BytesIO(content_bytes))
            sheets_content = []

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheet_text = f"Sheet: {sheet_name}\n" + df.to_string()
                sheets_content.append(sheet_text)

            content = '\n\n'.join(sheets_content)
            return {'content': content, 'type': 'structured'}

        except ImportError:
            logger.warning("pandas not installed, cannot extract Excel files")
            return {'content': '', 'error': 'pandas not installed'}
        except Exception as e:
            logger.error(f"Error extracting Excel file {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_csv(self, file_id: str) -> Dict[str, Any]:
        """Extract content from CSV file"""
        try:
            import pandas as pd
            content_bytes = self._download_file(file_id)
            content_str = content_bytes.decode('utf-8')

            # Parse CSV
            df = pd.read_csv(io.StringIO(content_str))
            content = df.to_string()

            return {'content': content, 'type': 'structured'}

        except ImportError:
            # Fallback without pandas
            content_bytes = self._download_file(file_id)
            content = content_bytes.decode('utf-8')
            return {'content': content, 'type': 'structured'}
        except Exception as e:
            logger.error(f"Error extracting CSV {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_text_file(self, file_id: str) -> Dict[str, Any]:
        """Extract content from plain text file"""
        try:
            content_bytes = self._download_file(file_id)
            content = content_bytes.decode('utf-8')
            return {'content': content, 'type': 'text'}
        except Exception as e:
            logger.error(f"Error extracting text file {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _extract_generic_file(self, file_id: str) -> Dict[str, Any]:
        """Generic extraction for unknown file types"""
        try:
            content_bytes = self._download_file(file_id)
            content = content_bytes.decode('utf-8', errors='ignore')
            return {'content': content, 'type': 'text'}
        except Exception as e:
            logger.error(f"Error extracting generic file {file_id}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def get_folder_structure(self) -> Dict[str, Any]:
        """Get folder structure for better organization"""
        try:
            folders = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name, parents)"
            ).execute()

            return folders.get('files', [])

        except Exception as e:
            logger.error(f"Error getting folder structure: {str(e)}")
            return []
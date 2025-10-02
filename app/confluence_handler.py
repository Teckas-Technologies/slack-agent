# confluence_handler.py
import os
import logging
import requests
from typing import List, Dict, Any, Optional
import base64
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


class ConfluenceHandler:
    """Handle Confluence document operations"""

    def __init__(self):
        from config import Config

        # Handle both old and new Confluence API URL formats
        base_url = Config.CONFLUENCE_BASE_URL.rstrip('/') if Config.CONFLUENCE_BASE_URL else ''

        # For newer Confluence Cloud instances, API endpoints are under /wiki
        # Check if we need to add /wiki to the base URL
        if base_url and not base_url.endswith('/wiki'):
            # Test both with and without /wiki to find the correct format
            self.base_url = base_url
            self.base_url_with_wiki = f"{base_url}/wiki"
        else:
            self.base_url = base_url
            self.base_url_with_wiki = base_url

        self.username = Config.CONFLUENCE_USERNAME or ''
        self.api_token = Config.CONFLUENCE_API_TOKEN or ''
        
        # Configuration for organization-wide access
        confluence_spaces = Config.CONFLUENCE_SPACES or ''
        self.organization_spaces = [space.strip() for space in confluence_spaces.split(',') if space.strip()]
        
        if not all([self.base_url, self.username, self.api_token]):
            logger.warning("Confluence credentials not properly configured")
            return

        # Create session with authentication
        self.session = requests.Session()
        auth_string = f"{self.username}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_header = base64.b64encode(auth_bytes).decode('ascii')

        self.session.headers.update({
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        # Determine correct API endpoint format
        self.api_base_url = self._determine_api_endpoint()

        # Test connection
        self._test_connection()

    def _determine_api_endpoint(self) -> str:
        """Determine the correct API endpoint format (with or without /wiki)"""
        try:
            # Try with /wiki first (newer Confluence Cloud format)
            test_url = f"{self.base_url_with_wiki}/rest/api/space"
            response = self.session.get(test_url, params={'limit': 1}, timeout=5)

            if response.status_code in [200, 401, 403]:  # Connection works
                logger.info(f"Using Confluence API endpoint: {self.base_url_with_wiki}")
                return self.base_url_with_wiki

            # Try without /wiki (older format)
            test_url = f"{self.base_url}/rest/api/space"
            response = self.session.get(test_url, params={'limit': 1}, timeout=5)

            if response.status_code in [200, 401, 403]:  # Connection works
                logger.info(f"Using Confluence API endpoint: {self.base_url}")
                return self.base_url

            # Default to /wiki format for Atlassian Cloud
            logger.warning(f"Could not determine Confluence API format, defaulting to: {self.base_url_with_wiki}")
            return self.base_url_with_wiki

        except Exception as e:
            logger.warning(f"Error determining API endpoint: {str(e)}, using default: {self.base_url_with_wiki}")
            return self.base_url_with_wiki

    def _test_connection(self) -> bool:
        """Test Confluence connection"""
        try:
            response = self.session.get(f"{self.api_base_url}/rest/api/space")
            if response.status_code == 200:
                logger.info("Successfully connected to Confluence")
                return True
            else:
                logger.error(f"Failed to connect to Confluence: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing Confluence connection: {str(e)}")
            return False

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get documents from specified organization spaces in Confluence"""
        try:
            if not all([self.base_url, self.username, self.api_token]):
                logger.warning("Confluence not properly configured, returning empty list")
                return []

            documents = []

            # If specific organization spaces are configured, use those
            if self.organization_spaces:
                logger.info(f"Processing configured organization spaces: {', '.join(self.organization_spaces)}")
                
                for space_key in self.organization_spaces:
                    try:
                        logger.info(f"Processing Confluence space: {space_key}")
                        space_documents = self._get_space_documents(space_key)
                        documents.extend(space_documents)
                    except Exception as e:
                        logger.error(f"Error processing space {space_key}: {str(e)}")
                        continue
            else:
                # Fallback: Get all accessible spaces (but warn it's not organization-specific)
                logger.warning("No specific organization spaces configured, fetching all accessible spaces")
                spaces = self._get_spaces()

                for space in spaces:
                    space_key = space['key']
                    logger.info(f"Processing Confluence space: {space_key}")

                    # Get pages from this space
                    space_documents = self._get_space_documents(space_key)
                    documents.extend(space_documents)

            logger.info(f"Found {len(documents)} documents in Confluence")
            return documents

        except Exception as e:
            logger.error(f"Error fetching documents from Confluence: {str(e)}")
            return []

    def _get_spaces(self) -> List[Dict[str, Any]]:
        """Get all accessible spaces"""
        try:
            spaces = []
            start = 0
            limit = 50

            while True:
                url = f"{self.api_base_url}/rest/api/space"
                params = {
                    'start': start,
                    'limit': limit,
                    'type': 'global'
                }

                response = self.session.get(url, params=params)

                if response.status_code != 200:
                    logger.error(f"Error fetching spaces: {response.status_code}")
                    break

                data = response.json()
                results = data.get('results', [])

                spaces.extend(results)

                # Check if there are more results
                if len(results) < limit:
                    break

                start += limit

            return spaces

        except Exception as e:
            logger.error(f"Error getting Confluence spaces: {str(e)}")
            return []

    def _get_space_documents(self, space_key: str) -> List[Dict[str, Any]]:
        """Get all documents from a specific space"""
        try:
            documents = []
            start = 0
            limit = 50

            while True:
                url = f"{self.api_base_url}/rest/api/content"
                params = {
                    'spaceKey': space_key,
                    'start': start,
                    'limit': limit,
                    'type': 'page',
                    'status': 'current',
                    'expand': 'version,space,ancestors'
                }

                logger.info(f"Fetching pages from space {space_key}: {url}")
                response = self.session.get(url, params=params)

                if response.status_code != 200:
                    logger.error(f"Error fetching pages from space {space_key}: {response.status_code}")
                    logger.error(f"Response URL: {response.url}")
                    logger.error(f"Response body: {response.text[:500]}")
                    break

                data = response.json()
                results = data.get('results', [])

                for page in results:
                    # Construct proper web URL - webui link is relative
                    webui_link = page['_links']['webui']
                    # If webui_link starts with /, prepend base_url
                    if webui_link.startswith('/'):
                        # Check if webui already starts with /wiki
                        if webui_link.startswith('/wiki/'):
                            page_url = f"{self.base_url}{webui_link}"
                        else:
                            # Add /wiki to the path
                            page_url = f"{self.base_url}/wiki{webui_link}"
                    else:
                        page_url = webui_link

                    doc_info = {
                        'id': page['id'],
                        'name': page['title'],
                        'space_key': space_key,
                        'space_name': page['space']['name'],
                        'modified_time': page['version']['when'],
                        'version': page['version']['number'],
                        'source': 'confluence',
                        'url': page_url,
                        'type': 'page'
                    }
                    documents.append(doc_info)

                # Check if there are more results
                if len(results) < limit:
                    break

                start += limit

            return documents

        except Exception as e:
            logger.error(f"Error getting documents from space {space_key}: {str(e)}")
            return []

    def get_document_content(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from a Confluence page"""
        try:
            page_id = document['id']

            # Get page content with body
            url = f"{self.api_base_url}/rest/api/content/{page_id}"
            params = {
                'expand': 'body.storage,body.view'
            }

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                error_msg = f"Error fetching page content: {response.status_code}"
                logger.error(error_msg)
                return {'content': '', 'error': error_msg}

            data = response.json()

            # Try to get view body first (rendered HTML), then storage (XHTML)
            content_html = ""

            if 'body' in data:
                if 'view' in data['body'] and data['body']['view']['value']:
                    content_html = data['body']['view']['value']
                elif 'storage' in data['body'] and data['body']['storage']['value']:
                    content_html = data['body']['storage']['value']

            if not content_html:
                return {'content': '', 'error': 'No content found'}

            # Convert HTML to plain text
            text_content = self._html_to_text(content_html)

            # Get page attachments if any
            attachments_content = self._get_page_attachments(page_id)

            # Combine page content with attachment information
            full_content = text_content
            if attachments_content:
                full_content += f"\n\nAttachments:\n{attachments_content}"

            return {
                'content': full_content,
                'type': 'text',
                'html_content': content_html  # Keep original HTML if needed
            }

        except Exception as e:
            logger.error(f"Error extracting content from Confluence page {document.get('name', 'Unknown')}: {str(e)}")
            return {'content': '', 'error': str(e)}

    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Handle specific Confluence elements

            # Convert tables to readable format
            for table in soup.find_all('table'):
                self._convert_table_to_text(table)

            # Convert lists to readable format
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li'):
                    li.insert(0, '• ')

            for ol in soup.find_all('ol'):
                for i, li in enumerate(ol.find_all('li'), 1):
                    li.insert(0, f'{i}. ')

            # Handle code blocks
            for code in soup.find_all(['code', 'pre']):
                code.insert(0, '\n```\n')
                code.append('\n```\n')

            # Handle headings
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                level = int(heading.name[1])
                heading.insert(0, '#' * level + ' ')
                heading.append('\n')

            # Get text and clean up
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text.strip()

        except Exception as e:
            logger.error(f"Error converting HTML to text: {str(e)}")
            return html_content  # Return original HTML if conversion fails

    def _convert_table_to_text(self, table):
        """Convert HTML table to readable text format"""
        try:
            rows = table.find_all('tr')
            if not rows:
                return

            # Clear the table content
            table.clear()

            # Add table header
            table.append('\n--- Table ---\n')

            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' | '.join(cell.get_text().strip() for cell in cells)
                table.append(row_text + '\n')

            table.append('--- End Table ---\n')

        except Exception as e:
            logger.error(f"Error converting table to text: {str(e)}")

    def _get_page_attachments(self, page_id: str) -> str:
        """Get information about page attachments"""
        try:
            url = f"{self.api_base_url}/rest/api/content/{page_id}/child/attachment"

            response = self.session.get(url)

            if response.status_code != 200:
                return ""

            data = response.json()
            attachments = data.get('results', [])

            if not attachments:
                return ""

            attachment_info = []
            for attachment in attachments:
                info = f"- {attachment['title']} ({attachment.get('extensions', {}).get('mediaType', 'unknown')})"
                attachment_info.append(info)

            return '\n'.join(attachment_info)

        except Exception as e:
            logger.error(f"Error getting page attachments: {str(e)}")
            return ""

    def get_page_tree(self, space_key: str) -> Dict[str, Any]:
        """Get page hierarchy for a space"""
        try:
            # Get root pages (pages without parents in the space)
            url = f"{self.api_base_url}/rest/api/content"
            params = {
                'spaceKey': space_key,
                'type': 'page',
                'status': 'current',
                'expand': 'ancestors',
                'limit': 100
            }

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                return {}

            data = response.json()
            pages = data.get('results', [])

            # Build page tree
            tree = {}

            for page in pages:
                ancestors = page.get('ancestors', [])
                if not ancestors or all(ancestor.get('type') != 'page' for ancestor in ancestors):
                    # This is a root page
                    tree[page['id']] = {
                        'title': page['title'],
                        'id': page['id'],
                        'children': self._get_child_pages(page['id'])
                    }

            return tree

        except Exception as e:
            logger.error(f"Error getting page tree for space {space_key}: {str(e)}")
            return {}

    def _get_child_pages(self, page_id: str) -> List[Dict[str, Any]]:
        """Get child pages of a given page"""
        try:
            url = f"{self.api_base_url}/rest/api/content/{page_id}/child/page"

            response = self.session.get(url)

            if response.status_code != 200:
                return []

            data = response.json()
            children = data.get('results', [])

            child_list = []
            for child in children:
                child_info = {
                    'title': child['title'],
                    'id': child['id'],
                    'children': self._get_child_pages(child['id'])  # Recursive
                }
                child_list.append(child_info)

            return child_list

        except Exception as e:
            logger.error(f"Error getting child pages for {page_id}: {str(e)}")
            return []

    def search_confluence(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search Confluence content"""
        try:
            url = f"{self.api_base_url}/rest/api/content/search"
            params = {
                'cql': f'text ~ "{query}" and type = "page"',
                'limit': limit,
                'expand': 'space,version'
            }

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"Error searching Confluence: {response.status_code}")
                return []

            data = response.json()
            results = data.get('results', [])

            search_results = []
            for result in results:
                # Construct proper web URL
                webui_link = result['_links']['webui']
                if webui_link.startswith('/'):
                    # Add /wiki if not present
                    if webui_link.startswith('/wiki/'):
                        page_url = f"{self.base_url}{webui_link}"
                    else:
                        page_url = f"{self.base_url}/wiki{webui_link}"
                else:
                    page_url = webui_link

                search_result = {
                    'id': result['id'],
                    'name': result['title'],
                    'space_key': result['space']['key'],
                    'space_name': result['space']['name'],
                    'modified_time': result['version']['when'],
                    'source': 'confluence',
                    'url': page_url,
                    'type': 'page'
                }
                search_results.append(search_result)

            return search_results

        except Exception as e:
            logger.error(f"Error searching Confluence: {str(e)}")
            return []

    def get_recent_updates(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recently updated pages"""
        try:
            from datetime import datetime, timedelta

            # Calculate date threshold
            threshold_date = datetime.now() - timedelta(days=days)
            date_str = threshold_date.strftime('%Y-%m-%d')

            url = f"{self.api_base_url}/rest/api/content/search"
            params = {
                'cql': f'type = "page" and lastModified >= "{date_str}"',
                'limit': 50,
                'expand': 'space,version',
                'orderby': 'lastModified desc'
            }

            response = self.session.get(url, params=params)

            if response.status_code != 200:
                logger.error(f"Error getting recent updates: {response.status_code}")
                return []

            data = response.json()
            results = data.get('results', [])

            recent_docs = []
            for result in results:
                # Construct proper web URL
                webui_link = result['_links']['webui']
                if webui_link.startswith('/'):
                    # Add /wiki if not present
                    if webui_link.startswith('/wiki/'):
                        page_url = f"{self.base_url}{webui_link}"
                    else:
                        page_url = f"{self.base_url}/wiki{webui_link}"
                else:
                    page_url = webui_link

                doc_info = {
                    'id': result['id'],
                    'name': result['title'],
                    'space_key': result['space']['key'],
                    'space_name': result['space']['name'],
                    'modified_time': result['version']['when'],
                    'source': 'confluence',
                    'url': page_url,
                    'type': 'page'
                }
                recent_docs.append(doc_info)

            return recent_docs

        except Exception as e:
            logger.error(f"Error getting recent updates: {str(e)}")
            return []

    def validate_connection(self) -> Dict[str, Any]:
        """Validate Confluence connection and return status"""
        try:
            if not all([self.base_url, self.username, self.api_token]):
                return {
                    'status': 'error',
                    'message': 'Confluence credentials not configured'
                }

            # Test basic connectivity
            response = self.session.get(f"{self.api_base_url}/rest/api/space", timeout=10)

            if response.status_code == 200:
                spaces = response.json().get('results', [])
                return {
                    'status': 'connected',
                    'message': f'Successfully connected to Confluence',
                    'spaces_count': len(spaces)
                }
            elif response.status_code == 401:
                return {
                    'status': 'error',
                    'message': 'Authentication failed - check credentials'
                }
            elif response.status_code == 403:
                return {
                    'status': 'error',
                    'message': 'Access forbidden - check permissions'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Connection failed with status {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'Connection timeout - check Confluence URL'
            }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'message': 'Connection error - check network and Confluence URL'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }
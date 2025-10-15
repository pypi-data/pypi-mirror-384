import json
import os
import re
from pathlib import Path
from datetime import datetime

from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado

from .cache_service import get_cache_service
from .cache_handlers import ChatHistoriesHandler, AppValuesHandler, CacheInfoHandler
from .unified_database_schema_service import UnifiedDatabaseSchemaHandler, UnifiedDatabaseQueryHandler
from .snowflake_schema_service import SnowflakeSchemaHandler, SnowflakeQueryHandler
from .schema_search_service import SchemaSearchHandler


class HelloWorldHandler(APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "data": "Hello World from SignalPilot AI backend!",
            "message": "This is a simple hello world endpoint from the sage agent backend."
        }))


class ReadAllFilesHandler(APIHandler):
    """Handler for reading all notebook and data files in the workspace"""
    
    # Common data file extensions
    DATA_EXTENSIONS = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.pkl', '.pickle', 
                       '.feather', '.hdf5', '.h5', '.sql', '.db', '.sqlite', '.tsv', '.txt'}
    
    # Directories to exclude from search
    EXCLUDE_DIRS = {'.git', '.ipynb_checkpoints', 'node_modules', '__pycache__', 
                    '.venv', 'venv', 'env', '.pytest_cache', '.mypy_cache', 
                    'dist', 'build', '.tox', 'logs', '.vscode'}
    
    @tornado.web.authenticated
    def get(self):
        try:
            # Get the root directory where Jupyter Lab is running
            root_dir = Path(os.getcwd())
            
            # Find all notebook files
            notebooks = self._find_notebooks(root_dir)
            
            # Find all data files
            data_files = self._find_data_files(root_dir)
            
            # Get the 10 most recently edited notebooks
            recent_notebooks = self._get_recent_notebooks(notebooks, limit=10)
            
            # Analyze each notebook for data dependencies
            notebook_info = []
            all_data_dependencies = set()
            for notebook_path in recent_notebooks:
                info = self._analyze_notebook(notebook_path, data_files, root_dir)
                notebook_info.append(info)
                # Collect all data dependencies from recent notebooks
                all_data_dependencies.update(info['data_dependencies'])
            
            # Filter data files to only those referenced by recent notebooks
            referenced_data_files = []
            for data_file in data_files:
                rel_path = str(data_file.relative_to(root_dir))
                rel_path_forward = rel_path.replace('\\', '/')
                file_name = data_file.name
                
                # Check if this data file is referenced in any dependency
                if any(dep in [file_name, rel_path, rel_path_forward] or 
                       file_name in dep or rel_path in dep or rel_path_forward in dep 
                       for dep in all_data_dependencies):
                    referenced_data_files.append(data_file)
            
            # Generate the LLM-optimized context string with only referenced data
            welcome_context = self._generate_welcome_context(notebook_info, referenced_data_files, root_dir)
            
            self.finish(json.dumps({
                "welcome_context": welcome_context,
                "notebook_count": len(notebooks),
                "data_file_count": len(data_files),
                "recent_notebook_count": len(recent_notebooks),
                "referenced_data_count": len(referenced_data_files)
            }))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": str(e)
            }))
    
    def _find_notebooks(self, root_dir: Path) -> list:
        """Find all .ipynb files in the workspace"""
        notebooks = []
        for path in root_dir.rglob('*.ipynb'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in self.EXCLUDE_DIRS):
                continue
            notebooks.append(path)
        return notebooks
    
    def _find_data_files(self, root_dir: Path) -> list:
        """Find all data files in the workspace"""
        data_files = []
        for path in root_dir.rglob('*'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in self.EXCLUDE_DIRS):
                continue
            # Check if file has a data extension
            if path.is_file() and path.suffix.lower() in self.DATA_EXTENSIONS:
                data_files.append(path)
        return data_files
    
    def _get_recent_notebooks(self, notebooks: list, limit: int = 10) -> list:
        """Get the most recently modified notebooks"""
        # Sort by modification time (most recent first)
        notebooks_with_mtime = [(nb, nb.stat().st_mtime) for nb in notebooks]
        notebooks_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # Return only the paths, limited to the specified number
        return [nb for nb, _ in notebooks_with_mtime[:limit]]
    
    def _analyze_notebook(self, notebook_path: Path, data_files: list, root_dir: Path) -> dict:
        """Analyze a notebook to find data dependencies"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook_content = f.read()
            
            # Find data file references in the notebook
            referenced_data_files = self._find_data_references(notebook_content, data_files, root_dir)
            
            # Get relative path from root
            relative_path = notebook_path.relative_to(root_dir)
            
            # Get last modified time
            mtime = datetime.fromtimestamp(notebook_path.stat().st_mtime)
            
            return {
                'name': notebook_path.name,
                'path': str(relative_path),
                'last_modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                'data_dependencies': referenced_data_files
            }
        except Exception as e:
            # If we can't read the notebook, return basic info
            relative_path = notebook_path.relative_to(root_dir)
            return {
                'name': notebook_path.name,
                'path': str(relative_path),
                'last_modified': 'unknown',
                'data_dependencies': [],
                'error': str(e)
            }
    
    def _find_data_references(self, content: str, data_files: list, root_dir: Path) -> list:
        """Find references to data files in notebook content"""
        referenced_files = []
        
        # Create a set of data file names and paths for matching
        data_file_patterns = set()
        for data_file in data_files:
            # Add the filename
            data_file_patterns.add(data_file.name)
            # Add relative path
            try:
                rel_path = str(data_file.relative_to(root_dir))
                data_file_patterns.add(rel_path)
                # Also add with forward slashes (common in code)
                data_file_patterns.add(rel_path.replace('\\', '/'))
            except ValueError:
                pass
        
        # Search for data file references
        # Common patterns: pd.read_csv('file.csv'), open('file.csv'), 'path/to/file.csv'
        patterns = [
            r'["\']([^"\']+\.(?:csv|json|xlsx?|parquet|pkl|pickle|feather|hdf5|h5|sql|db|sqlite|tsv|txt))["\']',
            r'read_(?:csv|json|excel|parquet|pickle|feather|hdf|sql|table)\(["\']([^"\']+)["\']',
            r'to_(?:csv|json|excel|parquet|pickle|feather|hdf|sql)\(["\']([^"\']+)["\']',
        ]
        
        found_references = set()
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                file_ref = match.group(1)
                # Check if this reference matches any of our data files
                if file_ref in data_file_patterns or any(file_ref in str(df) for df in data_files):
                    found_references.add(file_ref)
        
        # Also check for database connection strings
        db_patterns = [
            r'(?:postgresql|mysql|sqlite|mongodb)://[^\s\'"]+',
            r'(?:DATABASE_URL|DB_URL|CONNECTION_STRING)\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in db_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                found_references.add(f"Database: {match.group(0)[:50]}...")
        
        return sorted(list(found_references))
    
    def _generate_welcome_context(self, notebook_info: list, data_files: list, root_dir: Path) -> str:
        """Generate an LLM-optimized, human-readable context string"""
        lines = []
        lines.append("# Workspace Overview\n")
        
        if not notebook_info:
            lines.append("No notebooks found in the workspace.\n")
        else:
            lines.append(f"## Recent Notebooks ({len(notebook_info)})\n")
            
            for i, info in enumerate(notebook_info, 1):
                lines.append(f"\n### {i}. {info['name']}")
                lines.append(f"   - Path: {info['path']}")
                lines.append(f"   - Last Modified: {info['last_modified']}")
                
                if info.get('error'):
                    lines.append(f"   - Note: Could not fully analyze ({info['error']})")
                
                if info['data_dependencies']:
                    lines.append(f"   - Data Dependencies:")
                    for dep in info['data_dependencies']:
                        lines.append(f"     • {dep}")
                else:
                    lines.append(f"   - Data Dependencies: None detected")
        
        # Add summary of data files referenced by recent notebooks
        if data_files:
            lines.append(f"\n## Data Files Referenced by Recent Notebooks ({len(data_files)} total)\n")
            
            # Group by extension
            by_extension = {}
            for df in data_files:
                ext = df.suffix.lower()
                if ext not in by_extension:
                    by_extension[ext] = []
                try:
                    rel_path = str(df.relative_to(root_dir))
                    by_extension[ext].append(rel_path)
                except ValueError:
                    by_extension[ext].append(str(df))
            
            for ext in sorted(by_extension.keys()):
                files = by_extension[ext]
                lines.append(f"\n### {ext} files ({len(files)})")
                # Show all referenced files (they should be limited already)
                for f in sorted(files):
                    lines.append(f"   - {f}")
        else:
            lines.append(f"\n## Data Files Referenced by Recent Notebooks\n")
            lines.append("No data file dependencies found in recent notebooks.\n")
        
        return '\n'.join(lines)


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    
    # Original hello world endpoint
    hello_route = url_path_join(base_url, "signalpilot-ai-internal", "hello-world")
    
    # Read all files endpoint
    read_all_files_route = url_path_join(base_url, "signalpilot-ai-internal", "read-all-files")
    
    # Cache service endpoints
    chat_histories_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "chat-histories")
    chat_history_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "chat-histories", "([^/]+)")
    
    app_values_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "app-values")
    app_value_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "app-values", "([^/]+)")
    
    cache_info_route = url_path_join(base_url, "signalpilot-ai-internal", "cache", "info")
    
    # Database service endpoints
    database_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "schema")
    database_query_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "query")
    database_schema_search_route = url_path_join(base_url, "signalpilot-ai-internal", "database", "schema-search")
    
    # MySQL service endpoints
    mysql_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "mysql", "schema")
    mysql_query_route = url_path_join(base_url, "signalpilot-ai-internal", "mysql", "query")
    
    # Snowflake service endpoints
    snowflake_schema_route = url_path_join(base_url, "signalpilot-ai-internal", "snowflake", "schema")
    snowflake_query_route = url_path_join(base_url, "signalpilot-ai-internal", "snowflake", "query")
    
    handlers = [
        # Original endpoint
        (hello_route, HelloWorldHandler),
        
        # Read all files endpoint
        (read_all_files_route, ReadAllFilesHandler),
        
        # Chat histories endpoints
        (chat_histories_route, ChatHistoriesHandler),
        (chat_history_route, ChatHistoriesHandler),
        
        # App values endpoints
        (app_values_route, AppValuesHandler),
        (app_value_route, AppValuesHandler),
        
        # Cache info endpoint
        (cache_info_route, CacheInfoHandler),
        
        # Database service endpoints (unified for PostgreSQL and MySQL)
        (database_schema_route, UnifiedDatabaseSchemaHandler),
        (database_query_route, UnifiedDatabaseQueryHandler),
        (database_schema_search_route, SchemaSearchHandler),
        
        # MySQL service endpoints (use unified handler)
        (mysql_schema_route, UnifiedDatabaseSchemaHandler),
        (mysql_query_route, UnifiedDatabaseQueryHandler),
        
        # Snowflake service endpoints
        (snowflake_schema_route, SnowflakeSchemaHandler),
        (snowflake_query_route, SnowflakeQueryHandler),
    ]
    
    web_app.add_handlers(host_pattern, handlers)
    
    # Initialize cache service on startup
    cache_service = get_cache_service()
    if cache_service.is_available():
        print(f"SignalPilot AI cache service initialized successfully")
        print(f"Cache directory: {cache_service.cache_dir}")
    else:
        print("WARNING: SignalPilot AI cache service failed to initialize!")
    
    print("SignalPilot AI backend handlers registered:")
    print(f"  - Hello World: {hello_route}")
    print(f"  - Read All Files: {read_all_files_route}")
    print(f"  - Chat Histories: {chat_histories_route}")
    print(f"  - Chat History (by ID): {chat_history_route}")
    print(f"  - App Values: {app_values_route}")
    print(f"  - App Value (by key): {app_value_route}")
    print(f"  - Cache Info: {cache_info_route}")
    print(f"  - Database Schema: {database_schema_route}")
    print(f"  - Database Query: {database_query_route}")
    print(f"  - Database Schema Search: {database_schema_search_route}")
    print(f"  - MySQL Schema: {mysql_schema_route}")
    print(f"  - MySQL Query: {mysql_query_route}")
    print(f"  - Snowflake Schema: {snowflake_schema_route}")
    print(f"  - Snowflake Query: {snowflake_query_route}")

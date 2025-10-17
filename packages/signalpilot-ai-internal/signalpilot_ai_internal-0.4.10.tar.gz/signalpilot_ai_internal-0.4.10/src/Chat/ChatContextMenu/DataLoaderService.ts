/**
 * Service responsible for loading data files and directories
 * Refactored from embedded Python code in ChatContextLoaders.ts
 */
import { Kernel } from '@jupyterlab/services';
import { MentionContext } from './ChatContextLoaders';
import { AppStateService } from '../../AppState';
import { IDatasetSchema } from '../../Services/PandasSchemaService';

export const DATA_DIRECTORY_FILE = './data/data_directory.json';

export interface FileInfo {
  extension: string;
  is_csv: boolean;
  is_tsv: boolean;
  is_json: boolean;
  is_parquet: boolean;
  is_pkl: boolean;
  is_text: boolean;
  is_data: boolean;
  is_binary: boolean;
  size_bytes: number;
}

export interface CsvInfo {
  type: 'csv';
  preview_type: 'header_and_sample';
  header?: string;
  sample_rows: string[];
  estimated_columns: number;
}

export interface JsonInfo {
  type: 'json';
  preview_type: 'structure_preview';
  structure: 'object' | 'array' | 'primitive';
  estimated_keys?: number;
  estimated_items?: number;
}

export interface FileEntry {
  id: string;
  name: string;
  path: string;
  absolute_path: string;
  relative_path: string;
  is_directory: boolean;
  file_info: FileInfo;
  content_preview?: string;
  is_truncated?: boolean;
  preview_length?: number;
  csv_info?: CsvInfo;
  json_info?: JsonInfo;
  schema?: IDatasetSchema;
  uploaded?: boolean;
}

export interface ScanResult {
  success: boolean;
  data_path: string;
  file_count: number;
  directory_count: number;
  total_items: number;
  files: FileEntry[];
  error?: string;
  error_type?: string;
}

/**
 * Service for loading data files using Python kernel execution
 */
export class DataLoaderService {
  private static cachedData: MentionContext[] | null = null;
  private static isRefreshing: boolean = false;
  private static refreshPromise: Promise<void> | null = null;

  /**
   * Load datasets from cache or JSON file directly (fast initial load)
   */
  public static async loadDatasets(
    kernel?: Kernel.IKernelConnection,
    currentPath: string = './data'
  ): Promise<MentionContext[]> {
    // First try to load from cache
    if (this.cachedData) {
      return this.cachedData;
    }

    // If no cache, load directly from JSON file
    return await this.loadFromJsonFile();
  }

  /**
   * Asynchronously refresh the data directory JSON file in the background
   */
  public static async refreshDataDirectory(
    kernel: Kernel.IKernelConnection,
    currentPath: string = './data'
  ): Promise<void> {
    // If already refreshing, return the existing promise
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    console.log(
      '[DataLoaderService] Starting async refresh of data directory...'
    );

    this.refreshPromise = this.performRefresh(kernel, currentPath);

    try {
      await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
      this.isRefreshing = false;
    }
  }

  /**
   * Load data directly from the data_directory.json file (synchronous)
   */
  private static async loadFromJsonFile(): Promise<MentionContext[]> {
    try {
      const data = await AppStateService.getState().contentManager?.get(
        DATA_DIRECTORY_FILE,
        { content: true }
      );
      console.log('[DataLoaderService] Loading data from cached JSON file');

      if (!data?.content) {
        console.warn('[DataLoaderService] No content in data_directory.json');
        return [];
      }

      const result: ScanResult = JSON.parse(data.content);

      if (!result.success) {
        console.warn(
          '[DataLoaderService] Data directory scan was not successful'
        );
        return [];
      }

      // Convert to MentionContext format and cache the result
      const mentionContexts = this.convertToMentionContexts(result.files);
      this.cachedData = mentionContexts;

      console.log(
        `[DataLoaderService] Loaded ${mentionContexts.length} items from JSON file`
      );
      return mentionContexts;
    } catch (error) {
      console.error('[DataLoaderService] Error loading from JSON file:', error);
      return [];
    }
  }

  /**
   * Perform the actual refresh by executing Python script and updating JSON file
   */
  private static async performRefresh(
    kernel: Kernel.IKernelConnection,
    currentPath: string
  ): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const currentExecutionPath =
        AppStateService.getState().currentNotebook?.sessionContext.path || '';

      // Calculate the correct relative path to the data directory from the notebook's location
      const resolvedDataPath = this.resolveDataPath(
        currentExecutionPath,
        currentPath
      );

      const pythonCode = this.generatePythonScript(resolvedDataPath);

      const future = kernel.requestExecute({
        code: pythonCode,
        silent: false
      });

      future.onIOPub = (msg: any) => {
        const msgType = msg.header.msg_type;

        if (msgType === 'error') {
          console.warn(
            '[DataLoaderService] Error during Python execution for data refresh'
          );
          resolve(); // Don't reject, just resolve so the app continues working
        }
      };

      future.done
        .then(async () => {
          try {
            // Reload from the updated JSON file
            const mentionContexts = await this.loadFromJsonFile();
            console.log(
              `[DataLoaderService] Async refresh completed with ${mentionContexts.length} items`
            );
            resolve();
          } catch (error) {
            console.error(
              '[DataLoaderService] Error after Python execution:',
              error
            );
            resolve(); // Don't reject, just resolve so the app continues working
          }
        })
        .catch((error: any) => {
          console.error('[DataLoaderService] Python execution failed:', error);
          resolve(); // Don't reject, just resolve so the app continues working
        });
    });
  }

  /**
   * Convert file entries to MentionContext format
   */
  private static convertToMentionContexts(
    files: FileEntry[]
  ): MentionContext[] {
    // Filter out the .data_directory.json file itself
    return files
      .filter((file: FileEntry) => !file.name.endsWith('data_directory.json'))
      .map((file: FileEntry) => {
        // Normalize the relative path and add ./data/ prefix for id
        const normalizedRelativePath = file.relative_path.replace(/\\/g, '/');

        // Path should also include the data prefix
        const path = `./data/${normalizedRelativePath}`;

        // Get parent path with ./data/ prefix
        const parentPath = this.getParentPathFromFile(file.relative_path);
        const normalizedParentPath = parentPath
          ? `./data/${parentPath}`
          : './data';

        if (file.is_directory) {
          return {
            type: 'directory' as const,
            id: file.id,
            name: file.name,
            path: path,
            isDirectory: true,
            parentPath: normalizedParentPath
          };
        } else {
          return {
            type: 'data' as const,
            id: file.id,
            name: file.name,
            description: this.getFileDescription(file),
            content: this.formatFileContent(file),
            path: path,
            isDirectory: false,
            parentPath: normalizedParentPath
          };
        }
      });
  }

  /**
   * Check if a refresh is currently in progress
   */
  public static isRefreshInProgress(): boolean {
    return this.isRefreshing;
  }

  /**
   * Clear cached data (useful for testing or forced refresh)
   */
  public static clearCache(): void {
    this.cachedData = null;
  }

  /**
   * Generate the Python script for file scanning
   */
  private static generatePythonScript(currentPath: string): string {
    return `
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

def is_binary_file(filepath: str, chunk_size: int = 512) -> bool:
    """Ultra-fast binary file detection with minimal I/O"""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(chunk_size)
            if not chunk:
                return False
            # Fast null byte check - if any null bytes, it's binary
            if b'\\x00' in chunk:
                return True
            # Quick printable ratio check using bytes directly
            printable = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
            return (printable / len(chunk)) < 0.7
    except (IOError, OSError):
        return True

def read_file_preview_optimized(filepath: str, max_chars: int = 5000, max_newlines: int = 5) -> Tuple[str, bool]:
    """
    Ultra-fast file preview reader using efficient buffered reading.
    Reads first 5000 characters OR first 5 newlines, whichever comes first.
    Returns (content, is_truncated)
    """
    try:
        file_size = os.path.getsize(filepath)
        
        # For very small files, read directly
        if file_size <= max_chars:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return content, False
        
        # For larger files, read in chunks and stop at limits
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_chars)
            
            # Count newlines in the content we read
            newline_count = content.count('\\n')
            
            # If we have 5 or fewer newlines, we're good
            if newline_count <= max_newlines:
                # Check if there's more content (for truncation flag)
                next_chunk = f.read(1)
                is_truncated = bool(next_chunk)
                return content, is_truncated
            
            # If we have more than 5 newlines, truncate to first 5
            lines = content.split('\\n', max_newlines + 1)
            if len(lines) > max_newlines:
                # We have more than max_newlines, so truncate
                truncated_content = '\\n'.join(lines[:max_newlines])
                return truncated_content, True
            else:
                # Exactly max_newlines, check if there's more content
                next_chunk = f.read(1)
                is_truncated = bool(next_chunk)
                return content, is_truncated
                
    except (UnicodeDecodeError, IOError, OSError):
        try:
            # Fallback for problematic files
            with open(filepath, 'rb') as f:
                raw_bytes = f.read(max_chars)
                content = raw_bytes.decode('utf-8', errors='replace')
                # Apply newline limit to fallback content too
                lines = content.split('\\n')
                if len(lines) > max_newlines:
                    content = '\\n'.join(lines[:max_newlines])
                    return content, True
                return content, len(raw_bytes) == max_chars
        except Exception:
            return f"<Error reading file: {filepath}>", False

def get_file_type_info(filepath: str, extension: str) -> Dict[str, Any]:
    """Get optimized metadata about file type"""
    file_info = {
        'extension': extension,
        'is_csv': extension == '.csv',
        'is_tsv': extension == '.tsv',
        'is_json': extension == '.json',
        'is_parquet': extension == '.parquet',
        'is_pkl': extension in ['.pkl', '.pickle'],
        'is_text': extension in ['.txt', '.md', '.py', '.js', '.ts', '.html', '.xml'],
        'is_data': extension in ['.csv', '.tsv', '.json', '.jsonl', '.parquet', '.pkl', '.pickle'],
        'is_binary': extension in ['.parquet', '.pkl', '.pickle']  # Will be set later based on actual binary detection
    }
    
    try:
        file_info['size_bytes'] = os.path.getsize(filepath)
    except (IOError, OSError):
        file_info['size_bytes'] = 0
        
    return file_info

def process_csv_preview(content: str, filepath: str) -> Dict[str, Any]:
    """Fast CSV preview processing"""
    # Split into lines efficiently, limit to what we need
    newline_pos = content.find('\\n')
    if newline_pos == -1:
        # Single line file
        header = content.strip()
        sample_rows = []
    else:
        # Multi-line file - get header and up to 5 sample rows
        lines = content.split('\\n', 6)  # Get at most 6 lines (header + 5 samples)
        header = lines[0] if lines[0] else None
        sample_rows = [line for line in lines[1:6] if line.strip()]
    
    result = {
        'type': 'csv',
        'preview_type': 'header_and_sample',
        'header': header,
        'sample_rows': sample_rows
    }
    
    if header:
        result['estimated_columns'] = header.count(',') + 1
    
    return result

def process_json_preview(content: str, filepath: str) -> Dict[str, Any]:
    """Fast JSON structure analysis without parsing"""
    result = {
        'type': 'json',
        'preview_type': 'structure_preview'
    }
    
    # Quick peek at first non-whitespace character
    content_stripped = content.lstrip()
    if not content_stripped:
        result['structure'] = 'primitive'
        return result
        
    first_char = content_stripped[0]
    if first_char == '{':
        result['structure'] = 'object'
        # Fast approximate key count (not 100% accurate but good enough)
        result['estimated_keys'] = content_stripped.count('":')
    elif first_char == '[':
        result['structure'] = 'array'
        # Fast approximate item count
        comma_count = content_stripped.count(',')
        result['estimated_items'] = comma_count + (1 if content_stripped != '[]' else 0)
    else:
        result['structure'] = 'primitive'
    
    return result

def scan_directory_optimized(data_path: str, original_root: str = None, max_depth: int = 10, current_depth: int = 0) -> List[Dict[str, Any]]:
    """Memory-optimized directory scanner with recursive traversal"""
    results = []
    data_dir = Path(data_path)
    
    # Set the original root on first call
    if original_root is None:
        original_root = data_path
    
    original_root_path = Path(original_root)
    
    if not data_dir.exists():
        return results
        
    if not data_dir.is_dir():
        return results
        
    # Prevent infinite recursion
    if current_depth >= max_depth:
        return results
    
    try:
        items = list(data_dir.iterdir())
        
        for item in items:
            try:
                if item.is_file() and not item.name.startswith('.'):
                    extension = item.suffix.lower()
                    file_info = get_file_type_info(str(item), extension)
                    
                    # Check if file is binary
                    is_binary = is_binary_file(str(item))
                    
                    if is_binary:
                        # For binary files, just provide basic info and file path
                        content = f"Binary file: {str(item)}"
                        is_truncated = False
                        # Mark as binary in file_info
                        file_info['is_binary'] = True
                    else:
                        # Read file preview with limits for text files
                        content, is_truncated = read_file_preview_optimized(str(item))
                        file_info['is_binary'] = False
                    
                    # Calculate relative path from the original root directory
                    try:
                        relative_path = str(item.relative_to(original_root_path))
                    except ValueError:
                        # Fallback if relative_to fails
                        relative_path = str(item.name)
                    
                    # Normalize the 'path' to remove any leading '../' or './'
                    normalized_path = str(item.resolve().relative_to(original_root_path)) if item.resolve().is_relative_to(original_root_path) else str(item.name)
                    file_entry = {
                        'id': str(item),
                        'name': item.stem,
                        'absolute_path': str(item.absolute()),
                        # Use normalized_path to avoid double dots in the path
                        'path': str(item),
                        'normalized_path': normalized_path,
                        'relative_path': relative_path,
                        'is_directory': False,
                        'file_info': file_info,
                        'content_preview': content,
                        'is_truncated': is_truncated,
                        'preview_length': len(content)
                    }
                    
                    if (file_info['is_csv'] or file_info['is_tsv']) and content:
                        file_entry['csv_info'] = process_csv_preview(content, str(item))
                    elif file_info['is_json'] and content:
                        file_entry['json_info'] = process_json_preview(content, str(item))
                    
                    results.append(file_entry)
                    
                elif item.is_dir() and not item.name.startswith('.'):
                    # Calculate relative path from the original root directory
                    try:
                        relative_path = str(item.relative_to(original_root_path))
                    except ValueError:
                        # Fallback if relative_to fails
                        relative_path = str(item.name)

                    # Normalize the 'path' to remove any leading '../' or './'
                    normalized_path = str(item.resolve().relative_to(original_root_path)) if item.resolve().is_relative_to(original_root_path) else str(item.name)
                    dir_entry = {
                        'id': str(item),
                        'name': item.name,
                        'absolute_path': str(item.absolute()),
                        'path': str(item),
                        'normalized_path': normalized_path,
                        'relative_path': relative_path,
                        'is_directory': True,
                        'file_info': {'is_directory': True}
                    }
                    results.append(dir_entry)
                    
                    # Recursively scan subdirectory
                    try:
                        subdirectory_results = scan_directory_optimized(
                            str(item), 
                            original_root, 
                            max_depth, 
                            current_depth + 1
                        )
                        results.extend(subdirectory_results)
                    except Exception as e:
                        continue
                    
            except (IOError, OSError, PermissionError) as e:
                continue
                
    except (IOError, OSError, PermissionError) as e:
        pass
    
    # Sort only at the root level to maintain hierarchy
    if current_depth == 0:
        results.sort(key=lambda x: (not x['is_directory'], x['relative_path'].lower()))
    
    return results

# Execute the file scanning
try:
    data_path = "${currentPath}"
    
    file_data = scan_directory_optimized(data_path)
    
    result = {
        'success': True,
        'data_path': data_path,
        'file_count': len([f for f in file_data if not f['is_directory']]),
        'directory_count': len([f for f in file_data if f['is_directory']]),
        'total_items': len(file_data),
        'files': file_data
    }
    
    with open("${currentPath}/data_directory.json", "w") as f:
        json.dump(result, f, separators=(',', ':'))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e),
        'error_type': type(e).__name__,
        'data_path': "${currentPath}"
    }
    print(json.dumps(error_result, separators=(',', ':')))
    `;
  }

  /**
   * Format file content for display
   */
  private static formatFileContent(file: FileEntry): string {
    let contentWithPath = `File Path: ${file.path}\n\n`;

    // Handle binary files
    if (file.file_info.is_binary) {
      contentWithPath += `Binary File (${file.file_info.extension})\n\n`;
      contentWithPath += 'Content: Binary file - content not displayed';
      return contentWithPath;
    }

    if (file.csv_info) {
      contentWithPath += `CSV File (${file.csv_info.estimated_columns} columns)\n`;
      if (file.csv_info.header) {
        contentWithPath += `Header: ${file.csv_info.header}\n`;
      }
      if (file.csv_info.sample_rows?.length > 0) {
        contentWithPath += `Sample Rows:\n${file.csv_info.sample_rows.join('\n')}\n`;
      }
    } else if (file.json_info) {
      contentWithPath += `JSON File (${file.json_info.structure})\n`;
      if (file.json_info.estimated_keys) {
        contentWithPath += `Estimated Keys: ${file.json_info.estimated_keys}\n`;
      }
      if (file.json_info.estimated_items) {
        contentWithPath += `Estimated Items: ${file.json_info.estimated_items}\n`;
      }
    }

    if (file.content_preview) {
      contentWithPath += `\nContent Preview:\n${file.content_preview}`;

      if (file.is_truncated) {
        contentWithPath +=
          '\n\n[Content truncated - showing first 5000 chars or 5 lines]';
      }
    }

    return contentWithPath;
  }

  /**
   * Public wrapper to get formatted file content for UI rendering
   */
  public static getFormattedFileContent(file: FileEntry): string {
    return DataLoaderService.formatFileContent(file);
  }

  /**
   * Generate appropriate file description based on file info
   */
  private static getFileDescription(file: FileEntry): string {
    // Handle binary files first
    if (file.file_info.is_binary) {
      return `Binary file (${file.file_info.extension})`;
    }

    if (file.csv_info) {
      return `CSV file (${file.csv_info.estimated_columns} cols)`;
    } else if (file.json_info) {
      return `JSON file (${file.json_info.structure})`;
    } else if (file.file_info.is_data) {
      return `Data file (${file.file_info.extension})`;
    } else {
      return `Text file (${file.file_info.extension})`;
    }
  }

  /**
   * Get the parent path from a given path
   */
  private static getParentPath(path: string): string {
    const parts = path.split('/');
    parts.pop(); // Remove the last part
    return parts.join('/') || './data';
  }

  /**
   * Get the parent path from a file's relative path
   * Returns undefined if the file is in the root data directory
   */
  private static getParentPathFromFile(
    relativePath: string
  ): string | undefined {
    // Normalize path separators to forward slashes
    const normalizedPath = relativePath.replace(/\\/g, '/');

    // Split the path into parts
    const parts = normalizedPath.split('/');

    // If there's only one part (file in root), no parent path
    if (parts.length <= 1) {
      return undefined;
    }

    // Remove the filename (last part) to get parent directory
    parts.pop();

    // Join the remaining parts to form the parent path
    return parts.join('/');
  }

  /**
   * Resolve the correct path to the data directory from the notebook's location
   */
  private static resolveDataPath(
    notebookPath: string,
    requestedPath: string
  ): string {
    // If no notebook path or requested path is absolute, return as-is
    if (
      !notebookPath ||
      requestedPath.startsWith('/') ||
      requestedPath.includes(':\\')
    ) {
      return requestedPath;
    }

    // If the requested path is not the default './data', return as-is
    if (requestedPath !== './data') {
      return requestedPath;
    }

    // Calculate the directory depth of the notebook relative to the workspace root
    const notebookDir = notebookPath.split('/').slice(0, -1).join('/'); // Remove filename, keep directory
    const depth = notebookDir ? notebookDir.split('/').length : 0;

    // If the notebook is in the root, use './data'
    if (depth === 0) {
      return './data';
    }

    // Build the relative path back to root, then to data
    const backToRoot = '../'.repeat(depth);
    return `${backToRoot}data`;
  }
}

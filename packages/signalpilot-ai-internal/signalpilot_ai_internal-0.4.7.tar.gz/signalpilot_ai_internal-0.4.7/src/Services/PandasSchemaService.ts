import { AppStateService } from '../AppState';
import { FileEntry } from '../Chat/ChatContextMenu/DataLoaderService';
import Bluebird from 'bluebird';

export interface IColumnSchema {
  name: string;
  dataType: string;
  description: string;
}

export type IDatasetSchema = IDatasetSchemaSuccess | IDatasetSchemaError;

interface IDatasetSchemaSuccess {
  fileId: string;
  fileName: string;
  filePath: string;
  fileType: 'csv' | 'tsv' | 'parquet' | 'pkl';
  extractedAt: string;
  summary: string;
  totalRows?: number;
  totalColumns?: number;
  columns: IColumnSchema[];
  sampleData?: any[][];
  success: true;
}

interface IDatasetSchemaError {
  success: false;
  error: string;
}

export interface ISchemaExtractionResult {
  fileId: string;
  absolutePath: string;
  success: boolean;
  schema?: IDatasetSchema;
  error?: string;
}

/**
 * Service for extracting schema information from files using pandas
 */
export class PandasSchemaService {
  /**
   * Extract schema from a file entry using pandas
   */
  public static async extractSchema(
    file: FileEntry
  ): Promise<ISchemaExtractionResult> {
    try {
      console.log('[PandasSchemaService] Extracting schema for:', file.name);

      // Determine file type
      const fileType = this.getFileType(file);
      if (!fileType) {
        return {
          absolutePath: file.absolute_path,
          fileId: file.id,
          success: false,
          error: 'Unsupported file type'
        };
      }

      // Get current kernel
      const currentNotebook = AppStateService.getState().currentNotebook;
      const kernel = currentNotebook?.sessionContext?.session?.kernel;

      if (!kernel) {
        return {
          absolutePath: file.absolute_path,
          fileId: file.id,
          success: false,
          error: 'No active kernel available'
        };
      }

      // Generate pandas script based on file type
      const pythonCode = this.generatePandasScript(file, fileType);

      // Execute the pandas script
      const future = kernel.requestExecute({
        code: pythonCode,
        store_history: false,
        silent: true
      });

      return new Promise(resolve => {
        let result = '';
        let error = '';

        future.onIOPub = msg => {
          if (msg.header.msg_type === 'execute_result') {
            const data = (msg.content as any).data;
            if (data && data['text/plain']) {
              result = data['text/plain'];
            }
          } else if (msg.header.msg_type === 'stream') {
            const content = msg.content as any;
            if (content.name === 'stdout') {
              result += content.text;
            } else if (content.name === 'stderr') {
              error += content.text;
            }
          } else if (msg.header.msg_type === 'error') {
            const content = msg.content as any;
            error += content.evalue || 'Unknown error';
          }
        };

        void future.done.then(() => {
          if (error) {
            resolve({
              absolutePath: file.absolute_path,
              fileId: file.id,
              success: false,
              error: `Pandas extraction failed: ${error}`
            });
            return;
          }

          try {
            // Parse the result
            const schema = this.parseSchemaResult(result, file, fileType);
            resolve({
              absolutePath: file.absolute_path,
              fileId: file.id,
              success: true,
              schema
            });
          } catch (parseError) {
            console.error('[PandasSchemaService] Parse error:', parseError);
            resolve({
              absolutePath: file.absolute_path,
              fileId: file.id,
              success: false,
              error: `Failed to parse schema result: ${parseError}`
            });
          }
        });
      });
    } catch (error) {
      console.error('[PandasSchemaService] Error extracting schema:', error);
      return {
        absolutePath: file.absolute_path,
        fileId: file.id,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get file type from file entry
   */
  private static getFileType(
    file: FileEntry
  ): 'csv' | 'tsv' | 'parquet' | 'pkl' | null {
    const extension = file.path.toLowerCase().split('.').pop();
    switch (extension) {
      case 'csv':
        return 'csv';
      case 'tsv':
        return 'tsv';
      case 'parquet':
        return 'parquet';
      case 'pkl':
      case 'pickle':
        return 'pkl';
      default:
        return null;
    }
  }

  /**
   * Generate pandas script for schema extraction
   */
  private static generatePandasScript(
    file: FileEntry,
    fileType: string
  ): string {
    // Convert relative paths to absolute paths
    let filePath = file.path;

    // If it's a relative path, make it absolute from the workspace root
    if (filePath.startsWith('./')) {
      filePath = filePath.slice(2); // Remove './'
    }

    // Add robust path resolution to handle various directory structures
    const fullPath = `import os
import sys

# First, try the path as given
file_path = '${filePath.replace(/\\/g, '\\\\')}'

if not os.path.isfile(file_path):
    # Get current working directory
    cwd = os.getcwd()
    
    # Try absolute path
    abs_path = os.path.abspath(file_path)
    if os.path.isfile(abs_path):
        file_path = abs_path
    else:
        # If path starts with 'data/', try without the data prefix in case we're already in data dir
        if file_path.startswith('data/'):
            no_data_prefix = file_path[5:]  # Remove 'data/' prefix
            if os.path.isfile(no_data_prefix):
                file_path = no_data_prefix
            elif os.path.isfile(os.path.join(cwd, no_data_prefix)):
                file_path = os.path.join(cwd, no_data_prefix)
            else:
                # Try joining with cwd
                workspace_path = os.path.join(cwd, file_path)
                if os.path.isfile(workspace_path):
                    file_path = workspace_path
                else:
                    # Try going up one directory and then joining (in case we're in a subdirectory)
                    parent_path = os.path.join(os.path.dirname(cwd), file_path)
                    if os.path.isfile(parent_path):
                        file_path = parent_path
                    else:
                        raise FileNotFoundError(f"File not found. Tried: {file_path}, {abs_path}, {workspace_path}, {parent_path}")
        else:
            # Try joining with cwd
            workspace_path = os.path.join(cwd, file_path)
            if os.path.isfile(workspace_path):
                file_path = workspace_path
            else:
                # Try going up one directory and then joining
                parent_path = os.path.join(os.path.dirname(cwd), file_path)
                if os.path.isfile(parent_path):
                    file_path = parent_path
                else:
                    raise FileNotFoundError(f"File not found. Tried: {file_path}, {abs_path}, {workspace_path}, {parent_path}")
`;

    const baseScript = `${fullPath}
import pandas as pd
import json
import numpy as np

def get_data_type(dtype_str):
    """Map pandas dtypes to readable types"""
    if dtype_str.startswith('int'):
        return 'integer'
    elif dtype_str.startswith('float'):
        return 'float'
    elif dtype_str == 'bool':
        return 'boolean'
    elif dtype_str.startswith('datetime'):
        return 'datetime'
    elif dtype_str == 'object':
        return 'string'
    else:
        return 'string'

def analyze_dataframe(df, file_type):
    """Analyze DataFrame and return schema information"""
    # Get basic info
    total_rows_sample = len(df)
    total_columns = len(df.columns)
    
    # Get column information
    columns = []
    sample_data = []
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        data_type = get_data_type(dtype)
        
        # For object columns, try to infer if it's a date
        if dtype == 'object' and not df[col].dropna().empty:
            sample_val = df[col].dropna().iloc[0]
            try:
                pd.to_datetime(sample_val)
                data_type = 'date'
            except:
                pass
        
        columns.append({
            'name': str(col),
            'dataType': data_type,
            'description': f'Column {col} of type {data_type}'
        })
    
    # Get sample data (first 3 rows)
    for _, row in df.head(3).iterrows():
        sample_data.append(row.fillna('').astype(str).tolist())
    
    return {
        'success': True,
        'totalRows': total_rows_sample,
        'totalColumns': total_columns,
        'columns': columns,
        'sampleData': sample_data,
        'summary': f'{file_type.upper()} file with {total_columns} columns'
    }

try:`;

    if (fileType === 'csv' || fileType === 'tsv') {
      const separator = fileType === 'csv' ? ',' : '\\t';
      return (
        baseScript +
        `
    # Read only first 3 rows for schema detection
    df = pd.read_csv(file_path, sep='${separator}', nrows=3)
    result = analyze_dataframe(df, '${fileType}')
    print(json.dumps(result))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e)
    }
    print(json.dumps(error_result))
`
      );
    } else if (fileType === 'parquet') {
      return (
        baseScript +
        `
    # Read only first 3 rows for schema detection
    df = pd.read_parquet(file_path)
    df = df.head(3)  # Limit to first 3 rows
    result = analyze_dataframe(df, '${fileType}')
    print(json.dumps(result))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e)
    }
    print(json.dumps(error_result))
`
      );
    } else if (fileType === 'pkl') {
      return (
        baseScript +
        `
    # Read pickle file
    data = pd.read_pickle(file_path)
    
    # Check if it's a DataFrame
    if isinstance(data, pd.DataFrame):
        df = data.head(3)  # Limit to first 3 rows
        result = analyze_dataframe(df, '${fileType}')
    else:
        # If it's not a DataFrame, try to analyze the object
        result = {
            'success': True,
            'summary': f'Pickle file containing {type(data).__name__}',
            'columns': [],
            'totalRows': 1 if not hasattr(data, '__len__') else len(data) if hasattr(data, '__len__') else 1,
            'totalColumns': 0
        }
    
    print(json.dumps(result))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e)
    }
    print(json.dumps(error_result))
`
      );
    }

    return `
print(json.dumps({
    'success': False,
    'error': 'Unsupported file type: ${fileType}'
}))
`;
  }

  /**
   * Parse the schema result from pandas execution
   */
  private static parseSchemaResult(
    result: string,
    file: FileEntry,
    fileType: string
  ): IDatasetSchema {
    try {
      // Clean the result string and parse JSON
      const cleanResult = result.trim().replace(/^'|'$/g, '');
      const parsedResult = JSON.parse(cleanResult);

      if (!parsedResult.success) {
        return {
          success: false,
          error: parsedResult.error || 'Schema extraction failed'
        };
      }

      const schema: IDatasetSchema = {
        success: true,
        fileId: file.id,
        fileName: file.name,
        filePath: file.path,
        fileType: fileType as any,
        extractedAt: new Date().toISOString(),
        summary: parsedResult.summary || `${fileType.toUpperCase()} file`,
        totalRows: parsedResult.totalRows,
        totalColumns: parsedResult.totalColumns,
        columns: parsedResult.columns || [],
        sampleData: parsedResult.sampleData
      };

      return schema;
    } catch (error) {
      console.error('[PandasSchemaService] Parse error:', error);

      // Fallback schema
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Extract schemas for multiple files with concurrency control
   */
  public static async extractMultipleSchemas(
    files: FileEntry[],
    maxConcurrency: number = 10,
    onFinish?: (result: ISchemaExtractionResult) => void
  ): Promise<ISchemaExtractionResult[]> {
    const results = await Bluebird.map(
      files,
      async file => {
        const result = await this.extractSchema(file);

        if (onFinish) {
          onFinish(result);
        }

        return result;
      },
      {
        concurrency: maxConcurrency
      }
    );

    return results;
  }
}

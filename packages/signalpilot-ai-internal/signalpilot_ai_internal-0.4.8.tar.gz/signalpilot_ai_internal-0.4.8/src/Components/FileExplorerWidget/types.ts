import { FileEntry } from '../../Chat/ChatContextMenu/DataLoaderService';
import { IDatasetSchema } from '../../Services/PandasSchemaService';

export interface IFileExplorerState {
  isVisible: boolean;
  files: FileEntry[];
  isLoading: boolean;
  error?: string;
  totalFileCount: number;
  isUploading: boolean;
  uploadProgress?: {
    completed: number;
    total: number;
  };
}

export type FileType = 'csv' | 'tsv' | 'json' | 'parquet' | 'pkl';

export interface ISupportedFileEntry extends FileEntry {
  displayPath: string;
  fileType: FileType;
  schema?: IDatasetSchema;
  hasSchema: boolean;
  isExpanded?: boolean;
}

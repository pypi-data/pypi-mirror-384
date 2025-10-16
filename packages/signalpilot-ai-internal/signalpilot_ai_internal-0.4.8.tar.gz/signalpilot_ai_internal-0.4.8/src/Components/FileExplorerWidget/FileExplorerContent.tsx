import * as React from 'react';
import { FileType, IFileExplorerState, ISupportedFileEntry } from './types';
import { ARROW_DOWN_ICON, FOLDER_ICON } from './icons';
import { DataLoaderService } from '../../Chat/ChatContextMenu/DataLoaderService';

interface IFileUploadBoxProps {
  onFileUpload: (files: FileList) => void;
  disabled?: boolean;
}

const FileUploadBox: React.FC<IFileUploadBoxProps> = ({
  onFileUpload,
  disabled
}) => {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    if (disabled) {
      return;
    }

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileUpload(files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileUpload(files);
    }
    // Reset input value so same file can be selected again
    e.target.value = '';
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div
      className={`file-upload-box ${isDragOver ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".csv,.tsv,.parquet,.pkl,.pickle"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        disabled={disabled}
      />
      <div className="upload-text">
        <span className="upload-primary">
          Drop files here or click to upload
        </span>
        <span className="upload-secondary">
          Supports CSV, TSV, Parquet, Pickle files
        </span>
      </div>
    </div>
  );
};

interface IFileExplorerContentProps {
  state: IFileExplorerState;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onExtractSingleSchema: (file: ISupportedFileEntry) => void;
  onFileUpload: (files: FileList) => void;
  onAddToContext: (file: ISupportedFileEntry) => void;
}

export const FileExplorerContent: React.FC<IFileExplorerContentProps> = ({
  state,
  onOpenInBrowser,
  onExtractSingleSchema,
  onFileUpload,
  onAddToContext
}) => {
  if (!state.isVisible) {
    return null;
  }

  // Filter and convert files to supported format
  const supportedFiles: ISupportedFileEntry[] = state.files
    .filter(file => {
      // Only show non-directory, non-binary files
      if (file.is_directory || file.path.endsWith('data_directory.json')) {
        return false;
      }

      // Check for supported file types
      const filePath = file.path.toLowerCase();
      return (
        filePath.endsWith('.csv') ||
        filePath.endsWith('.tsv') ||
        filePath.endsWith('.parquet') ||
        filePath.endsWith('.pkl') ||
        filePath.endsWith('.pickle')
      );
    })
    .map(file => ({
      ...file,
      displayPath: file.relative_path,
      fileType: (file.path.split('.').pop() || '').toLowerCase() as FileType,
      schema: file.schema,
      hasSchema: file.schema ? true : false
    })); // Show all files
  return (
    <div className="sage-ai-file-explorer-content">
      <div className="file-explorer-header">
        <h3>File Scanner</h3>
      </div>

      {state.isLoading && (
        <div className="loading-indicator">
          <div className="loading-spinner"></div>
          <span>Loading files...</span>
        </div>
      )}

      {state.error && (
        <div className="error-message">
          <div className="error-icon">⚠️</div>
          <span>{state.error}</span>
        </div>
      )}

      {!state.isLoading && !state.error && (
        <>
          {/* File Upload Component */}
          <div className="file-upload-container">
            <div className="file-upload-info">
              Upload your files, we will scan for the schema and you can focus
              on the important part - the analysis.
              <br />
              All files are stored in ./data directory.
            </div>
            <FileUploadBox
              onFileUpload={onFileUpload}
              disabled={state.isUploading}
            />
          </div>

          {state.isUploading && (
            <div className="upload-progress">
              <div className="loading-spinner">📤</div>
              <span>
                Uploading files...
                {state.uploadProgress &&
                  ` (${state.uploadProgress.completed}/${state.uploadProgress.total})`}
              </span>
            </div>
          )}

          <div className="file-list">
            {supportedFiles.length === 0 ? (
              <div className="empty-message">
                <div className="empty-icon">
                  <FOLDER_ICON.react />
                </div>
                <span>No supported data files found</span>
                <small>Supported formats: CSV, TSV, Parquet, Pickle</small>
              </div>
            ) : (
              supportedFiles.map(file => (
                <FileItem
                  key={file.id}
                  file={file}
                  onOpenInBrowser={onOpenInBrowser}
                  onExtractSingleSchema={onExtractSingleSchema}
                  onAddToContext={onAddToContext}
                />
              ))
            )}
          </div>

          <div className="file-count-info">
            <span className="count-text">
              Showing {supportedFiles.length} files
            </span>
          </div>
        </>
      )}
    </div>
  );
};

interface IFileActionsMenuProps {
  file: ISupportedFileEntry;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onExtractSingleSchema: (file: ISupportedFileEntry) => void;
}

const FileActionsMenu: React.FC<IFileActionsMenuProps> = ({
  file,
  onOpenInBrowser,
  onExtractSingleSchema
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleAction = (action: () => void) => {
    action();
    setIsOpen(false);
  };

  return (
    <div className="file-actions-menu" ref={menuRef}>
      <button
        className="three-dot-button"
        onClick={e => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        title="More actions"
      >
        ⋯
      </button>
      {isOpen && (
        <div className="actions-dialog">
          <button
            className="action-menu-item"
            onClick={e => {
              e.stopPropagation();
              handleAction(() => onOpenInBrowser(file));
            }}
          >
            Go to file
          </button>
          <button
            className="action-menu-item"
            onClick={e => {
              e.stopPropagation();
              handleAction(() => onExtractSingleSchema(file));
            }}
          >
            Reload scan
          </button>
        </div>
      )}
    </div>
  );
};

interface IFileItemProps {
  file: ISupportedFileEntry;
  onOpenInBrowser: (file: ISupportedFileEntry) => void;
  onExtractSingleSchema: (file: ISupportedFileEntry) => void;
  onAddToContext: (file: ISupportedFileEntry) => void;
}

const FileItem: React.FC<IFileItemProps> = ({
  file,
  onOpenInBrowser,
  onExtractSingleSchema,
  onAddToContext
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [showPreview, setShowPreview] = React.useState(false);
  const formattedContent = React.useMemo(
    () => DataLoaderService.getFormattedFileContent(file),
    [file]
  );
  return (
    <div key={file.id}>
      <div className="file-item">
        <div className="file-header" onClick={() => setIsExpanded(!isExpanded)}>
          <ARROW_DOWN_ICON.react
            transform={isExpanded ? 'rotate(0deg)' : 'rotate(270deg)'}
            opacity={0.5}
            visibility={file.schema?.success ? 'visible' : 'hidden'}
          />
          <div className="file-info">
            <div className="file-name">
              <span className="file-name-text">{file.name} </span>
              {file.schema && file.schema.success === false && (
                <span title={file.schema.error} className="file-error-message">
                  {file.schema.error}
                </span>
              )}
              <div className="file-actions">
                <button
                  className="add-to-context-button"
                  onClick={e => {
                    e.stopPropagation();
                    onAddToContext(file);
                  }}
                >
                  + Add to context
                </button>
                {file.schema &&
                  file.schema.success &&
                  file.schema.totalColumns && (
                    <span className="column-count">
                      {file.schema.totalColumns} cols
                    </span>
                  )}
                {!file.schema && <div className="loading-spinner"></div>}
                <FileActionsMenu
                  file={file}
                  onOpenInBrowser={onOpenInBrowser}
                  onExtractSingleSchema={onExtractSingleSchema}
                />
              </div>
            </div>
            <div className="file-path">{file.displayPath}</div>
          </div>
        </div>
      </div>
      {isExpanded && (file.fileType === 'csv' || file.fileType === 'tsv') && (
        <label
          className="toggle-preview-checkbox"
          onClick={e => e.stopPropagation()}
        >
          <input
            type="checkbox"
            checked={showPreview}
            onChange={e => setShowPreview(e.target.checked)}
          />
          <span style={{ marginLeft: 6 }}>See what AI sees</span>
        </label>
      )}
      {showPreview &&
        isExpanded &&
        (file.fileType === 'csv' || file.fileType === 'tsv') && (
          <pre className="file-content-preview">
            <code>{formattedContent}</code>
          </pre>
        )}
      {isExpanded &&
        file.schema &&
        file.schema.success &&
        file.schema.columns && (
          <div className="file-columns">
            {file.schema.columns.map((column: any) => (
              <div key={column.name} className="column-item">
                <span className="column-name">{column.name}</span>
                <span className="column-type">
                  {column.dataType.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        )}
    </div>
  );
};

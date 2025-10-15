import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { ISignal, Signal } from '@lumino/signaling';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { AppStateService } from '../../AppState';
import {
  DATA_DIRECTORY_FILE,
  DataLoaderService,
  FileEntry,
  ScanResult
} from '../../Chat/ChatContextMenu/DataLoaderService';
import { IFileExplorerState, ISupportedFileEntry } from './types';
import { FileExplorerContent } from './FileExplorerContent';
import { folderIcon } from '@jupyterlab/ui-components';
import { PandasSchemaService } from '../../Services/PandasSchemaService';
import { Message } from '@lumino/messaging';

/**
 * Widget for exploring data files in the left sidebar
 */
export class FileExplorerWidget extends ReactWidget {
  private _state: IFileExplorerState;
  private _stateChanged = new Signal<this, IFileExplorerState>(this);
  private _app: JupyterFrontEnd | null = null;
  private _pollingTimer: NodeJS.Timeout | null = null;
  private _isPolling = false;

  constructor() {
    super();
    this._state = {
      isVisible: true,
      files: [],
      isLoading: true,
      totalFileCount: 0,
      isUploading: false
    };

    this.addClass('sage-ai-file-explorer-widget');
    this.id = 'sage-ai-file-explorer';
    this.title.closable = true;
    this.title.icon = folderIcon;

    // Set initial visibility state
    if (!this._state.isVisible) {
      this.addClass('hidden');
    }

    // Initialize schema storage and load files
    void this.initialize();
  }

  /**
   * Dispose of the widget and clean up resources
   */
  dispose(): void {
    super.dispose();
  }

  /**
   * Set the JupyterLab app instance for file browser operations
   */
  public setApp(app: JupyterFrontEnd): void {
    this._app = app;
  }

  /**
   * When the widget becomes visible after being hidden, refresh
   */
  protected onAfterShow(msg: Message): void {
    super.onAfterShow(msg);
    try {
      const currentNotebook = AppStateService.getState().currentNotebook;
      const kernel = currentNotebook?.sessionContext?.session?.kernel;
      if (kernel) {
        void DataLoaderService.refreshDataDirectory(kernel);
      }
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Failed to refresh data directory on show:',
        error
      );
    }
  }

  /**
   * Get the signal that fires when state changes
   */
  public get stateChanged(): ISignal<this, IFileExplorerState> {
    return this._stateChanged;
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <FileExplorerContent
        state={this._state}
        onOpenInBrowser={this.handleOpenInBrowser.bind(this)}
        onExtractSingleSchema={this.handleExtractSingleSchema.bind(this)}
        onFileUpload={this.handleFileUpload.bind(this)}
        onAddToContext={this.handleAddToContext.bind(this)}
      />
    );
  }

  /**
   * Initialize the widget
   */
  private async initialize(): Promise<void> {
    // Load files
    await this.loadFiles();
  }

  private async loadFilesFromCache(): Promise<ScanResult | null> {
    try {
      const data = await AppStateService.getState().contentManager?.get(
        DATA_DIRECTORY_FILE,
        { content: true }
      );

      return data?.content ? (JSON.parse(data.content) as ScanResult) : null;
    } catch (error) {
      return null;
    }
  }

  /**
   * Load files from DataLoaderService
   */
  private async loadFiles(): Promise<void> {
    try {
      // Try to get the current kernel from AppState
      const currentNotebook = AppStateService.getState().currentNotebook;
      const kernel = currentNotebook?.sessionContext?.session?.kernel;

      const data = await this.loadFilesFromCache();
      if (data) {
        const { files } = data;

        this.updateState({
          files,
          isLoading: false,
          totalFileCount: files.length
        });
      }

      // Trigger background refresh and start polling for files if we have a kernel
      if (kernel) {
        void DataLoaderService.refreshDataDirectory(kernel);
      }

      void this.startPollingForFiles();
    } catch (error) {
      console.error('[FileExplorerWidget] Failed to load files:', error);
      this.updateState({
        isLoading: false,
        error: 'Failed to load files. Please try refreshing.'
      });
    }
  }

  /**
   * Handle extract schema for a single file
   */
  private async handleExtractSingleSchema(
    file: ISupportedFileEntry
  ): Promise<void> {
    try {
      console.log('[FileExplorerWidget] Extracting schema for:', file.name);

      const result = await PandasSchemaService.extractSchema(file);

      if (result.success && result.schema) {
        // Update the file with schema info in the current state
        const updatedFiles = this._state.files.map(f => {
          if (f.absolute_path === file.absolute_path) {
            return {
              ...f,
              schema: result.schema,
              hasSchema: true
            };
          }
          return f;
        });

        this.updateState({ files: updatedFiles });

        console.log(
          '[FileExplorerWidget] Schema extracted successfully for:',
          file.name
        );
      } else {
        console.error(
          '[FileExplorerWidget] Schema extraction failed:',
          result.error
        );
      }
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Error extracting single schema:',
        error
      );
    }
  }

  private async handleAddToContext(file: ISupportedFileEntry): Promise<void> {
    console.log('[FileExplorerWidget] Add to context:', file);
    const chatMessages =
      AppStateService.getState().chatContainer?.chatWidget.messageComponent;
    if (!chatMessages) {
      console.error('[FileExplorerWidget] Chat messages not available');
      return;
    }

    const context = await DataLoaderService.loadDatasets();

    const fileContext = context.find(c => c.path?.endsWith(file.path));
    if (!fileContext) {
      console.error('[FileExplorerWidget] File context not found');
      return;
    }

    chatMessages.addMentionContext(fileContext);
  }

  /**
   * Handle opening file in browser
   */
  private async handleOpenInBrowser(file: ISupportedFileEntry): Promise<void> {
    console.log('[FileExplorerWidget] Open in browser:', file);

    if (!this._app) {
      console.error('[FileExplorerWidget] JupyterLab app not available');
      return;
    }

    try {
      // Get the directory path (remove filename)
      const filePath = file.path.startsWith('./')
        ? file.path.slice(2)
        : file.path;
      const directoryPath = filePath.includes('/')
        ? filePath.substring(0, filePath.lastIndexOf('/'))
        : '';

      // First, activate the file browser tab
      await this._app.commands.execute('filebrowser:activate');

      // Navigate to the directory containing the file
      if (directoryPath) {
        await this._app.commands.execute('filebrowser:go-to-path', {
          path: directoryPath
        });
      }

      // Wait a moment for the file browser to update
      await new Promise(resolve => setTimeout(resolve, 300));

      // Try to select/highlight the specific file
      try {
        await this._app.commands.execute('filebrowser:go-to-path', {
          path: filePath
        });
      } catch (selectError) {
        // If specific file selection fails, at least we're in the right directory
        console.warn(
          '[FileExplorerWidget] Could not select specific file, but navigated to directory:',
          selectError
        );
      }

      // Open the file in the main area using the default document factory
      try {
        await this._app.commands.execute('docmanager:open', {
          path: filePath
        });
      } catch (openError) {
        console.error('[FileExplorerWidget] Failed to open file:', openError);
      }

      console.log(`[FileExplorerWidget] Opened file browser at: ${filePath}`);
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Error opening file in browser:',
        error
      );

      // Fallback: just try to activate the file browser
      try {
        await this._app.commands.execute('filebrowser:activate');
      } catch (fallbackError) {
        console.error(
          '[FileExplorerWidget] Fallback file browser activation failed:',
          fallbackError
        );
      }
    }
  }

  /**
   * Update the widget state and trigger re-render
   */
  private updateState(updates: Partial<IFileExplorerState>): void {
    this._state = { ...this._state, ...updates };
    this._stateChanged.emit(this._state);
    this.update();
  }

  /**
   * Infer file info from file name and path
   */
  private inferFileInfo(name: string, path: string): any {
    const extension = name.substring(name.lastIndexOf('.')).toLowerCase();
    return {
      extension,
      is_csv: extension === '.csv',
      is_tsv: extension === '.tsv',
      is_json: extension === '.json',
      is_parquet: extension === '.parquet',
      is_pkl: ['.pkl', '.pickle'].includes(extension),
      is_data: [
        '.csv',
        '.tsv',
        '.json',
        '.parquet',
        '.pkl',
        '.pickle'
      ].includes(extension),
      is_binary: ['.parquet', '.pkl', '.pickle'].includes(extension),
      size_bytes: 0 // We don't have size info from MentionContext
    };
  }

  /**
   * Infer CSV info from content
   */
  private inferCsvInfo(content?: string): any {
    if (!content) {
      return undefined;
    }

    const lines = content.split('\n');
    const header = lines[0];
    const sampleRows = lines.slice(1, 6);

    return {
      type: 'csv',
      preview_type: 'header_and_sample',
      header,
      sample_rows: sampleRows,
      estimated_columns: header ? header.split(',').length : 0
    };
  }

  /**
   * Automatically extract schemas for supported data files in the background
   */
  private async autoExtractSchemas(files: FileEntry[]): Promise<void> {
    try {
      const filesToExtractSchemas = files.filter(file => !file.schema);
      // Filter for supported data files
      const supportedFiles = filesToExtractSchemas.filter(file => {
        const fileType = this.getFileTypeFromPath(file.path);
        return fileType && ['csv', 'tsv', 'parquet', 'pkl'].includes(fileType);
      });

      if (!supportedFiles.length) {
        console.log(
          '[FileExplorerWidget] No supported data files found for schema extraction'
        );
        return;
      }

      console.log(
        `[FileExplorerWidget] Extracting schemas for ${supportedFiles.length} files...`
      );

      // Use the extractMultipleSchemas method with progress tracking
      const results = await PandasSchemaService.extractMultipleSchemas(
        supportedFiles,
        10, // max 10 concurrent
        result => {
          const file = this._state.files.find(
            f => f.absolute_path === result.absolutePath
          );
          if (!file) {
            return;
          }

          if (result.success && result.schema) {
            file.schema = result.schema;
          } else if (result.error) {
            file.schema = { error: result.error, success: false };
          }

          this.updateState({ files: [...this._state.files] });
        }
      );

      // Update files with extracted schemas
      let updatedCount = 0;
      const updatedFiles = this._state.files.map(file => {
        const result = results.find(r => r.absolutePath === file.absolute_path);
        if (result?.success && result.schema) {
          updatedCount++;
          return {
            ...file,
            schema: result.schema,
            hasSchema: true
          };
        }
        return file;
      });

      // Update the state with schema information
      this.updateState({ files: updatedFiles });

      // Update cached schemas
      const data = await AppStateService.getState().contentManager?.get(
        DATA_DIRECTORY_FILE,
        {
          content: true
        }
      );
      if (data?.content) {
        const result: ScanResult = JSON.parse(data.content);
        result.files.forEach((file: FileEntry) => {
          const result = results.find(
            r => r.absolutePath === file.absolute_path
          );
          if (result?.success && result.schema) {
            file.schema = result.schema;
          }
        });
        await AppStateService.getState().contentManager?.save(
          DATA_DIRECTORY_FILE,
          {
            ...data,
            content: JSON.stringify(result)
          }
        );
      }

      console.log(
        `[FileExplorerWidget] Successfully extracted schemas for ${updatedCount} files`
      );
    } catch (error) {
      console.error(
        '[FileExplorerWidget] Error during automatic schema extraction:',
        error
      );
      // Don't throw - this is a background operation
    }
  }

  /**
   * Start continuous polling for files and auto-extract schemas when files become available
   */
  private async startPollingForFiles(): Promise<void> {
    if (this._isPolling) {
      console.log(
        '[FileExplorerWidget] Polling already active, skipping start'
      );
      return;
    }

    this._isPolling = true;
    console.log('[FileExplorerWidget] Starting continuous file polling...');

    const pollForFiles = async () => {
      if (!this._isPolling) {
        return; // Stop if polling was disabled
      }

      try {
        // Try to get the current kernel from AppState
        const currentNotebook = AppStateService.getState().currentNotebook;
        const kernel = currentNotebook?.sessionContext?.session?.kernel;

        if (!kernel) {
          console.error('[FileExplorerWidget] No kernel available');
          this._pollingTimer = setTimeout(pollForFiles, 3000); // Poll every 3 seconds
          return;
        }

        // Load files from DataLoaderService
        const data = await this.loadFilesFromCache();
        if (data) {
          const { files } = data;

          const oldFilesMap = new Map(
            this._state.files.map(f => [f.absolute_path, f])
          );
          const newFilesMap = new Map(files.map(f => [f.absolute_path, f]));

          // Find new files (in cache, not in state)
          const newFiles = files.filter(f => !oldFilesMap.has(f.absolute_path));
          // Find files that still exist (in both cache and state)
          const existingFiles = this._state.files.filter(f =>
            newFilesMap.has(f.absolute_path)
          );
          // Remove files that were deleted from cache (i.e., not in newFilesMap)
          // Only keep files that are in the cache and not uploaded
          const updatedFiles = [...newFiles, ...existingFiles].filter(
            file => !file.uploaded
          );

          // Only update state if there are changes (new files or deleted files)
          const currentPaths = new Set(
            this._state.files.map(f => f.absolute_path)
          );
          const updatedPaths = new Set(updatedFiles.map(f => f.absolute_path));

          let newFilesState = this._state.files;
          if (!this.setsAreEqual(currentPaths, updatedPaths)) {
            newFilesState = updatedFiles;
            this.updateState({
              files: updatedFiles,
              isLoading: false,
              totalFileCount: files.length
            });
          }

          const filesWithoutSchema = newFilesState.filter(file => !file.schema);
          if (filesWithoutSchema.length) {
            await this.autoExtractSchemas(filesWithoutSchema);
          }
        }

        // Continue polling - never stop
        if (this._isPolling) {
          this._pollingTimer = setTimeout(pollForFiles, 3000); // Poll every 3 seconds
        }
      } catch (error) {
        console.error('[FileExplorerWidget] Error during polling:', error);

        // Continue polling even on error
        if (this._isPolling) {
          this._pollingTimer = setTimeout(pollForFiles, 5000); // Longer interval on error
        }
      }
    };

    // Start first poll immediately
    await pollForFiles();
  }

  /**
   * Helper method to compare two sets for equality
   */
  private setsAreEqual<T>(set1: Set<T>, set2: Set<T>): boolean {
    if (set1.size !== set2.size) {
      return false;
    }
    for (const item of set1) {
      if (!set2.has(item)) {
        return false;
      }
    }
    return true;
  }

  /**
   * Stop the polling timer and disable polling
   */
  private stopPolling(): void {
    console.log('[FileExplorerWidget] Stopping file polling...');
    this._isPolling = false;
    if (this._pollingTimer) {
      clearTimeout(this._pollingTimer);
      this._pollingTimer = null;
    }
  }

  /**
   * Handle file upload
   */
  private async handleFileUpload(files: FileList): Promise<void> {
    try {
      console.log(
        '[FileExplorerWidget] Starting file upload:',
        files.length,
        'files'
      );

      this.updateState({
        isUploading: true,
        uploadProgress: { completed: 0, total: files.length },
        error: undefined
      });

      const contentManager = AppStateService.getState().contentManager;
      if (!contentManager) {
        throw new Error('Content manager not available');
      }

      const uploadedFiles: FileEntry[] = [];

      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        try {
          // Upload file to /data directory
          const filePath = `data/${file.name}`;
          const content = await this.readFileAsText(file);

          const model = {
            type: 'file' as const,
            format: 'text' as const,
            content
          };

          await contentManager.save(filePath, model);
          console.log('[FileExplorerWidget] Uploaded file:', filePath);

          // Create FileEntry for the uploaded file
          const fileEntry: FileEntry = {
            uploaded: true,
            absolute_path: filePath,
            id: filePath,
            name: file.name,
            path: `./${filePath}`,
            relative_path: file.name,
            is_directory: false,
            file_info: this.inferFileInfo(file.name, filePath),
            content_preview: content.substring(0, 5000), // First 5000 chars
            csv_info:
              file.name.endsWith('.csv') || file.name.endsWith('.tsv')
                ? this.inferCsvInfo(content)
                : undefined
          };

          uploadedFiles.push(fileEntry);

          // Update progress
          this.updateState({
            uploadProgress: { completed: i + 1, total: files.length }
          });
        } catch (error) {
          console.error(
            '[FileExplorerWidget] Failed to upload file:',
            file.name,
            error
          );
          // Continue with other files even if one fails
        }
      }

      // Add uploaded files to state immediately for instant feedback
      if (uploadedFiles.length > 0) {
        // Add to current state
        const currentFiles = [...this._state.files];
        const newFiles = [...uploadedFiles, ...currentFiles];

        this.updateState({
          files: newFiles,
          totalFileCount: newFiles.length
        });

        console.log(
          '[FileExplorerWidget] Files uploaded successfully. Schemas can be extracted on-demand.'
        );
      }

      const kernel =
        AppStateService.getState().currentNotebook?.sessionContext?.session
          ?.kernel;
      if (kernel) {
        void DataLoaderService.refreshDataDirectory(kernel);
      }

      this.updateState({
        isUploading: false,
        uploadProgress: undefined
      });

      console.log('[FileExplorerWidget] File upload completed successfully');
    } catch (error) {
      console.error('[FileExplorerWidget] File upload failed:', error);
      this.updateState({
        isUploading: false,
        uploadProgress: undefined,
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  }

  /**
   * Read file as text
   */
  private readFileAsText(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => {
        resolve((e.target?.result as string) || '');
      };
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      reader.readAsText(file);
    });
  }

  /**
   * Get file type from path
   */
  private getFileTypeFromPath(path: string): string | null {
    const extension = path.toLowerCase().split('.').pop();
    switch (extension) {
      case 'csv':
        return 'csv';
      case 'tsv':
        return 'tsv';
      case 'json':
        return 'json';
      case 'parquet':
        return 'parquet';
      case 'pkl':
      case 'pickle':
        return 'pkl';
      default:
        return null;
    }
  }
}

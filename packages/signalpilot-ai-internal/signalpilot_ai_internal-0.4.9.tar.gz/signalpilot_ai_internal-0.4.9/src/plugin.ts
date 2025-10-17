import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ISettingRegistry } from '@jupyterlab/settingregistry';
import {
  ICommandPalette,
  IThemeManager,
  IToolbarWidgetRegistry
} from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { NotebookDiffTools } from './Notebook/NotebookDiffTools';
import { KernelExecutionListener } from './Chat/ChatContextMenu/KernelExecutionListener';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { activateSage } from './activateSage';
import {
  getGlobalDiffNavigationWidget,
  getGlobalSnippetCreationWidget,
  setGlobalDiffNavigationWidget,
  setGlobalSnippetCreationWidget
} from './globalWidgets';
import { posthogService } from './Services/PostHogService';
import { Widget } from '@lumino/widgets';
import { AppStateService } from './AppState';

/**
 * Initialization data for the sage-ai extension
 */
export const plugin: JupyterFrontEndPlugin<void> = {
  id: 'signalpilot-ai-internal:plugin',
  description: 'SignalPilot AI - Your AI Data Partner',
  autoStart: true,
  requires: [
    INotebookTracker,
    ICommandPalette,
    IThemeManager,
    IStateDB,
    IDocumentManager
  ],
  optional: [ISettingRegistry, IToolbarWidgetRegistry],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    palette: ICommandPalette,
    themeManager: IThemeManager,
    db: IStateDB,
    documentManager: IDocumentManager,
    settingRegistry: ISettingRegistry | null,
    toolbarRegistry: IToolbarWidgetRegistry | null
  ) => {
    console.log('JupyterLab extension signalpilot-ai-internal is activated!');
    console.log(window.location.href);

    // Initialize PostHog
    void posthogService.initialize();

    // Handle authentication callback early in the initialization process
    const handleEarlyAuth = async () => {
      try {
        // Import StateDBCachingService and JupyterAuthService dynamically to avoid circular dependencies
        const { StateDBCachingService } = await import(
          './utils/backendCaching'
        );
        const { JupyterAuthService } = await import(
          './Services/JupyterAuthService'
        );

        // Initialize StateDB caching service early so authentication can use it
        StateDBCachingService.initialize();

        // Check for temp_token in URL and handle authentication callback
        const urlParams = new URLSearchParams(window.location.search);
        const tempToken = urlParams.get('temp_token');
        const isCallback = urlParams.get('auth_callback') === 'true';

        if (isCallback && tempToken) {
          console.log(
            'Processing temp_token during plugin initialization:',
            tempToken
          );

          // Handle the auth callback early
          const authSuccess = await JupyterAuthService.handleAuthCallback();
          if (authSuccess) {
            console.log(
              'Authentication successful during plugin initialization'
            );
            void posthogService.identifyUser();
            // User identification is now handled by PostHogService
            console.log('Authentication callback handled');
          } else {
            console.error('Authentication failed during plugin initialization');
          }
        }
      } catch (error) {
        console.error('Error processing early authentication:', error);
      }

      // Continue with normal activation regardless of auth result
      void activateSage(
        app,
        notebooks,
        palette,
        themeManager,
        db,
        documentManager,
        settingRegistry,
        toolbarRegistry,
        plugin
      );
    };

    // Start the async authentication handling
    void handleEarlyAuth();
  },
  deactivate: () => {
    console.log('JupyterLab extension signalpilot-ai-internal is deactivated!');

    // Cleanup snippet creation widget
    const snippetWidget = getGlobalSnippetCreationWidget();
    if (snippetWidget && !snippetWidget.isDisposed) {
      snippetWidget.dispose();
      setGlobalSnippetCreationWidget(undefined);
    }

    // Cleanup diff navigation widget
    const diffWidget = getGlobalDiffNavigationWidget();
    if (diffWidget && !diffWidget.isDisposed) {
      // Remove from DOM (could be attached to notebook or document.body)
      if (diffWidget.node.parentNode) {
        diffWidget.node.parentNode.removeChild(diffWidget.node);
      }
      diffWidget.dispose();
      setGlobalDiffNavigationWidget(undefined);
    }

    // Cleanup kernel execution listener
    const kernelExecutionListener = KernelExecutionListener.getInstance();
    kernelExecutionListener.dispose();

    // Cleanup theme detection
    NotebookDiffTools.cleanupThemeDetection();
  }
};

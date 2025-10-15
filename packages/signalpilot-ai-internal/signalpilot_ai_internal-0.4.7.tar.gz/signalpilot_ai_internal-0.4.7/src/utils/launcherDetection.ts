/**
 * Utility functions for detecting the launcher screen
 */

/**
 * Detects if the user is currently on the launcher screen
 * by checking for the presence of the 'lm-Widget jp-Launcher' class combination
 * @returns true if launcher screen is detected, false otherwise
 */
export function isLauncherScreenActive(): boolean {
  // Look for elements with both 'lm-Widget' and 'jp-Launcher' classes
  const launcherElement = document.querySelector('.lm-Widget.jp-Launcher');
  
  if (!launcherElement) {
    return false;
  }
  
  // Additional check: make sure the launcher is actually visible
  // (not just in the DOM but hidden)
  const isVisible = (element: Element): boolean => {
    const htmlElement = element as HTMLElement;
    return !!(
      htmlElement.offsetWidth ||
      htmlElement.offsetHeight ||
      htmlElement.getClientRects().length
    );
  };
  
  return isVisible(launcherElement);
}

/**
 * Detects if any notebook is currently open
 * @returns true if a notebook is open, false otherwise
 */
export function isNotebookOpen(): boolean {
  const notebookPanel = document.querySelector('.jp-NotebookPanel');
  return !!notebookPanel;
}

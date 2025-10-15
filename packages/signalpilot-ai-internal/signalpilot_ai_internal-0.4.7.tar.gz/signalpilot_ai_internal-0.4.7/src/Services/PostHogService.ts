import posthog from 'posthog-js';
import { JupyterAuthService } from './JupyterAuthService';

export class PostHogService {
  private static instance: PostHogService;
  private initialized = false;
  private readonly POSTHOG_PROJECT_API_KEY =
    'phc_E3oZ3UN1nOoWsMMKtPBAGKSqQCtuKutiwmfUZAu3ybr';
  private readonly POSTHOG_API_HOST = 'https://user.signalpilot.ai'; // Production PostHog instance

  private constructor() {}

  public static getInstance(): PostHogService {
    if (!PostHogService.instance) {
      PostHogService.instance = new PostHogService();
    }
    return PostHogService.instance;
  }

  /**
   * Initialize PostHog with proper configuration
   * Only tracks in production environment
   */
  public async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Only initialize tracking in production
      if (this.isProduction()) {
        posthog.init(this.POSTHOG_PROJECT_API_KEY, {
          api_host: this.POSTHOG_API_HOST,
          persistence: 'localStorage',
          cross_subdomain_cookie: false,
          secure_cookie: window.location.protocol === 'https:',
          loaded: posthog => {
            // Disable autocapture in development
            if (!this.isProduction()) {
              posthog.config.autocapture = false;
            }
          }
        });

        // Identify user after initialization
        await this.identifyUser();
      } else {
        console.log('PostHog tracking disabled in development environment');
      }

      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize PostHog:', error);
    }
  }

  /**
   * Identify user with their profile information
   */
  public async identifyUser(): Promise<void> {
    try {
      const userProfile = await JupyterAuthService.getUserProfile();
      if (userProfile && this.isProduction()) {
        posthog.identify(userProfile.id, userProfile);
      }
    } catch (error) {
      console.error('Failed to identify user:', error);
    }
  }

  /**
   * Check if we're in production environment
   */
  private isProduction(): boolean {
    const isDev = process.env.NODE_ENV === 'development';

    return !isDev;
  }
}

// Export a singleton instance
export const posthogService = PostHogService.getInstance();

import * as React from 'react';
import { Modal, Button } from 'react-bootstrap';

/**
 * Props for the JWTAuthModal component
 */
export interface JWTAuthModalProps {
  isVisible: boolean;
  onLogin: () => void;
  onDismiss?: () => void;
}

/**
 * JWT Authentication modal component that appears when JWT is not set or invalid
 */
export function JWTAuthModal({
  isVisible,
  onLogin,
  onDismiss
}: JWTAuthModalProps): JSX.Element | null {
  console.log('[JWTAuthModal] Render called with isVisible:', isVisible);

  if (!isVisible) {
    console.log('[JWTAuthModal] Not visible, returning null');
    return null;
  }

  console.log('[JWTAuthModal] Rendering modal');

  const handleLogin = () => {
    console.log('[JWTAuthModal] Login clicked');
    onLogin();
  };

  const handleDismiss = () => {
    console.log('[JWTAuthModal] Dismiss clicked');
    if (onDismiss) {
      onDismiss();
    }
  };

  return (
    <Modal
      show={isVisible}
      backdrop="static"
      keyboard={false}
      centered
      dialogClassName="sage-ai-jwt-auth-modal"
    >
      <div className="sage-ai-jwt-auth-logo-container">
        <svg width="23" height="24" viewBox="0 0 23 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" clipRule="evenodd" d="M10.3937 0.0761562C10.5124 0.139743 10.6113 0.233873 10.6798 0.348458C10.7482 0.463042 10.7836 0.593761 10.7822 0.726604V6.91066C10.7822 7.02229 10.7563 7.13244 10.7063 7.2327C10.6563 7.33296 10.5836 7.42066 10.4939 7.4891L8.4315 9.05642C9.40159 9.72007 10.7822 10.6597 10.7822 12.0002C10.7822 13.4199 9.52377 14.422 8.39485 15.0437L10.4719 16.491C10.6674 16.6314 10.7822 16.851 10.7822 17.091V23.2751C10.7822 23.5439 10.638 23.7911 10.401 23.9171C10.2857 23.978 10.1555 24.0063 10.0248 23.9988C9.89408 23.9914 9.76803 23.9486 9.66061 23.8751L1.75448 18.4255C1.22738 18.0763 0.793064 17.6082 0.487834 17.0603C0.182604 16.5125 0.0153307 15.9008 0 15.2765C0 14.38 0.403188 13.2999 1.74714 12.029C0.719629 11.1674 0 10.1233 0 8.72519C0 7.05227 1.97684 5.61816 3.19129 4.84891L9.63862 0.139761C9.74605 0.0613494 9.87359 0.0138669 10.007 0.00263312C10.1403 -0.00860067 10.2742 0.0168576 10.3937 0.0761562ZM3.04834 6.73425C2.52297 7.15788 1.43803 7.95594 1.43803 8.72519C1.43803 9.79807 2.09902 10.4617 2.87485 11.0894L5.03129 9.69967L6.46932 10.5469L4.08319 11.9942L7.04356 14.0908C7.83527 13.7584 9.34417 13.0311 9.34417 12.0002C9.34417 10.907 7.57625 10.2289 6.79309 9.69967C5.54932 8.8524 3.85349 8.06154 3.05445 6.73425H3.04834ZM2.90417 12.9255C1.59687 14.0968 1.43803 14.8816 1.43803 15.2765C1.43803 15.7925 1.70438 16.6386 2.5523 17.2182H2.55963L3.17052 17.6418C3.36574 17.1191 3.67163 16.6431 4.068 16.245C4.46437 15.847 4.94219 15.5361 5.46991 15.3329L6.53285 16.3638C5.6715 16.7454 4.7796 17.5146 4.61466 17.8819C4.51852 18.0899 4.47412 18.3173 4.48515 18.5455L9.34417 21.8986V17.4714C7.19003 15.9664 5.04334 14.451 2.90417 12.9255ZM4.22614 5.88698C4.71485 6.91786 6.2604 7.59591 7.16574 8.20315L9.34417 6.54343V2.15231L4.22614 5.89418V5.88698ZM12.6002 0.0833568C12.7141 0.0230493 12.8426 -0.00547802 12.9719 0.000868599C13.1011 0.00721522 13.2261 0.0481935 13.3333 0.119359L20.8802 5.21613C22.1386 6.0562 23 7.15068 23 8.72519C23 10.0165 22.1741 11.1038 21.2748 11.9438C22.0653 12.5799 23 13.6384 23 15.2765C23 17.3238 21.4838 18.3055 20.4844 18.9475L20.1606 19.1516C19.6144 19.526 15.3822 22.4422 13.3479 23.8751C13.2405 23.9486 13.1145 23.9914 12.9838 23.9988C12.8531 24.0063 12.7229 23.978 12.6075 23.9171C12.4901 23.8542 12.392 23.7614 12.3236 23.6484C12.2553 23.5354 12.2191 23.4065 12.219 23.2751V17.091C12.219 16.8654 12.3265 16.647 12.5061 16.5114L14.5257 14.9801C13.4054 14.296 12.219 13.5111 12.219 12.0002C12.219 10.6741 13.6057 9.64326 14.5551 8.94361L12.5281 7.5035C12.4325 7.43574 12.3547 7.34667 12.301 7.24361C12.2472 7.14055 12.2191 7.02645 12.219 6.91066V0.726604C12.2169 0.596407 12.2513 0.468149 12.3186 0.355935C12.3858 0.24372 12.4833 0.151896 12.6002 0.0905574V0.0833568ZM15.8062 9.82687C15.2527 10.2217 13.6558 11.153 13.6558 12.0002C13.6558 13.1727 15.4103 13.822 16.18 14.2876L16.2081 14.302C17.5594 15.2141 19.2479 15.9893 20.1325 17.4294C20.9657 16.8582 21.562 16.3218 21.562 15.2765C21.562 14.1256 20.8228 13.3983 20.1398 12.8979L17.9687 14.5492L16.5319 13.822L18.9034 12.0218L15.8123 9.83287L15.8062 9.82687ZM20.0824 11.0834L13.6558 6.52903V2.0815L18.2925 5.20893C19.0475 5.71777 16.8263 7.39789 16.5319 7.63791L17.9687 8.36517C18.7751 7.70872 19.3774 7.26348 19.744 6.19061L20.0897 6.42342C20.9303 6.98746 21.5632 7.64511 21.5632 8.72519C21.5632 9.68526 20.7434 10.4893 20.0824 11.0834ZM18.9315 18.2347C18.2852 17.1054 16.8691 16.4982 15.8416 15.7985L13.6571 17.4582V21.8842L18.9388 18.2347H18.9315Z" fill="#D9D9D9"/>
        </svg>
      </div>
      <Modal.Body className="sage-ai-jwt-auth-body">
        <div className="sage-ai-jwt-auth-content">
          <h3 className="sage-ai-jwt-auth-subtitle">
            Welcome to SignalPilot!
          </h3>
          
          <p className="sage-ai-jwt-auth-message">
            To start using SignalPilot, please log in to your account. We'll get you set up with all the amazing AI features in just a moment!
          </p>

          <div className="sage-ai-jwt-auth-features">
            <div className="sage-ai-jwt-auth-feature">
              <div className="sage-ai-jwt-auth-feature-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 11H15M9 15H15M17 21H7C5.89543 21 5 20.1046 5 19V5C5 3.89543 5.89543 3 7 3H12.5858C12.851 3 13.1054 3.10536 13.2929 3.29289L19.7071 9.70711C19.8946 9.89464 20 10.149 20 10.4142V19C20 20.1046 19.1046 21 18 21H17Z" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                </svg>
              </div>
              <span>AI-powered code assistance</span>
            </div>
            
            <div className="sage-ai-jwt-auth-feature">
              <div className="sage-ai-jwt-auth-feature-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 16V8C21 5.79086 19.2091 4 17 4H7C4.79086 4 3 5.79086 3 8V16C3 18.2091 4.79086 20 7 20H17C19.2091 20 21 18.2091 21 16Z" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                  <path d="M7 4V20M17 4V20M3 12H21" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                </svg>
              </div>
              <span>Database integration tools</span>
            </div>
            
            <div className="sage-ai-jwt-auth-feature">
              <div className="sage-ai-jwt-auth-feature-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 9L12 13L16 9" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                  <path d="M3 4H21V20H3V4Z" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                </svg>
              </div>
              <span>Smart autocomplete & suggestions</span>
            </div>
          </div>
        </div>

        <div className="sage-ai-jwt-auth-actions">
          <Button
            variant="primary"
            size="lg"
            className="sage-ai-jwt-auth-login-btn"
            onClick={handleLogin}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ marginRight: '8px' }}>
              <path d="M15 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H15" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"/>
              <path d="M10 17L15 12L10 7" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"/>
              <path d="M15 12H3" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"/>
            </svg>
            Login or Sign Up
          </Button>

          {onDismiss && (
            <Button
              variant="outline-secondary"
              className="sage-ai-jwt-auth-dismiss-btn"
              onClick={handleDismiss}
            >
              Continue without login
            </Button>
          )}
        </div>
      </Modal.Body>
    </Modal>
  );
}
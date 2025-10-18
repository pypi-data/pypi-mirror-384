/**
 * Manages the ready state for VS Code integration
 * Only sends the ready message when both DOM and event listeners are ready
 */
declare global {
    interface Window {
        vscode?: {
            postMessage(message: any): void;
        };
    }
}
declare class ReadyStateManager {
    private eventListenerReady;
    private domReady;
    private readySent;
    setEventListenerReady(): void;
    setDomReady(): void;
    private checkAndSendReady;
}
export declare const readyStateManager: ReadyStateManager;
export {};

import { Niivue } from '@niivue/niivue';
import { AppProps } from './components/AppProps';
export declare function handleMessage(message: any, appProps: AppProps): Promise<boolean>;
export declare function listenToMessages(appProps: AppProps): void;
export declare function openImageFromURL(uri: string): void;
export declare function addImageFromURLParams(): void;
export declare function addOverlayEvent(imageIndex: number, type: string): void;
export declare function addImagesEvent(): void;
export declare function addDcmFolderEvent(): void;
export declare class ExtendedNiivue extends Niivue {
    constructor(opts: any);
    isNew: boolean;
    isLoaded: boolean;
    key: number;
    body: null;
    mouseMoveListener(e: MouseEvent): void;
}

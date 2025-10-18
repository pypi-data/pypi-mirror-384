import { Signal } from '@preact/signals';
import { ExtendedNiivue } from '../events';
import { NiiVueSettings } from '../settings';
export declare const enum SelectionMode {
    NONE = 0,
    SINGLE = 1,
    MULTIPLE = 2
}
export interface AppProps {
    nvArray: Signal<ExtendedNiivue[]>;
    selection: Signal<Array<number>>;
    selectionMode: Signal<SelectionMode>;
    hideUI: Signal<number>;
    sliceType: Signal<number>;
    location: Signal<string>;
    settings: Signal<NiiVueSettings>;
}
export interface ScalingOpts {
    isManual: boolean;
    min: number;
    max: number;
}
export declare function useAppState(initialSettings: NiiVueSettings): AppProps;

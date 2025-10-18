import { Signal } from '@preact/signals';
import { ExtendedNiivue } from '../events';
import { AppProps } from './AppProps';
export interface NiiVueCanvasProps {
    nv: ExtendedNiivue;
    width: number;
    height: number;
    render: Signal<number>;
}
export declare const NiiVueCanvas: ({ nv, width, height, sliceType, render, nvArray, settings, }: AppProps & NiiVueCanvasProps) => import("preact").JSX.Element;

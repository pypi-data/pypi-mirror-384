import { Signal } from '@preact/signals';
import { ExtendedNiivue } from '../events';
import { AppProps } from './AppProps';
export interface VolumeProps {
    name: string;
    volumeIndex: number;
    nv: ExtendedNiivue;
    remove: () => void;
    width: number;
    height: number;
    render: Signal<number>;
}
export declare const Volume: (props: AppProps & VolumeProps) => import("preact").JSX.Element;

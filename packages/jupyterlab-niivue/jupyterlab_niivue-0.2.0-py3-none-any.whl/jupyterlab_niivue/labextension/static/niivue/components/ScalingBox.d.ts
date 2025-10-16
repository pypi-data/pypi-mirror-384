export interface ScalingOpts {
    isManual: boolean;
    min: number;
    max: number;
}
export declare const ScalingBox: (props: any) => import("preact").JSX.Element | null;
interface ScalingProps {
    setScaling: (scaling: ScalingOpts) => void;
    init: any;
}
export declare const Scaling: ({ setScaling, init }: ScalingProps) => import("preact").JSX.Element;
export {};

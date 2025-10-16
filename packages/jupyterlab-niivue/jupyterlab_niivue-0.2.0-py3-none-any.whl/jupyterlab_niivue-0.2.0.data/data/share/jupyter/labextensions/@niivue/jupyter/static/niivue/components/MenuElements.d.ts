import { Signal } from '@preact/signals';
export declare const MenuEntry: ({ label, onClick, isOpen, visible }: any) => import("preact").JSX.Element | null;
export declare const MenuItem: ({ label, onClick, children, visible }: any) => import("preact").JSX.Element | null;
export declare const ToggleEntry: ({ label, state }: any) => import("preact").JSX.Element;
export declare const MenuButton: ({ label, onClick }: {
    label: string;
    onClick: () => void;
}) => import("preact").JSX.Element;
export declare const MenuToggle: ({ label, state }: any) => import("preact").JSX.Element;
export declare const HeaderDialog: ({ nvArraySelected, isOpen }: any) => import("preact").JSX.Element;
export declare const ImageSelect: ({ label, state, children, visible }: any) => import("preact").JSX.Element | null;
export declare function toggle(state: Signal<boolean>): () => boolean;

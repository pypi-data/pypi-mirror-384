import { Signal } from '@preact/signals';
/**
 * Custom hook for managing local storage with signals
 */
export declare function useLocalStorage<T>(key: string, signal: Signal<T>): Signal<T>;
/**
 * Custom hook for debouncing values
 */
export declare function useDebounce<T>(value: T, delay: number): T;

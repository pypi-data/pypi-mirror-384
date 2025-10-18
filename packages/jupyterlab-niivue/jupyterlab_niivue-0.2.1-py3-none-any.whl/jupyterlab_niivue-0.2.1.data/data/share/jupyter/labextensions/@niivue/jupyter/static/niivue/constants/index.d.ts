/**
 * Application constants
 */
export declare const APP_CONFIG: {
    readonly NAME: "NiiVue Medical Image Viewer";
    readonly SHORT_NAME: "NiiVue";
    readonly VERSION: "0.0.1";
    readonly DESCRIPTION: "Advanced web-based medical image viewer for NIfTI and DICOM files";
};
export declare const SUPPORTED_FILE_EXTENSIONS: readonly [".nii", ".nii.gz", ".dcm", ".mha", ".mhd", ".nhdr", ".nrrd", ".mgh", ".mgz", ".npy", ".npz", ".v", ".v16", ".vmr", ".gii", ".mz3"];
export declare const SLICE_TYPES: {
    readonly AXIAL: 0;
    readonly CORONAL: 1;
    readonly SAGITTAL: 2;
    readonly MULTIPLANAR: 3;
    readonly RENDER: 4;
};
export declare const STORAGE_KEYS: {
    readonly USER_SETTINGS: "userSettings";
    readonly RECENT_FILES: "recentFiles";
    readonly LAYOUT_PREFERENCES: "layoutPreferences";
};
export declare const EXTERNAL_URLS: {
    readonly EXAMPLE_IMAGE: "https://niivue.github.io/niivue-demo-images/mni152.nii.gz";
    readonly DOCUMENTATION: "https://niivue.github.io/niivue/";
    readonly GITHUB: "https://github.com/niivue/niivue";
};

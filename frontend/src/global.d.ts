export {}

declare global {
  function __(text: string, args?: any[]): string

  interface String {
    format(...args: any[]): string
  }
}

declare module 'vue' {
  interface ComponentCustomProperties {
    __: (text: string, args?: any[]) => string
  }
}

// Khai báo module frappe-ui để tránh lỗi "Cannot find module"
declare module 'frappe-ui' {
  export const call: (...args: any[]) => Promise<any>
  export const Dialog: any
  export const FormControl: any
  export const Switch: any
  export const toast: {
    success: (message: string) => void
    error: (message: string) => void
    warning: (message: string) => void
    info: (message: string) => void
  }
  export const Button: any
  export const Badge: any
  export const Avatar: any
  export const Input: any
  export const Dropdown: any
  export const Tooltip: any
  export const Spinner: any
  export const ListView: any
  export const ListHeader: any
  export const ListHeaderItem: any
  export const ListRow: any
  export const ListRowItem: any
  export const Autocomplete: any
  export const DatePicker: any
  export const TimePicker: any
  export const TextInput: any
  export const Select: any
  export const Checkbox: any
  export const FileUploader: any
  export const Alert: any
  export const ErrorMessage: any
  export const FeatherIcon: any
  export const Breadcrumbs: any
  export const Tabs: any
  export const setConfig: (...args: any[]) => void
  export const frappeRequest: (...args: any[]) => Promise<any>
  export const useFrappeAuth: (...args: any[]) => any
  export const useFrappeGetDoc: (...args: any[]) => any
  export const useFrappeGetDocList: (...args: any[]) => any
  export const useFrappeCreateDoc: (...args: any[]) => any
  export const useFrappeUpdateDoc: (...args: any[]) => any
  export const useFrappeDeleteDoc: (...args: any[]) => any
  export const resource: (...args: any[]) => any
  export const createListResource: (...args: any[]) => any
  export const createDocumentResource: (...args: any[]) => any
  export const createResource: (...args: any[]) => any
}
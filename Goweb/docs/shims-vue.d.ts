declare module "*.vue" {
  import { DefineComponent } from "vue";
  const comp: DefineComponent;
  export default comp;
}

declare module "*.md" {
  import { DefineComponent } from "vue";
  const comp: DefineComponent;
  export default comp;
}

declare module "prismjs";
declare module "prismjs/components/index";
declare module "escape-html";
declare module "markdown-it-container";

interface ImportMeta {
  env: {
    MODE: string;
    BASE_URL: string;
    PROD: boolean;
    DEV: boolean;
    SSR: boolean;
    VITE_API_URL?: string;
  };
}

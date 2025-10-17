import { FuncNodesReactFlow } from "@/funcnodes-context";

const development: boolean = !!import.meta.env.DEV; // vite

const print_object_size = (
  obj: any,
  message: string,
  fnrf_zst: FuncNodesReactFlow | undefined
): void => {
  if (!fnrf_zst) {
    return;
  }
  if (fnrf_zst.dev_settings.debug) {
    fnrf_zst.logger.debug(
      "Object size: " + JSON.stringify(obj).length + " chars. " + message
    );
  }
};

const print_object = (
  obj: any,
  fnrf_zst: FuncNodesReactFlow | undefined
): void => {
  if (!fnrf_zst) {
    return;
  }
  if (fnrf_zst.dev_settings.debug) {
    fnrf_zst.logger.debug("Object: ", obj);
  }
};

export { print_object_size, print_object, development };

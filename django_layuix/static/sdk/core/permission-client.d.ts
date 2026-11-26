export interface PermissionSnapshot {
  user?: {
    id?: number | string;
    username?: string;
    is_superuser?: boolean;
  } | null;
  permissions?: string[];
  roles?: Array<{ id?: number | string; code?: string; name?: string }>;
  menus?: unknown[];
  plugins?: unknown[];
  scope_nodes?: unknown[];
  abac_policies?: unknown[];
  page_permissions?: Record<string, string>;
  button_actions?: Array<{ value: string; zh_hans?: string; en?: string }>;
  permission_catalog?: string[];
}

export interface PermissionClientOptions {
  endpoint?: string;
  token?: string;
  tokenHeader?: string;
  tokenPrefix?: string;
  credentials?: RequestCredentials;
  headers?: Record<string, string>;
  fetch?: typeof fetch;
  bootstrap?: Partial<PermissionSnapshot>;
}

export interface LoadOptions {
  refresh?: boolean;
}

export interface PermissionClient {
  load(options?: LoadOptions): Promise<PermissionSnapshot>;
  can(code: string): boolean;
  canAny(codes: string | string[]): boolean;
  canAll(codes: string | string[]): boolean;
  hasRole(code: string): boolean;
  menuTree(): unknown[];
  pluginManifest(): unknown[];
  scopeNodes(): unknown[];
  abacPolicies(): unknown[];
  pagePermissions(): Record<string, string>;
  buttonActions(): Array<{ value: string; zh_hans?: string; en?: string }>;
  permissionCatalog(): string[];
  canLoadPage(path: string, options?: { defaultDeny?: boolean }): boolean;
  readonly snapshot: PermissionSnapshot;
  readonly ready: boolean;
  invalidate(): PermissionSnapshot;
  configure(options: PermissionClientOptions): void;
  setToken(token: string): void;
  setSnapshot(data: Partial<PermissionSnapshot>): PermissionSnapshot;
}

export declare function createPermissionClient(
  options?: PermissionClientOptions,
): PermissionClient;

export declare function prefetchPermissions(
  options?: PermissionClientOptions,
): Promise<PermissionSnapshot>;

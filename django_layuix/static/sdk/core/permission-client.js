/**
 * django-layuix framework-agnostic permission client.
 * Works with plain fetch; no external dependency.
 */
export function createPermissionClient(options = {}) {
  const settings = {
    endpoint: options.endpoint || '/admin/api/rbac/frontend/permissions/',
    token: options.token || '',
    tokenHeader: options.tokenHeader || 'Authorization',
    tokenPrefix: options.tokenPrefix || 'Bearer ',
    credentials: options.credentials === undefined ? 'include' : options.credentials,
    headers: options.headers || {},
    fetch: options.fetch || null,
  };

  let snapshot = {
    user: null,
    permissions: [],
    roles: [],
    menus: [],
    plugins: [],
    scope_nodes: [],
    abac_policies: [],
    page_permissions: {},
    button_actions: [],
    permission_catalog: [],
  };
  let ready = false;
  if (options.bootstrap) {
    snapshot = Object.assign({}, snapshot, options.bootstrap);
    ready = true;
  }

  function buildHeaders() {
    const headers = Object.assign({}, settings.headers);
    if (settings.token) {
      headers[settings.tokenHeader] = settings.tokenPrefix + settings.token;
    }
    return headers;
  }

  let loadPromise = null;
  let generation = 0;

  async function load(options = {}) {
    if (loadPromise && !options.refresh) return loadPromise;
    if (ready && !options.refresh) return snapshot;
    const requestGeneration = ++generation;
    const request = (async () => {
      const fetchImpl = settings.fetch || (typeof fetch === 'function' ? fetch : null);
      if (!fetchImpl) throw new Error('fetch is not available; pass options.fetch');
      const response = await fetchImpl(settings.endpoint, {
        method: 'GET',
        credentials: settings.credentials,
        headers: buildHeaders(),
      });
      if (!response.ok) {
        throw new Error('Permission request failed: ' + response.status);
      }
      const payload = await response.json();
      if (payload.code !== 200) {
        throw new Error(payload.msg || 'Permission request failed');
      }
      if (requestGeneration !== generation) return snapshot;
      snapshot = Object.assign({}, snapshot, payload.data || {});
      ready = true;
      return snapshot;
    })();
    loadPromise = request;
    try {
      return await request;
    } finally {
      if (loadPromise === request) loadPromise = null;
    }
  }

  function can(code) {
    if (!ready || !code) return false;
    if (snapshot.user && snapshot.user.is_superuser) return true;
    return (snapshot.permissions || []).indexOf(code) > -1;
  }

  function codeList(codes) {
    if (Array.isArray(codes)) return codes;
    return codes ? [codes] : [];
  }

  function canAny(codes) {
    return codeList(codes).some(can);
  }

  function canAll(codes) {
    return codeList(codes).every(can);
  }

  function hasRole(code) {
    return (snapshot.roles || []).some((role) => role.code === code);
  }

  function menuTree() {
    return snapshot.menus || [];
  }

  function pluginManifest() {
    return snapshot.plugins || [];
  }

  function scopeNodes() {
    return snapshot.scope_nodes || [];
  }

  function abacPolicies() {
    return snapshot.abac_policies || [];
  }

  function pagePermissions() {
    return snapshot.page_permissions || {};
  }

  function buttonActions() {
    return snapshot.button_actions || [];
  }

  function permissionCatalog() {
    return snapshot.permission_catalog || [];
  }

  function canLoadPage(path, options = {}) {
    const required = pagePermissions()[path] || '';
    if (!required) return !options.defaultDeny;
    return can(required);
  }

  return {
    load,
    can,
    canAny,
    canAll,
    hasRole,
    menuTree,
    pluginManifest,
    scopeNodes,
    abacPolicies,
    pagePermissions,
    buttonActions,
    permissionCatalog,
    canLoadPage,
    get snapshot() { return snapshot; },
    get ready() { return ready; },
    invalidate() {
      generation++;
      loadPromise = null;
      ready = false;
      snapshot = {
        user: null,
        permissions: [],
        roles: [],
        menus: [],
        plugins: [],
        scope_nodes: [],
        abac_policies: [],
        page_permissions: {},
        button_actions: [],
        permission_catalog: [],
      };
      return snapshot;
    },
    configure(nextOptions) {
      Object.assign(settings, nextOptions || {});
      this.invalidate();
    },
    setToken(token) {
      settings.token = token || '';
      this.invalidate();
    },
    setSnapshot(data) {
      generation++;
      loadPromise = null;
      snapshot = Object.assign({}, snapshot, data || {});
      ready = true;
      return snapshot;
    },
  };
}

export async function prefetchPermissions(options = {}) {
  const client = createPermissionClient(options);
  await client.load({refresh: true});
  return client.snapshot;
}

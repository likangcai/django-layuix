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
  };

  let snapshot = {
    user: null,
    permissions: [],
    roles: [],
    menus: [],
    plugins: [],
    scope_nodes: [],
    abac_policies: [],
  };

  function buildHeaders() {
    const headers = Object.assign({}, settings.headers);
    if (settings.token) {
      headers[settings.tokenHeader] = settings.tokenPrefix + settings.token;
    }
    return headers;
  }

  let loadPromise = null;

  async function load() {
    if (loadPromise) return loadPromise;
    loadPromise = (async () => {
      const response = await fetch(settings.endpoint, {
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
      snapshot = Object.assign({}, snapshot, payload.data || {});
      return snapshot;
    })();
    try {
      return await loadPromise;
    } finally {
      loadPromise = null;
    }
  }

  function can(code) {
    if (!code) return false;
    if (snapshot.user && snapshot.user.is_superuser) return true;
    return (snapshot.permissions || []).indexOf(code) > -1;
  }

  function canAny(codes) {
    return (codes || []).some(can);
  }

  function canAll(codes) {
    return (codes || []).every(can);
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
    get snapshot() { return snapshot; },
    configure(nextOptions) {
      Object.assign(settings, nextOptions || {});
    },
    setToken(token) { settings.token = token || ''; },
  };
}

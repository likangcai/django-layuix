import { inject, onMounted, ref } from 'vue';
import { createPermissionClient } from '../core/permission-client.js';

export const PERMISSION_KEY = Symbol('layuix-permission');

export const PermissionPlugin = {
  install(app, options = {}) {
    const client = createPermissionClient(options);
    app.config.globalProperties.$permission = client;
    app.provide(PERMISSION_KEY, client);
    const originalDisplay = new WeakMap();
    const apply = (el, value) => {
      if (!originalDisplay.has(el)) originalDisplay.set(el, el.style.display);
      const codes = Array.isArray(value) ? value : [value];
      el.style.display = 'none';
      client.load().then(() => {
        el.style.display = client.canAny(codes) ? (originalDisplay.get(el) || '') : 'none';
      }).catch(() => {
        el.style.display = 'none';
      });
    };
    app.directive('permission', {
      mounted(el, binding) { apply(el, binding.value); },
      updated(el, binding) {
        if (binding.value !== binding.oldValue) apply(el, binding.value);
      },
    });
  },
};

export function usePermission() {
  const client = inject(PERMISSION_KEY, null);
  const ready = ref(false);
  const error = ref(null);

  onMounted(async () => {
    if (!client || ready.value) return;
    try {
      await client.load();
      ready.value = true;
    } catch (err) {
      error.value = err;
    }
  });

  return {
    client,
    ready,
    error,
    can: (code) => !!client && client.can(code),
    canAny: (codes) => !!client && client.canAny(codes),
    canAll: (codes) => !!client && client.canAll(codes),
    hasRole: (code) => !!client && client.hasRole(code),
    menus: () => (client ? client.menuTree() : []),
    plugins: () => (client ? client.pluginManifest() : []),
    scopeNodes: () => (client ? client.scopeNodes() : []),
    abacPolicies: () => (client ? client.abacPolicies() : []),
    pagePermissions: () => (client ? client.pagePermissions() : {}),
    buttonActions: () => (client ? client.buttonActions() : []),
    permissionCatalog: () => (client ? client.permissionCatalog() : []),
    canLoadPage: (path) => !!client && client.canLoadPage(path),
  };
}

export function createPermissionGuard(client) {
  return async (to, from, next) => {
    if (!client.snapshot.user) await client.load();
    const required = to.meta && to.meta.permissions;
    if (!required || client.canAny(Array.isArray(required) ? required : [required])) {
      next();
    } else {
      next(from && from.fullPath ? from.fullPath : '/');
    }
  };
}

/**
 * django-layuix Svelte permission bindings.
 * Requires Svelte 4+ as a peer dependency of the consuming application.
 */
import { getContext, setContext } from 'svelte';
import { writable } from 'svelte/store';
import { createPermissionClient } from '../core/permission-client.js';

export const PERMISSION_KEY = Symbol('layuix-permission-svelte');

export function createPermissionStore(options = {}) {
  const client = createPermissionClient(options);
  const store = writable({
    ready: client.ready,
    error: null,
    snapshot: client.snapshot,
  });

  async function load({ refresh: force = false } = {}) {
    try {
      const snapshot = await client.load({ refresh: force });
      store.set({ ready: true, error: null, snapshot });
      return snapshot;
    } catch (error) {
      store.set({ ready: false, error, snapshot: client.snapshot });
      throw error;
    }
  }

  function refresh() {
    return load({ refresh: true });
  }

  function invalidate() {
    const snapshot = client.invalidate();
    store.set({ ready: false, error: null, snapshot });
  }

  return {
    subscribe: store.subscribe,
    client,
    load,
    refresh,
    invalidate,
    can: (code) => client.can(code),
    canAny: (codes) => client.canAny(codes),
    canAll: (codes) => client.canAll(codes),
    hasRole: (code) => client.hasRole(code),
    menus: () => client.menuTree(),
    plugins: () => client.pluginManifest(),
    scopeNodes: () => client.scopeNodes(),
    abacPolicies: () => client.abacPolicies(),
    pagePermissions: () => client.pagePermissions(),
    buttonActions: () => client.buttonActions(),
    permissionCatalog: () => client.permissionCatalog(),
    canLoadPage: (path) => client.canLoadPage(path),
  };
}

export function providePermission(store) {
  setContext(PERMISSION_KEY, store);
  return store;
}

export function usePermission() {
  return getContext(PERMISSION_KEY);
}

export function createPermissionAction(store) {
  const permissionStore = store || usePermission();
  if (!permissionStore) {
    throw new Error('Permission store is missing. Call providePermission() first.');
  }
  const originalDisplay = new WeakMap();

  const apply = (node, value) => {
    if (!originalDisplay.has(node)) originalDisplay.set(node, node.style.display);
    const codes = Array.isArray(value) ? value : [value];
    node.style.display = 'none';
    Promise.resolve(permissionStore.load()).then(() => {
      const allowed = permissionStore.canAny(codes);
      node.style.display = allowed ? (originalDisplay.get(node) || '') : 'none';
    }).catch(() => {
      node.style.display = 'none';
    });
  };

  return (node, value) => {
    apply(node, value);
    return {
      update(nextValue) {
        if (JSON.stringify(nextValue) !== JSON.stringify(value)) {
          value = nextValue;
          apply(node, nextValue);
        }
      },
    };
  };
}

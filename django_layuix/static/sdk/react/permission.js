import React, { createContext, useContext, useEffect, useState } from 'react';
import { createPermissionClient } from '../core/permission-client.js';

const PermissionContext = createContext(null);

export function PermissionProvider(props) {
  const [client, setClient] = useState(props.client || null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    const instance = client || createPermissionClient(props.options || {});
    if (!client) setClient(instance);
    instance.load().then(() => {
      if (active) setReady(true);
    }).catch((err) => {
      if (active) setError(err);
    });
    return () => { active = false; };
  }, [client]);

  return React.createElement(
    PermissionContext.Provider,
    { value: { client, ready, error } },
    props.children
  );
}

export function usePermission() {
  const value = useContext(PermissionContext);
  const client = value && value.client;
  return {
    client,
    ready: !!(value && value.ready),
    error: value && value.error,
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

export function Can(props) {
  const permission = usePermission();
  const required = Array.isArray(props.perm) ? props.perm : [props.perm];
  const allowed = props.requireAll ? permission.canAll(required) : permission.canAny(required);
  return allowed ? props.children : (props.fallback || null);
}

export function withPermission(Component, required, fallback = null) {
  return function Guarded(props) {
    return React.createElement(Can, { perm: required, fallback }, React.createElement(Component, props));
  };
}

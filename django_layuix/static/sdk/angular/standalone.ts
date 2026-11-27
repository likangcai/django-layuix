/**
 * django-layuix Angular standalone permission bootstrap.
 * Requires Angular 15+ and @angular/router as peer dependencies.
 */
import { APP_INITIALIZER, Provider, Type, inject } from '@angular/core';
import {
  ActivatedRouteSnapshot, CanActivateFn, Router, RouterStateSnapshot,
  UrlTree, provideRouter, Routes,
} from '@angular/router';
import { bootstrapApplication } from '@angular/platform-browser';
import { LayuiPermissionOptions, PermissionService } from './permission';

export function provideLayuiPermission(options: LayuiPermissionOptions = {}): Provider[] {
  return [
    PermissionService,
    {
      provide: APP_INITIALIZER,
      multi: true,
      deps: [PermissionService],
      useFactory: (permission: PermissionService) => () =>
        permission.load().catch(() => undefined),
    },
  ];
}

function normalizeRoutePath(url: string): string {
  return '/' + String(url || '').split('?')[0].replace(/^\/+/, '');
}

export const layuiPermissionGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot,
): Promise<boolean | UrlTree> => {
  const permission = inject(PermissionService);
  const router = inject(Router);
  const raw = route.data['permissions'] ?? route.data['layuiPermissions'];
  const codes = Array.isArray(raw) ? raw : (raw ? [raw] : []);

  return permission.load()
    .catch(() => permission.load({ refresh: true }))
    .then(() => {
      if (codes.length) {
        return permission.canAny(codes) ? true : router.parseUrl('/403');
      }
      return permission.canLoadPage(normalizeRoutePath(state.url), { defaultDeny: true })
        ? true
        : router.parseUrl('/403');
    })
    .catch(() => router.parseUrl('/403'));
};

export function bootstrapLayuiStandalone(
  rootComponent: Type<unknown>,
  options: LayuiPermissionOptions = {},
  routes: Routes = [],
): Promise<unknown> {
  return bootstrapApplication(rootComponent, {
    providers: [
      provideRouter(routes),
      provideLayuiPermission(options),
    ],
  });
}

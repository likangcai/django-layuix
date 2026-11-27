/**
 * django-layuix Angular permission bindings.
 * Requires Angular 15+ as a peer dependency of the consuming application.
 */
import { Directive, ElementRef, Injectable, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { createPermissionClient } from '../core/permission-client.js';

export interface LayuiPermissionOptions {
  endpoint?: string;
  token?: string;
  tokenHeader?: string;
  tokenPrefix?: string;
  credentials?: RequestCredentials;
  headers?: Record<string, string>;
}

@Injectable({ providedIn: 'root' })
export class PermissionService {
  private readonly client = createPermissionClient();

  ready = false;
  error: unknown = null;

  configure(options: LayuiPermissionOptions): void {
    this.client.configure(options);
    this.ready = false;
  }

  async load(options: { refresh?: boolean } = {}): Promise<void> {
    if (this.ready && !options.refresh) return;
    try {
      await this.client.load(options);
      this.ready = true;
      this.error = null;
    } catch (error) {
      this.error = error;
      throw error;
    }
  }

  can(code: string): boolean {
    return this.client.can(code);
  }

  canAny(codes: string | string[]): boolean {
    return this.client.canAny(codes);
  }

  canAll(codes: string | string[]): boolean {
    return this.client.canAll(codes);
  }

  hasRole(code: string): boolean {
    return this.client.hasRole(code);
  }

  menus(): unknown[] {
    return this.client.menuTree();
  }

  plugins(): unknown[] {
    return this.client.pluginManifest();
  }

  scopeNodes(): unknown[] {
    return this.client.scopeNodes();
  }

  abacPolicies(): unknown[] {
    return this.client.abacPolicies();
  }

  pagePermissions(): Record<string, string> {
    return this.client.pagePermissions();
  }

  buttonActions(): unknown[] {
    return this.client.buttonActions();
  }

  permissionCatalog(): string[] {
    return this.client.permissionCatalog();
  }

  canLoadPage(path: string): boolean {
    return this.client.canLoadPage(path);
  }
}

@Directive({
  selector: '[layuiPermission]',
  standalone: true,
})
export class PermissionDirective implements OnInit, OnChanges {
  @Input('layuiPermission') permissions: string | string[] = [];
  @Input() requireAll = false;
  private readonly originalDisplay = new WeakMap<HTMLElement, string>();

  constructor(
    private readonly elementRef: ElementRef<HTMLElement>,
    private readonly permission: PermissionService,
  ) {}

  ngOnInit(): void {
    this.apply();
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.apply();
  }

  private apply(): void {
    const node = this.elementRef.nativeElement;
    if (!this.originalDisplay.has(node)) {
      this.originalDisplay.set(node, node.style.display || '');
    }
    node.style.display = 'none';
    this.permission.load().then(() => {
      const codes = Array.isArray(this.permissions) ? this.permissions : [this.permissions];
      const allowed = this.requireAll
        ? this.permission.canAll(codes)
        : this.permission.canAny(codes);
      node.style.display = allowed ? this.originalDisplay.get(node) || '' : 'none';
    }).catch(() => {
      node.style.display = 'none';
    });
  }
}

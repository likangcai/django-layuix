/**
 * SvelteKit server-side permission prefetch helper.
 * Uses the framework-provided `fetch` so cookies and relative URLs work in SSR.
 */
import { prefetchPermissions } from '../core/permission-client.js';

export async function prefetchServerPermissions(event, options = {}) {
  const source = event.request && event.request.headers ? event.request.headers : null;
  const headers = new Headers(options.headers || {});
  for (const name of ['cookie', 'authorization', 'x-token']) {
    if (!headers.has(name) && source && source.has(name)) {
      headers.set(name, source.get(name));
    }
  }
  return prefetchPermissions(Object.assign({}, options, {
    fetch: event.fetch,
    credentials: options.credentials === undefined ? 'same-origin' : options.credentials,
    headers,
  }));
}

<script>
  import { usePermission } from './permission.js';

  export let perm = [];
  export let requireAll = false;

  const permission = usePermission();
  if (!permission) {
    throw new Error('Permission store is missing. Call providePermission() first.');
  }

  $: codes = Array.isArray(perm) ? perm : [perm];
  $: allowed = $permission.ready
    && (requireAll ? permission.canAll(codes) : permission.canAny(codes));
</script>

{#if allowed}
  <slot />
{/if}

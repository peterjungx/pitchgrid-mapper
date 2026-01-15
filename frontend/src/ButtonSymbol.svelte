<script lang="ts">
  export let type: 'plus' | 'minus' | 'up' | 'down';

  const size = 24;
  const strokeWidth = 2.5;
</script>

<svg width={size} height={size} viewBox="0 0 {size} {size}">
  {#if type === 'plus'}
    <!-- Plus sign: horizontal and vertical lines -->
    <line x1={size/2} y1={size * 0.25} x2={size/2} y2={size * 0.75} stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" />
    <line x1={size * 0.25} y1={size/2} x2={size * 0.75} y2={size/2} stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" />
  {:else if type === 'minus'}
    <!-- Minus sign: horizontal line -->
    <line x1={size * 0.25} y1={size/2} x2={size * 0.75} y2={size/2} stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" />
  {:else if type === 'up'}
    <!-- Up arrow -->
    <line x1={size/2} y1={size * 0.3} x2={size/2} y2={size * 0.75} stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" />
    <polyline points="{size * 0.3},{size * 0.45} {size/2},{size * 0.25} {size * 0.7},{size * 0.45}" fill="none" stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" stroke-linejoin="round" />
  {:else if type === 'down'}
    <!-- Down arrow -->
    <line x1={size/2} y1={size * 0.25} x2={size/2} y2={size * 0.7} stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" />
    <polyline points="{size * 0.3},{size * 0.55} {size/2},{size * 0.75} {size * 0.7},{size * 0.55}" fill="none" stroke="currentColor" stroke-width={strokeWidth} stroke-linecap="round" stroke-linejoin="round" />
  {/if}
</svg>

<style>
  svg {
    display: block;
  }
</style>

<script lang="ts">
  export let x: number;  // logical x
  export let y: number;  // logical y
  export let phys_x: number;  // physical x (center)
  export let phys_y: number;  // physical y (center)
  export let shape: Array<[number, number]> = [];  // Voronoi vertices in physical coordinates
  export let isActive: boolean = false;
  export let color: string = '#3a3a3a';
  export let onClick: () => void = () => {};

  // Generate SVG path from Voronoi shape
  $: shapePath = shape && shape.length > 0
    ? generatePath(shape, phys_x, phys_y)
    : generateHexagonPath(phys_x, phys_y, 0.5);

  function generatePath(vertices: Array<[number, number]>, centerX: number, centerY: number): string {
    if (vertices.length === 0) return '';

    let path = '';
    vertices.forEach((vertex, i) => {
      const vx = vertex[0];
      const vy = vertex[1];

      if (i === 0) {
        path += `M ${vx} ${vy}`;
      } else {
        path += ` L ${vx} ${vy}`;
      }
    });
    path += ' Z';
    return path;
  }

  function generateHexagonPath(centerX: number, centerY: number, radius: number): string {
    let path = '';

    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i - Math.PI / 2;
      const vx = centerX + radius * Math.cos(angle);
      const vy = centerY + radius * Math.sin(angle);

      if (i === 0) {
        path += `M ${vx} ${vy}`;
      } else {
        path += ` L ${vx} ${vy}`;
      }
    }
    path += ' Z';
    return path;
  }

  function handleClick() {
    onClick();
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<g on:click={handleClick} class="pad" class:active={isActive}>
  <path
    d={shapePath}
    fill={isActive ? '#54cec2' : color}
    stroke={isActive ? '#6ee0d4' : '#555555'}
    stroke-width="0.05"
  />
  <text
    x={phys_x}
    y={phys_y}
    text-anchor="middle"
    dominant-baseline="middle"
    font-family="monospace"
    font-size="3"
    fill={isActive ? '#ff0' : '#fff'}
  >
    {x},{y}
  </text>
</g>

<style>
  .pad {
    cursor: pointer;
  }

  .pad:hover path {
    stroke: #6ee0d4;
    stroke-width: 0.08;
  }
</style>

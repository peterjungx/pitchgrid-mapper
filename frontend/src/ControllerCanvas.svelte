<script lang="ts">
  import Pad from './Pad.svelte';
  import { onMount } from 'svelte';

  interface PadShape {
    x: number;
    y: number;
    phys_x: number;
    phys_y: number;
    shape: Array<[number, number]>;
    note?: number;
    color?: string;
  }

  export let pads: PadShape[] = [];
  export let deviceName: string = '';
  export let onPadNoteOn: (x: number, y: number) => void = (x, y) => {console.log('Pad note on', x, y);};
  export let onPadNoteOff: (x: number, y: number) => void = (x, y) => {console.log('Pad note off', x, y);};
  export let activeNotes: Set<string> = new Set();

  let containerWidth: number = 800;
  let containerHeight: number = 600;
  let containerElement: HTMLDivElement;

  // Calculate bounds in physical coordinates
  $: phys_xs = pads.map(p => p.phys_x);
  $: phys_ys = pads.map(p => p.phys_y);
  $: min_x = pads.length > 0 ? Math.min(...phys_xs) : 0;
  $: max_x = pads.length > 0 ? Math.max(...phys_xs) : 10;
  $: min_y = pads.length > 0 ? Math.min(...phys_ys) : 0;
  $: max_y = pads.length > 0 ? Math.max(...phys_ys) : 10;


  $: originPad = pads.find(p => p.x === 0 && p.y === 0);
  $: pad_halfheight = (Math.max(...(originPad?.shape.map(v => v[1]) || [0])) - Math.min(...(originPad?.shape.map(v => v[1]) || [0]))) / 2;
  $: pad_halfwidth = (Math.max(...(originPad?.shape.map(v => v[0]) || [0])) - Math.min(...(originPad?.shape.map(v => v[0]) || [0]))) / 2; 
  // Add padding around the controller
  $: padding_x = pad_halfwidth + 2.0;
  $: padding_y = pad_halfheight + 2.0;
  $: viewBox_min_x = min_x - padding_x;
  $: viewBox_min_y = min_y - padding_y;
  $: viewBox_width = (max_x - min_x) + 2 * padding_x;
  $: viewBox_height = (max_y - min_y) + 2 * padding_y;
  $: viewBox = `${viewBox_min_x} ${viewBox_min_y} ${viewBox_width} ${viewBox_height}`;

  onMount(() => {
    // Update container size on window resize
    const updateSize = () => {
      if (containerElement) {
        const rect = containerElement.getBoundingClientRect();
        containerWidth = rect.width;
        containerHeight = rect.height;
      }
    };

    updateSize();
    window.addEventListener('resize', updateSize);

    return () => {
      window.removeEventListener('resize', updateSize);
    };
  });
</script>

<div class="canvas-container" bind:this={containerElement}>

  <svg
    width={containerWidth}
    height={containerHeight}
    {viewBox}
    preserveAspectRatio="xMidYMid meet"
  >
    {#each pads as pad (pad.x + ',' + pad.y)}
      <Pad
        x={pad.x}
        y={pad.y}
        phys_x={pad.phys_x}
        phys_y={pad.phys_y}
        shape={pad.shape}
        color={pad.color}
        isActive={activeNotes.has(`${pad.x},${pad.y}`)}
        onNoteOn={() => onPadNoteOn(pad.x, pad.y)}
        onNoteOff={() => onPadNoteOff(pad.x, pad.y)}
      />
    {/each}
  </svg>
</div>

<style>
  .canvas-container {
    position: relative;
    width: 100%;
    height: 600px;
  }

  svg {
    border-radius: 4px;
    cursor: pointer;
    background-color: #514e4e;
  }

  .device-label {
    top: 1.5em;
    left: 1.5em;
    color: #54cec2;
    font-size: 0.9em;
    pointer-events: none;
  }
</style>

<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ControllerCanvas from './ControllerCanvas.svelte';

  interface Pad {
    x: number;
    y: number;
    phys_x: number;
    phys_y: number;
  }

  interface AppStatus {
    connected_controller: string | null;
    layout_type: string;
    virtual_midi_device: string;
    available_controllers: string[];
    detected_controllers: string[];
    controller_pads: Pad[];
    midi_stats: {
      messages_processed: number;
      notes_remapped: number;
    };
  }

  let ws: WebSocket | null = null;
  let status: AppStatus | null = null;
  let selectedController: string = '';

  // WebSocket connection
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);

      if (data.type === 'init') {
        status = data.status;
      } else if (data.type === 'layout_update') {
        // Handle layout updates
        fetchStatus();
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  async function fetchStatus() {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      console.log('Fetched status:', data);
      status = data;
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  }

  async function connectController(deviceName?: string) {
    const name = deviceName || selectedController;
    if (!name) return;

    try {
      const response = await fetch('/api/controllers/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_name: name }),
      });

      const result = await response.json();
      if (result.success) {
        await fetchStatus();
      }
    } catch (error) {
      console.error('Error connecting controller:', error);
    }
  }

  async function disconnectController() {
    try {
      await fetch('/api/controllers/disconnect', { method: 'POST' });
      await fetchStatus();
    } catch (error) {
      console.error('Error disconnecting controller:', error);
    }
  }

  async function handlePadClick(x: number, y: number) {
    console.log(`Pad clicked: (${x}, ${y})`);
    try {
      const response = await fetch('/api/trigger_note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, velocity: 100 }),
      });
      const result = await response.json();
      if (result.success) {
        console.log(`Triggered note: ${result.note}`);
      } else {
        console.warn('Pad not mapped:', result.error);
      }
    } catch (error) {
      console.error('Error triggering note:', error);
    }
  }

  onMount(() => {
    connectWebSocket();
    fetchStatus();
  });

  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<main>
  <h1>PitchGrid Isomap</h1>

  {#if status}
    <div class="card">
      <h2>Controller Visualization</h2>
      {#if status.controller_pads.length > 0}
        <ControllerCanvas
          pads={status.controller_pads}
          deviceName={status.connected_controller || 'Computer Keyboard'}
          onPadClick={handlePadClick}
        />
      {:else}
        <p>No controller loaded</p>
      {/if}
    </div>

    <div class="card">
      <h2>Controller Connection</h2>

      {#if status.connected_controller && status.connected_controller !== 'Computer Keyboard'}
        <p>Connected to: <strong>{status.connected_controller}</strong></p>
        <button on:click={disconnectController}>Disconnect</button>
      {:else}
        {#if status.detected_controllers.length > 0}
          <p>Detected controllers:</p>
          {#each status.detected_controllers as controller}
            <div class="detected-controller">
              <span>{controller} detected.</span>
              <button on:click={() => connectController(controller)}>Connect</button>
            </div>
          {/each}
        {:else}
          <p>No physical controllers detected.</p>
        {/if}
        <p class="info-text">Using Computer Keyboard layout by default.</p>
      {/if}
    </div>

    <div class="card">
      <h2>Status</h2>
      <p><strong>Virtual MIDI Device:</strong> {status.virtual_midi_device}</p>
      <p><strong>Layout Type:</strong> {status.layout_type}</p>
      <p><strong>Messages Processed:</strong> {status.midi_stats.messages_processed}</p>
      <p><strong>Notes Remapped:</strong> {status.midi_stats.notes_remapped}</p>
    </div>

    <div class="card">
      <h2>Layout Configuration</h2>
      <p>Layout configuration controls will be added here.</p>
      <p>Current layout: <strong>{status.layout_type}</strong></p>
    </div>
  {:else}
    <p>Loading...</p>
  {/if}
</main>

<style>
  main {
    width: 100%;
  }

  h1 {
    color: #646cff;
    margin-bottom: 1em;
  }

  h2 {
    font-size: 1.5em;
    margin-top: 0;
    margin-bottom: 0.5em;
  }

  select {
    padding: 0.5em;
    margin-right: 0.5em;
    border-radius: 4px;
    border: 1px solid #444;
    background-color: #1a1a1a;
    color: #d4d4d4;
    font-size: 1em;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .detected-controller {
    display: flex;
    align-items: center;
    gap: 1em;
    padding: 0.5em 0;
  }

  .detected-controller span {
    flex: 1;
  }

  .info-text {
    margin-top: 1em;
    font-size: 0.9em;
    color: #888;
  }
</style>

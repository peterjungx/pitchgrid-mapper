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
    osc_connected: boolean;
    osc_port: number;
    tuning: {
      depth: number;
      mode: number;
      root_freq: number;
      stretch: number;
      skew: number;
      mode_offset: number;
      steps: number;
      scale_system: string;
      scale_degree_count: number;
    };
    midi_stats: {
      messages_processed: number;
      notes_remapped: number;
    };
  }

  let ws: WebSocket | null = null;
  let status: AppStatus | null = null;
  let selectedController: string = '';

  // Helper to check if controller is detected/available
  function isControllerAvailable(controllerName: string): boolean {
    if (!status) return false;
    if (controllerName === 'Computer Keyboard') return true;
    return status.detected_controllers.includes(controllerName);
  }

  // Handle controller selection from dropdown
  async function handleControllerSelection(event: Event) {
    const target = event.target as HTMLSelectElement;
    const controllerName = target.value;

    if (!controllerName) return;

    selectedController = controllerName;

    // Always switch to the controller configuration to show its layout
    await switchToController(controllerName);

    // If it's a physical controller and it's available, also connect via MIDI
    if (controllerName !== 'Computer Keyboard' && isControllerAvailable(controllerName)) {
      await connectController(controllerName);
    }
  }

  // Switch to a controller configuration (doesn't require MIDI connection)
  async function switchToController(deviceName: string) {
    try {
      const response = await fetch('/api/controllers/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_name: deviceName }),
      });

      const result = await response.json();
      if (result.success) {
        await fetchStatus();
      }
    } catch (error) {
      console.error('Error switching controller:', error);
    }
  }

  // Handle layout type selection
  async function handleLayoutSelection(event: Event) {
    const target = event.target as HTMLSelectElement;
    const layoutType = target.value;

    try {
      const response = await fetch('/api/layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layout_type: layoutType }),
      });

      const result = await response.json();
      if (result.success) {
        console.log('Layout changed to:', layoutType);
      }
    } catch (error) {
      console.error('Error changing layout:', error);
    }
  }

  // Handle transformation toolbar actions
  async function handleTransformation(transformType: string) {
    console.log(`Applying transformation: ${transformType}`);

    // Send transformation via WebSocket if connected
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'apply_transformation',
        transformation: transformType,
      }));
    }
  }

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
      } else if (data.type === 'status_update') {
        // Real-time status update from backend
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

  async function handlePadNoteOn(x: number, y: number) {
    console.log(`Pad note on: (${x}, ${y})`);
    try {
      const response = await fetch('/api/trigger_note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, velocity: 100, note_on: true }),
      });
      const result = await response.json();
      if (result.success) {
        console.log(`Note on: ${result.note}`);
      } else {
        console.warn('Pad not mapped:', result.error);
      }
    } catch (error) {
      console.error('Error triggering note on:', error);
    }
  }

  async function handlePadNoteOff(x: number, y: number) {
    console.log(`Pad note off: (${x}, ${y})`);
    try {
      const response = await fetch('/api/trigger_note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y, velocity: 0, note_on: false }),
      });
      const result = await response.json();
      if (result.success) {
        console.log(`Note off: ${result.note}`);
      } else {
        console.warn('Pad not mapped:', result.error);
      }
    } catch (error) {
      console.error('Error triggering note off:', error);
    }
  }

  onMount(() => {
    connectWebSocket();
    fetchStatus();
  });

  // Update selected controller when status changes
  $: if (status && status.connected_controller) {
    selectedController = status.connected_controller;
  }

  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<main>

  {#if status}
    <div class="card">
      <div class="controller-selector">
        <label for="controller-select">Controller:</label>
        <select
          id="controller-select"
          value={selectedController}
          on:change={handleControllerSelection}
        >
          {#each status.available_controllers as controller}
            {@const available = isControllerAvailable(controller)}
            <option value={controller}>
              {controller}{available ? ' (available)' : ''}
            </option>
          {/each}
        </select>

        <label for="layout-select">Layout:</label>
        <select
          id="layout-select"
          value={status.layout_type}
          on:change={handleLayoutSelection}
        >
          <option value="isomorphic">Isomorphic</option>
          <option value="string_like">String-like</option>
          <option value="piano_like">Piano-like</option>
        </select>

        <div class="connection-indicators">
          {#if status.connected_controller && status.connected_controller !== 'Computer Keyboard'}
            <span class="connected-indicator midi-connected">● MIDI Connected</span>
          {/if}
          <span class="connected-indicator osc-indicator" class:osc-connected={status.osc_connected}>
            ● OSC {status.osc_connected ? 'Connected' : 'Disconnected'} (:{status.osc_port})
          </span>
        </div>
      </div>

      <!-- Transformation Toolbar (only for isomorphic layout) -->
      {#if status.layout_type === 'isomorphic'}
        <div class="transformation-toolbar">
          <div class="toolbar-group">
            <span class="toolbar-label">Shift:</span>
            <button class="toolbar-btn" on:click={() => handleTransformation('shift_left')} title="Shift Left">
              ←
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('shift_right')} title="Shift Right">
              →
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('shift_up')} title="Shift Up">
              ↑
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('shift_down')} title="Shift Down">
              ↓
            </button>
          </div>

          <div class="toolbar-group">
            <span class="toolbar-label">Skew:</span>
            <button class="toolbar-btn" on:click={() => handleTransformation('skew_left')} title="Skew Left">
              ⇤
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('skew_right')} title="Skew Right">
              ⇥
            </button>
          </div>

          <div class="toolbar-group">
            <span class="toolbar-label">Rotate:</span>
            <button class="toolbar-btn" on:click={() => handleTransformation('rotate_left')} title="Rotate Left">
              ↺
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('rotate_right')} title="Rotate Right">
              ↻
            </button>
          </div>

          <div class="toolbar-group">
            <span class="toolbar-label">Reflect:</span>
            <button class="toolbar-btn" on:click={() => handleTransformation('reflect_horizontal')} title="Reflect Horizontal">
              ↔
            </button>
            <button class="toolbar-btn" on:click={() => handleTransformation('reflect_vertical')} title="Reflect Vertical">
              ↕
            </button>
          </div>
        </div>
      {/if}

      {#if status.controller_pads.length > 0}
        <ControllerCanvas
          pads={status.controller_pads}
          deviceName={status.connected_controller || 'Computer Keyboard'}
          onPadNoteOn={handlePadNoteOn}
          onPadNoteOff={handlePadNoteOff}
        />
      {:else}
        <p>No controller loaded</p>
      {/if}
    </div>

    <div class="card">
      <h2>Status</h2>
      <p><strong>Virtual MIDI Device:</strong> {status.virtual_midi_device}</p>
      <p><strong>Scale System:</strong> {status.tuning.scale_system}</p>
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

  h2 {
    font-size: 1.5em;
    margin-top: 0;
    margin-bottom: 0.5em;
  }

  .controller-selector {
    display: flex;
    align-items: center;
    gap: 1em;
    margin-bottom: 1em;
    flex-wrap: wrap;
  }

  .controller-selector label {
    font-weight: 500;
  }

  select {
    padding: 0.5em;
    border-radius: 4px;
    border: 1px solid #444;
    background-color: #1a1a1a;
    color: #d4d4d4;
    font-size: 1em;
    min-width: 200px;
  }

  .connection-indicators {
    display: flex;
    gap: 1em;
    align-items: center;
  }

  .connected-indicator {
    font-size: 0.85em;
    padding: 0.25em 0.5em;
    border-radius: 4px;
  }

  .midi-connected {
    color: #54cec2;
    background-color: rgba(84, 206, 194, 0.1);
  }

  .osc-indicator {
    color: #888;
    background-color: rgba(136, 136, 136, 0.1);
  }

  .osc-indicator.osc-connected {
    color: #54cec2;
    background-color: rgba(84, 206, 194, 0.1);
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

  .transformation-toolbar {
    display: flex;
    gap: 1.5em;
    align-items: center;
    padding: 1em;
    background-color: rgba(84, 206, 194, 0.05);
    border-radius: 4px;
    margin-bottom: 1em;
    flex-wrap: wrap;
  }

  .toolbar-group {
    display: flex;
    gap: 0.5em;
    align-items: center;
  }

  .toolbar-label {
    font-size: 0.9em;
    font-weight: 500;
    color: #54cec2;
  }

  .toolbar-btn {
    padding: 0.5em 0.75em;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #1a1a1a;
    color: #d4d4d4;
    font-size: 1.2em;
    cursor: pointer;
    transition: all 0.2s;
    min-width: 2.5em;
  }

  .toolbar-btn:hover {
    background-color: #2a2a2a;
    border-color: #54cec2;
    color: #54cec2;
  }

  .toolbar-btn:active {
    transform: scale(0.95);
    background-color: rgba(84, 206, 194, 0.2);
  }
</style>

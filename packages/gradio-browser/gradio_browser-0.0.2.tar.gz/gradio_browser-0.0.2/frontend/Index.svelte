<script lang="ts">
  import { Block } from "@gradio/atoms";
  import { BaseButton } from "@gradio/button";
  import type { LoadingStatus } from "@gradio/statustracker";
  import { StatusTracker } from "@gradio/statustracker";
  import type { Gradio } from "@gradio/utils";
  import { onMount } from "svelte";

  export let gradio: Gradio<{
    change: string;
    input: string;
    submit: string;
  }>;

  export let value = "https://example.com";
  export let show_hostname = false;
  export let elem_id = "";
  export let elem_classes: string[] = [];
  export let scale: number | null = null;
  export let min_width: number | undefined = undefined;
  export let loading_status: LoadingStatus | undefined = undefined;
  export let mode: "static" | "interactive";
  export let min_height = "500px";

  let browserId: string;
  let hostBase: string;
  let initialPath: string;
  let pathInput: HTMLInputElement;
  let iframe: HTMLIFrameElement;
  let history: string[] = [];
  let historyIndex = -1;

  function parseUrl(url: string) {
    try {
      const parsed = new URL(url);
      hostBase = `${parsed.protocol}//${parsed.host}`;
      initialPath = parsed.pathname || "/";
    } catch {
      hostBase = "https://example.com";
      initialPath = "/";
    }
  }

  function addToHistory(url: string) {
    // Remove any forward history when navigating to new page
    if (historyIndex < history.length - 1) {
      history = history.slice(0, historyIndex + 1);
    }

    // Add new URL to history
    history = [...history, url];
    historyIndex = history.length - 1;
  }

  function navigate() {
    if (!pathInput || !iframe) return;

    let fullUrl: string;

    if (show_hostname) {
      // Full URL mode - use input as complete URL
      fullUrl = pathInput.value.trim() || value;
      if (!fullUrl.startsWith("http")) {
        fullUrl = "https://" + fullUrl;
      }
    } else {
      // Path only mode - combine with hostBase
      let path = pathInput.value.trim() || "/";
      if (!path.startsWith("/")) path = "/" + path;
      fullUrl = hostBase + path;
    }

    iframe.src = fullUrl;
    addToHistory(fullUrl);
    updateAddressBar(fullUrl);

    if (mode === "interactive") {
      gradio.dispatch("change", fullUrl);
    }
  }

  function goBack() {
    if (historyIndex > 0) {
      historyIndex--;
      const url = history[historyIndex];
      iframe.src = url;
      updateAddressBar(url);

      if (mode === "interactive") {
        gradio.dispatch("change", url);
      }
    }
  }

  function goForward() {
    if (historyIndex < history.length - 1) {
      historyIndex++;
      const url = history[historyIndex];
      iframe.src = url;
      updateAddressBar(url);

      if (mode === "interactive") {
        gradio.dispatch("change", url);
      }
    }
  }

  function updateAddressBar(url: string) {
    if (!pathInput) return;

    if (show_hostname) {
      pathInput.value = url;
    } else {
      try {
        const parsed = new URL(url);
        pathInput.value = parsed.pathname;
      } catch {
        pathInput.value = "/";
      }
    }
  }

  function refresh() {
    if (!iframe) return;

    const currentSrc = iframe.src.split("?")[0];
    iframe.src = currentSrc + "?t=" + Date.now();
  }

  function handleKeyPress(e: KeyboardEvent) {
    if (e.key === "Enter") {
      navigate();
    }
  }

  function openInNewTab() {
    if (!iframe) return;

    const currentUrl = iframe.src;
    window.open(currentUrl, "_blank");
  }

  onMount(() => {
    browserId = `browser_${
      Math.abs(
        value.split("").reduce((a, b) => {
          a = (a << 5) - a + b.charCodeAt(0);
          return a & a;
        }, 0)
      ) % 10000
    }`;

    parseUrl(value);
    addToHistory(value);
  });

  $: {
    if (value) {
      parseUrl(value);
    }
  }
</script>

<Block
  visible={true}
  {elem_id}
  {elem_classes}
  {scale}
  {min_width}
  allow_overflow={false}
  padding={false}
  height="100%"
>
  {#if loading_status}
    <StatusTracker
      autoscroll={gradio.autoscroll}
      i18n={gradio.i18n}
      {...loading_status}
    />
  {/if}

  <div class="browser-container" style="min-height: {min_height}">
    <!-- Browser Header -->
    <div class="browser-header">
      <!-- Traffic Lights -->
      <div class="traffic-lights">
        <div class="light red"></div>
        <div class="light yellow"></div>
        <div class="light green"></div>
      </div>

      <!-- Navigation Buttons -->
      <div class="nav-buttons">
        <BaseButton
          variant="secondary"
          size="sm"
          on:click={goBack}
          disabled={historyIndex <= 0}>←</BaseButton
        >
        <BaseButton
          variant="secondary"
          size="sm"
          on:click={goForward}
          disabled={historyIndex >= history.length - 1}>→</BaseButton
        >
        <BaseButton variant="secondary" size="sm" on:click={refresh}
          >↻</BaseButton
        >
      </div>

      <!-- Address Bar -->
      <input
        bind:this={pathInput}
        type="text"
        value={show_hostname ? value : initialPath}
        placeholder={show_hostname
          ? "https://example.com/path"
          : "/api/endpoint"}
        class="address-bar"
        on:keypress={handleKeyPress}
        disabled={mode === "static"}
      />

      <BaseButton variant="secondary" size="sm" on:click={openInNewTab}
        >↗</BaseButton
      >
    </div>
    <!-- Content Frame -->
    <iframe
      bind:this={iframe}
      src={value}
      class="browser-iframe"
      title="Browser content"
    ></iframe>
  </div>
</Block>

<style>
  .browser-container {
    width: 100%;
    height: 100% !important;
    display: flex;
    flex-direction: column;
    background: var(--background-fill-secondary);
    font-family: -apple-system, BlinkMacSystemFont, "Segue UI", Roboto,
      sans-serif;
  }

  .browser-header {
    height: 50px;
    flex-shrink: 0;
    background: var(--background-fill-secondary);
    display: flex;
    align-items: center;
    color: var(--body-text-color);
    padding: 0 16px;
    gap: 12px;
    border-bottom: 1px solid var(--border-color-primary);
  }

  .traffic-lights {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .light.red {
    background: #ff5f56;
  }
  .light.yellow {
    background: #ffbd2e;
  }
  .light.green {
    background: #27ca3f;
  }

  .nav-buttons {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .address-bar {
    flex: 1;
    border: none;
    outline: none;
    height: 32px;
    padding: var(--input-padding);
    font-size: 14px;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas,
      "Liberation Mono", Menlo, monospace;
    background: var(--input-background-fill);
    color: var(--body-text-color);
    min-width: 0;
    border: var(--input-border-width) solid var(--input-border-color);
    border-radius: var(--block-radius);
    margin: 0;
  }

  .address-bar:focus {
    box-shadow: 0 0 0 1px var(--input-border-color-focus);
  }

  .browser-iframe {
    width: 100%;
    height: 100%;
    flex: 1;
    border: none;
    background: white;
  }
</style>

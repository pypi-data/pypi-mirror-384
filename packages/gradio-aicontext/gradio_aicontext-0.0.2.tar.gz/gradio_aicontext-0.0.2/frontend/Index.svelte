<svelte:options accessors={true} />

<script lang="ts">
  import { Block } from "@gradio/atoms";
  import type { LoadingStatus } from "@gradio/statustracker";
  import { StatusTracker } from "@gradio/statustracker";
  import type { Gradio } from "@gradio/utils";
  import Bar from "./Bar.svelte";

  export let gradio: Gradio<{
    change: never;
    submit: never;
    input: never;
    clear_status: LoadingStatus;
  }>;
  export let elem_id = "";
  export let elem_classes: string[] = [];
  export let visible: boolean | "hidden" = true;
  export let value: any = null;
  export let scale: number | null = null;
  export let min_width: number | undefined = undefined;
  export let loading_status: LoadingStatus | undefined = undefined;
  export let interactive: boolean = false;
  export let min_height = "500px";

  $: messages = value?.messages || [];
  $: tokens = value?.tokens_count || [];
  $: totalTokens = tokens.reduce((sum: number, t: number) => sum + t, 0);
  $: heights = tokens.map((count: number) =>
    Math.min(Math.max(20, count * 0.2), 400)
  );

  function handle_change(): void {
    gradio.dispatch("change");
  }

  $: value, handle_change();
</script>

<Block
  {visible}
  {elem_id}
  {elem_classes}
  {scale}
  {min_width}
  allow_overflow={false}
  padding={false}
>
  {#if loading_status}
    <StatusTracker
      autoscroll={gradio.autoscroll}
      i18n={gradio.i18n}
      {...loading_status}
      on:clear_status={() => gradio.dispatch("clear_status", loading_status)}
    />
  {/if}

  <div class="context-container">
    {#if messages.length === 0}
      <div class="empty-state">No messages yet, start chatting!</div>
    {:else}
      <div class="header">
        <h4 class="title">📚 Context Stack</h4>
        <span class="count-badge">{messages.length}</span>
        <span class="token-count">{totalTokens} tokens</span>
      </div>
      <div class="bars-container">
        {#each messages as message, i}
          <Bar
            role={message.role || "unknown"}
            type={message.type || ""}
            name={message.name || ""}
            tokens={tokens[i]}
            height={heights[i]}
          />
        {/each}
      </div>
    {/if}
  </div>
</Block>

<style>
  .context-container {
    width: 100%;
    height: 100% !important;
    display: flex;
    flex-direction: column;
    border-radius: var(--block-radius);
    box-shadow: var(--shadow-drop);
  }

  .empty-state {
    height: 100%;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--neutral-500);
    font-size: 14px;
    background: var(--background-fill-primary);
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 40px;
  }

  .header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 16px 16px 12px 16px;
    border-bottom: 1px solid var(--border-color-primary);
    flex-wrap: wrap;
    flex-shrink: 0;
  }

  .title {
    margin: 0;
    color: var(--body-text-color);
    font-size: 14px;
    font-weight: 600;
  }

  .count-badge {
    background: var(--color-accent);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 600;
  }

  .token-count {
    margin: 0;
    color: var(--body-text-color);
    font-size: 12px;
    font-weight: 400;
  }

  .bars-container {
    flex: 1;
    overflow-y: auto;
    padding: 0 16px 16px 16px;
    min-height: 0;
  }
</style>

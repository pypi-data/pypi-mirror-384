<script lang="ts">
    export let role: string;
    export let type: string = "";
    export let name: string = "";
    export let tokens: number;
    export let height: number;

    const colors: Record<string, string> = {
        "system": "#BEF1FE",
        "user": "#CFFFD9", 
        "assistant": "#FEFEB1",
        "function_call": "#E9D8FF",
        "function_result": "#E9D8FF"
    };

    $: color = type === "function_call" ? colors["function_call"] :
               type === "function_call_output" ? colors["function_result"] :
               role === "system" ? colors["system"] :
               role === "user" ? colors["user"] :
               colors["assistant"];

    $: displayType = type === "function_call" ? name || "unknown" :
                     type === "function_call_output" ? "result" :
                     role;

    let hovered = false;
</script>

<div 
    class="bar"
    style:background={color}
    style:height="{height}px"
    style:border="1px solid {color}44"
    style:transform={hovered ? "scale(1.02)" : "scale(1)"}
    on:mouseenter={() => hovered = true}
    on:mouseleave={() => hovered = false}
>
    <div class="content">
        {#if type === "function_call"}
            <pre class="func-name">{displayType}</pre>
        {:else}
            <div class="type">{displayType}</div>
        {/if}
        <div class="tokens">/ {tokens} tokens</div>
    </div>
</div>

<style>
    .bar {
        width: 100%;
        margin: 8px 0;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 600;
        transition: all 0.2s ease;
        cursor: default;
    }

    .content {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        line-height: 1.2;
    }

    .type {
        font-size: 12px;
        font-weight: 700;
        color: black;
    }

    .func-name {
        color: black;
        font-size: 10px;
        margin: 0;
    }

    .tokens {
        font-size: 10px;
        opacity: 0.9;
        font-weight: 500;
        color: black;
    }
</style>
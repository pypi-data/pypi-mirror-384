<script lang="ts">
    import { type FileData } from "@gradio/client";
    import { Image } from "@gradio/image/shared";
    import { onMount, tick } from "svelte";

    export let elem_id = "";
    export let elem_classes: string[] = [];
    export let visible: boolean | "hidden" = true;
    export let variant: "primary" | "secondary" | "stop" | "huggingface" = "secondary";
    export let size: "sm" | "md" | "lg" = "lg";
    export let value: string | null = null;
    export let link: string | null = null;
    export let icon: FileData | null = null;
    export let disabled = false;
    export let scale: number | null = null;
    export let min_width: number | undefined = undefined;
    export let help: string | undefined = undefined;

    let show_tooltip = false;
    let tooltip_element: HTMLSpanElement;
    let button_element: HTMLButtonElement | HTMLAnchorElement;

    function position_tooltip() {
        if (!tooltip_element || !button_element) return;
        const button_rect = button_element.getBoundingClientRect();
		const tooltip_rect = tooltip_element.getBoundingClientRect();        
        tooltip_element.style.position = "fixed";
        // Center horizontally below the button
        tooltip_element.style.left = `${button_rect.left + (button_rect.width - tooltip_rect.width) / 2}px`;
        // Position below the button with an 8px offset
        tooltip_element.style.top = `${button_rect.bottom + 8}px`;
    }

    function portal(node: HTMLElement) {
        document.body.appendChild(node);
        return {
            destroy() {
                if (node.parentNode) {
                    node.parentNode.removeChild(node);
                }
            }
        };
    }

    function handle_show_tooltip() {
        show_tooltip = true;
        // Wait for tooltip to render before positioning
        tick().then(() => {
            position_tooltip();
            // Force reposition on next frame to ensure correct dimensions
            requestAnimationFrame(position_tooltip);
        });
    }

    // Update tooltip position on window resize
    onMount(() => {
        const handle_resize = () => {
            if (show_tooltip) {
                tick().then(position_tooltip);
            }
        };
        window.addEventListener("resize", handle_resize);
        return () => window.removeEventListener("resize", handle_resize);
    });
</script>

{#if link && link.length > 0}
    <a
        href={link}
        rel="noopener noreferrer"
        class:hidden={visible === false || visible === "hidden"}
        class:disabled
        aria-disabled={disabled}
        class="{size} {variant} {elem_classes.join(' ')}"
        style:flex-grow={scale}
        style:pointer-events={disabled ? "none" : null}
        style:width={scale === 0 ? "fit-content" : null}
        style:min-width={typeof min_width === "number" ? `calc(min(${min_width}px, 100%))` : null}
        id={elem_id}
        bind:this={button_element}
        on:mouseenter={help ? handle_show_tooltip : null}
        on:mouseleave={help ? () => show_tooltip = false : null}
        on:focusin={help ? handle_show_tooltip : null}
        on:focusout={help ? () => show_tooltip = false : null}
    >
        {#if icon}
            <Image class="button-icon" src={icon.url} alt={`${value} icon`} />
        {/if}
        <span class="button-content">
            {#if value}
                {value}
            {:else}
                <slot />
            {/if}
        </span>
        {#if show_tooltip && help}
            <span class="tooltip-text" bind:this={tooltip_element} use:portal>
                {help}
            </span>
        {/if}
    </a>
{:else}
    <button
        on:click
        class:hidden={visible === false || visible === "hidden"}
        class="{size} {variant} {elem_classes.join(' ')}"
        style:flex-grow={scale}
        style:width={scale === 0 ? "fit-content" : null}
        style:min-width={typeof min_width === "number" ? `calc(min(${min_width}px, 100%))` : null}
        id={elem_id}
        {disabled}
        bind:this={button_element}
        on:mouseenter={help ? handle_show_tooltip : null}
        on:mouseleave={help ? () => show_tooltip = false : null}
        on:focusin={help ? handle_show_tooltip : null}
        on:focusout={help ? () => show_tooltip = false : null}
    >
        {#if icon}
            <Image
                class={`button-icon ${value ? "right-padded" : ""}`}
                src={icon.url}
                alt={`${value} icon`}
            />
        {/if}
        <span class="button-content">
            {#if value}
                {value}
            {:else}
                <slot />
            {/if}
        </span>
        {#if show_tooltip && help}
            <span class="tooltip-text" bind:this={tooltip_element} use:portal>
                {help}
            </span>
        {/if}
    </button>
{/if}

<style>
    button,
    a {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        transition: var(--button-transition);
        padding: var(--size-0-5) var(--size-2);
        text-align: center;
        position: relative;
    }

    button:hover {
        transform: var(--button-transform-hover);
    }

    button:active,
    a:active {
        transform: var(--button-transform-active);
    }

    button[disabled],
    a.disabled {
        opacity: 0.5;
        filter: grayscale(30%);
        cursor: not-allowed;
        transform: none;
    }

    .hidden {
        display: none;
    }

    .primary {
        border: var(--button-border-width) solid var(--button-primary-border-color);
        background: var(--button-primary-background-fill);
        color: var(--button-primary-text-color);
        box-shadow: var(--button-primary-shadow);
    }
    .primary:hover,
    .primary[disabled] {
        background: var(--button-primary-background-fill-hover);
        color: var(--button-primary-text-color-hover);
    }

    .primary:hover {
        border-color: var(--button-primary-border-color-hover);
        box-shadow: var(--button-primary-shadow-hover);
    }
    .primary:active {
        box-shadow: var(--button-primary-shadow-active);
    }

    .primary[disabled] {
        border-color: var(--button-primary-border-color);
    }

    .secondary {
        border: var(--button-border-width) solid var(--button-secondary-border-color);
        background: var(--button-secondary-background-fill);
        color: var(--button-secondary-text-color);
        box-shadow: var(--button-secondary-shadow);
    }

    .secondary:hover,
    .secondary[disabled] {
        background: var(--button-secondary-background-fill-hover);
        color: var(--button-secondary-text-color-hover);
    }

    .secondary:hover {
        border-color: var(--button-secondary-border-color-hover);
        box-shadow: var(--button-secondary-shadow-hover);
    }
    .secondary:active {
        box-shadow: var(--button-secondary-shadow-active);
    }

    .secondary[disabled] {
        border-color: var(--button-secondary-border-color);
    }

    .stop {
        background: var(--button-cancel-background-fill);
        color: var(--button-cancel-text-color);
        border: var(--button-border-width) solid var(--button-cancel-border-color);
        box-shadow: var(--button-cancel-shadow);
    }

    .stop:hover,
    .stop[disabled] {
        background: var(--button-cancel-background-fill-hover);
    }

    .stop:hover {
        border-color: var(--button-cancel-border-color-hover);
        box-shadow: var(--button-cancel-shadow-hover);
    }
    .stop:active {
        box-shadow: var(--button-cancel-shadow-active);
    }

    .stop[disabled] {
        border-color: var(--button-cancel-border-color);
    }

    .sm {
        border-radius: var(--button-small-radius);
        padding: var(--button-small-padding);
        font-weight: var(--button-small-text-weight);
        font-size: var(--button-small-text-size);
    }

    .md {
        border-radius: var(--button-medium-radius);
        padding: var(--button-medium-padding);
        font-weight: var(--button-medium-text-weight);
        font-size: var(--button-medium-text-size);
    }

    .lg {
        border-radius: var(--button-large-radius);
        padding: var(--button-large-padding);
        font-weight: var(--button-large-text-weight);
        font-size: var(--button-large-text-size);
    }

    :global(.button-icon) {
        width: var(--text-xl);
        height: var(--text-xl);
    }
    :global(.button-icon.right-padded) {
        margin-right: var(--spacing-md);
    }

    .huggingface {
        background: rgb(20, 28, 46);
        color: white;
    }

    .huggingface:hover {
        background: rgb(40, 48, 66);
        color: white;
    }

    .button-content {
        display: inline;
        visibility: visible;
        color: inherit;
    }

    .tooltip-text {
        width: auto;
        max-width: 500px;
        background-color: var(--body-text-color);
        color: var(--background-fill-primary);
        text-align: center;
        border-radius: var(--radius-md);
        padding: var(--spacing-md);
        z-index: var(--layer-top);
        opacity: 1;
        transition: opacity 0.2s;
        pointer-events: none;
        font-weight: var(--body-text-weight);
        font-size: var(--body-text-size);
    }
</style>
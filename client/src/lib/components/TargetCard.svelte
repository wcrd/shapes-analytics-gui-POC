<script>
// @ts-nocheck

    import { createEventDispatcher } from "svelte";
    export let target;

    const dispatch = createEventDispatcher()

    function handleClick(){
        console.debug("Card clicked")
        dispatch('targetClick', { target })    
    }

</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div class="p-1 border-2 border-solid rounded-lg border-emerald-500 hover:bg-blue-200 cursor-pointer bg-white" on:click={handleClick} >
    <h6 class="text-sm font-semibold italic">Target:</h6>
    <p class="text-xs">{target}</p>
</div>
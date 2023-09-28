<script>
    import { createEventDispatcher } from "svelte";
    export let module;

    const dispatch = createEventDispatcher()

    function handleClick(){
        console.debug("Card clicked")
        dispatch('moduleClick', { module })    
    }

</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="p-1 border-4 border-solid rounded-lg border-blue-400 hover:bg-blue-200 cursor-pointer bg-white" on:click={handleClick} >
    <h6 class="font-semibold">{module.name.replaceAll("_", " ")}</h6>
    <hr class="my-1">
    <p class="font-semibold text-sm italic mb-1">Options:</p>
    <div class="flex flex-col gap-y-2 text-sm ml-2">
        {#each module.options as option }
        <div class="border border-blue-600 rounded-lg p-1 bg-slate-100">
            {option.name.replaceAll("_", " ")}
        </div>
        {/each}
    </div>
    <hr class="my-1">
    <h6 class="text-xs font-semibold italic">Module ID:</h6>
    <p class="text-xs text-slate-400">{module.uuid}</p>
</div>
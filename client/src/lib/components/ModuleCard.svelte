<script>
    import { createEventDispatcher } from "svelte";
    export let module;

    const dispatch = createEventDispatcher()

    function handleClick(){
        console.debug("Card clicked")
        dispatch('moduleClick', { module })    
    }

</script>

<div class="p-1 border-4 border-solid rounded-lg border-blue-400 hover:bg-blue-200 cursor-pointer bg-white" on:click={handleClick} >
    <h6 class="font-semibold">{module.name.replaceAll("_", " ")}</h6>
    <hr>
    <p class="font-semibold text-sm italic mb-1">Options:</p>
    <div class="flex flex-col gap-y-2 text-sm ml-2">
        {#each module.options as option }
        <div class="border border-blue-600 rounded-lg p-1 bg-slate-100">
            {option.name.replaceAll("_", " ")}
        </div>
        {/each}
    </div>
</div>
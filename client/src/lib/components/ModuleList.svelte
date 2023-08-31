<script>
	import ModuleCard from "./ModuleCard.svelte";
    import { selected_module, selected_match, matches, diagram } from "$lib/stores/state";


    export let modules;

    function handleClick(event){
        // set module
        selected_module.set(event.detail.module.uuid);
        // reset match selection
        selected_match.set(null);
        // reset matches
        matches.set([])
        // reset diagram
        diagram.set({})
    }
</script>

<div class="flex flex-col w-100 overflow-x-hidden gap-y-4 m-2 overflow-y-scroll h-100">
    {#each modules as module}
        <ModuleCard {module} on:moduleClick={handleClick} />
    {/each}
</div>
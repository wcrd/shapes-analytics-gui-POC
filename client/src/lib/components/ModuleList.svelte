<script>
	import ModuleCard from "./ModuleCard.svelte";
    import { state } from "$lib/stores/state";


    export let modules = [];

    function handleClick(event){
        state.update(v => {
            // set module
            v.selected_module = event.detail.module.uuid;
            // reset match selection
            v.selected_match = null;
            // reset matches
            v.matches = []
            return v
        })
    }
</script>

<div class="flex flex-col w-100 overflow-x-hidden gap-y-2 m-2 overflow-y-scroll h-100">
    {#each modules as module}
        <ModuleCard {module} on:moduleClick={handleClick} />
    {/each}
</div>
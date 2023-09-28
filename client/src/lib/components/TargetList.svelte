<script>
	import TargetCard from "./TargetCard.svelte";
    import { selected_target, selected_match, diagram } from "$lib/stores/state";


    export let targets;

    function handleClick(event){
        // console.debug(event.detail)
        selected_target.set(event.detail.target)
        // clear downstream
        // reset matches
        selected_match.set(null)
        // reset diagram
        diagram.set({})
    }
</script>

<div class="flex flex-col w-full overflow-x-hidden gap-y-2 m-2 overflow-y-scroll h-100">
    {#each targets as target}
        <TargetCard {target} on:targetClick={handleClick} />
    {/each}
</div>
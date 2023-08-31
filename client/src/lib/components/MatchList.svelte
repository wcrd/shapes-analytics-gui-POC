<script>
	import MatchCard from "./MatchCard.svelte";
    import { selected_match } from "$lib/stores/state";


    export let matches;

    function handleClick(event){
        // console.debug(event.detail)
        selected_match.set(event.detail.match)
    }
</script>

<div class="flex flex-col w-full overflow-x-hidden gap-y-2 m-2 overflow-y-scroll h-100">
    {#each matches as match}
        <MatchCard {match} on:matchClick={handleClick} />
    {/each}
</div>
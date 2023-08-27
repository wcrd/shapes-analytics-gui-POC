<script>
    import { createEventDispatcher } from "svelte";
    export let match;

    const dispatch = createEventDispatcher()

    function handleClick(){
        console.debug("Card clicked")
        dispatch('matchClick', { match })    
    }

</script>

<div class="p-1 border-2 border-solid rounded-lg border-blue-400 hover:bg-blue-200 cursor-pointer" on:click={handleClick} >
    <h6 class="font-semibold text-sm">{match['?target']}</h6>
</div>
<script>
    import { createEventDispatcher } from "svelte";
    export let match;

    const dispatch = createEventDispatcher()

    function handleClick(){
        console.debug("Card clicked")
        dispatch('matchClick', { match })    
    }

</script>

<div class="p-1 border-2 border-solid rounded-lg border-emerald-500 hover:bg-blue-200 cursor-pointer bg-white" on:click={handleClick} >
    <h6 class="text-sm font-semibold italic">Target:</h6>
    <p class="text-xs">{match['?target']}</p>
    <hr class="my-1">
    <h6 class="text-xs font-semibold italic">Logic Option:</h6>
    <div class="border rounded-md border-blue-500 bg-slate-100 my-1 p-1 text-xs">
        <p>{match['_logic_name']}</p>
        <p class="text-slate-400"><span class="font-semibold italic">id: </span><span>{match['_logic']}</span></p>
    </div>
    <hr class="my-1">
    <h6 class="text-xs font-semibold italic">Match ID:</h6>
    <p class="text-xs text-slate-400">{match['_match_id']}</p>


</div>
<script>
    import { onMount } from 'svelte';

    import ModuleList from '$lib/components/ModuleList.svelte';
    import { state } from '$lib/stores/state';
	import MatchList from '$lib/components/MatchList.svelte';
    import GraphContainer from '$lib/components/GraphContainer.svelte';

    const API_ADDR = "http://localhost:8080"

    let matches = []
    let diagram = {}

    $: module_uuid = $state.selected_module
    $: getMatches(module_uuid).then(x => matches=x.data)
    $: selected_match = $state.selected_match
    $: getDiagram(selected_match).then(x => diagram = x.data)

    // $: diagram

    onMount(async ()=>{
        // fetch module list
        const r = await fetch(`${API_ADDR}/get-modules`).then(x => x.json()) 
        $state.modules = r.data
    })

    async function getMatches(module_uuid){
        if(module_uuid==null){ return {}}

        const r = await fetch(`${API_ADDR}/get-module-matches`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                module_uuid: module_uuid,
                force_rematch: false
            })
        }).then(x => x.json())

        return r
    }

    async function getDiagram(match){
        if(match==null || Object.keys(match).length == 0){ return {}}

        const r = await fetch(`${API_ADDR}/get-match-diagram`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                match: match,
                force_regen: false
            })
        }).then(x => x.json())

        return r
    }

</script>

<div class="flex flex-col h-full w-screen bg-slate-100">
    <div class="flex flex-col h-full">
        <header class="h-8 border-solid border-b border-slate-400">
            Header Bar
        </header>
        <div class="flex flex-row h-full">
            <div class="flex w-1/6 h-full">
                <ModuleList modules={$state.modules} on:click={e => console.debug("Received")} />
            </div>
            <div class="flex w-1/6 h-full">
                <MatchList {matches} />
            </div>
            <div class="flex w-2/3 h-full overflow-hidden">
                <!-- <TidyTree data={diagram} /> -->
                <GraphContainer bind:data={diagram} />

            </div>
        </div>
    </div>
</div>
<script>
    import { onMount } from 'svelte';

    import ModuleList from '$lib/components/ModuleList.svelte';
    import { selected_module, selected_target, selected_match, modules, targets, matches, filteredMatches, diagram } from '$lib/stores/state';
	import MatchList from '$lib/components/MatchList.svelte';
    import GraphContainer from '$lib/components/GraphContainer.svelte';
    import TargetList from '$lib/components/TargetList.svelte';

    const API_ADDR = "http://localhost:8080"


    $: $selected_module && getMatches($selected_module).then(x => { $matches = x.data.matches; $targets = x.data.targets }), console.debug("Getting matches...")
    $: $selected_match && getDiagram($selected_match).then(x => $diagram = x.data), console.debug("Getting diagram...")
    // $: console.debug("diagram = ", $diagram)

    onMount(async ()=>{
        // fetch module list
        const r = await fetch(`${API_ADDR}/get-modules`).then(x => x.json()) 
        $modules = r.data
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
            <div class="flex flex-row text-sm items-center h-full px-2">
                {#if $selected_module}
                <p>{`${$selected_module}`}</p>
                    {#if $selected_target}
                    <p><span class="px-2 font-bold">></span>{`${$selected_target}`}</p>
                    {#if $selected_match}
                        <p><span class="px-2 font-bold">></span>{`${$selected_match._logic_name}`}</p>
                    {/if}
                    {/if}
                {/if}
            </div>
        </header>
        <div class="flex flex-row h-full">
            <div class="flex w-1/6 h-full">
                <ModuleList modules={$modules} />
            </div>
            <div class="flex w-1/6 h-full">
                <TargetList targets={$targets || []}/>
            </div>
            <div class="flex w-1/6 h-full">
                <MatchList matches={$filteredMatches || []} />
            </div>
            <div class="flex w-1/2 h-full">
                <!-- <TidyTree data={diagram} /> -->
                <GraphContainer data={$diagram} />

            </div>
        </div>
    </div>
</div>
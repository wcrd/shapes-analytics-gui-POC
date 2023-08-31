<script>
    import SvelteTidyTree from '$lib/components/SvelteTidyTree.svelte';

    export let data = {};

    // $: console.debug("GraphContainer got new data: ", data)

</script>

<div class="flex flex-col h-full w-full overflow-scroll">
    <SvelteTidyTree {data} />
</div>
<script>
    import SvelteTidyTree from '$lib/components/SvelteTidyTree.svelte';

    export let data = {};

    // $: console.debug("GraphContainer got new data: ", data)

</script>

<div class="h-full w-full overflow-scroll w-full">
    <SvelteTidyTree {data} />
</div>
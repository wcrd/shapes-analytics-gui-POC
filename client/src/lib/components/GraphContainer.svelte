<script>
    import SvelteTidyTree from '$lib/components/SvelteTidyTree.svelte';

    export let data;

</script>

<div class="h-full w-full overflow-scroll w-full">
    <SvelteTidyTree bind:data={data} />
</div>
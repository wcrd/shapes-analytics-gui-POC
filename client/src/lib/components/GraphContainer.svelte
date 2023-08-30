<script>
    import TidyTree from '$lib/components/TidyTree.svelte';

    export let data

</script>

<div class="h-full w-full overflow-scroll w-full">
    <TidyTree {data} />
</div>
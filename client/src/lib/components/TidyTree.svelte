<script>
	import * as d3 from 'd3';
	import { onMount } from 'svelte';

	export let data;

	let el;

	$: el && data && generateSVG(data)

	console.debug(generateSVG)

	// onMount(() => {
	function generateSVG() {
		d3.select('svg').remove()

		// Compute the tree height; this approach will allow the height of the
		// SVG to scale according to the breadth (width) of the tree layout.
		const width = 928;
		const root = d3.hierarchy(data);
		const dx = 10;
		const dy = width / (root.height + 1);

		// Create a tree layout.
		const tree = d3.tree().nodeSize([dx, dy]);

		// Sort the tree and apply the layout.
		root.sort((a, b) => d3.ascending(a.data.type, b.data.type));
		tree(root);


		// Compute the extent of the tree. Note that x and y are swapped here
		// because in the tree layout, x is the breadth, but when displayed, the
		// tree extends right rather than down.
		let x0 = Infinity;
		let x1 = -x0;
		root.each((d) => {
			if (d.x > x1) x1 = d.x;
			if (d.x < x0) x0 = d.x;
		});

		// Compute the adjusted height of the tree.
		const height = x1 - x0 + dx * 2


		

		const svg = d3
            .select(el)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [-dy / 3, x0 - dx, width, height])
			.attr('style', 'max-width: 100%; height: auto; font: 10px sans-serif;');

		const link = svg
			.append('g')
			.attr('fill', 'none')
			.attr('stroke', '#555')
			.attr('stroke-opacity', 0.4)
			.attr('stroke-width', 1.5)
			.selectAll()
			.data(root.links())
			.join('path')
			.attr(
				'd',
				d3
					.linkHorizontal()
					.x((d) => d.y)
					.y((d) => d.x)
			);
        
        link
            .attr('stroke', d => {
                switch(d.target.data.rel) {
                    case 'hasPoint':
                        return 'green'
                    case 'hasPart':
                        return 'blue'
                    case 'feeds':
                        return 'orange'
                    default:
                        return '#555'
                }
            })

		const node = svg
			.append('g')
			.attr('stroke-linejoin', 'round')
			.attr('stroke-width', 3)
			.selectAll()
			.data(root.descendants())
			.join('g')
			.attr('transform', (d) => `translate(${d.y},${d.x})`);

		node
            .filter(d => d.data.type == 'point')
			.append('circle')
			.attr('fill', (d) => (d.children ? '#555' : '#999'))
			.attr('r', d => 4);
        
        node
            .filter(d => d.data.type == 'entity')
            .append('rect')
            .attr('x', -4)
            .attr('y', -4)
            .attr('width', 8)
            .attr('height', 8)
            .attr('fill', d => d.data.name == 'target' ? 'red' : 'black')

		node
			.append('text')
			.attr('dy', '0.31em')
			.attr('x', (d) => (d.children ? -7 : 6))
			.attr('text-anchor', (d) => (d.children ? 'end' : 'start'))
			.text((d) => d.data.name)
			.clone(true)
			.lower()
			.attr('stroke', 'white');
	};
</script>

<div class="border rounded-md my-1 py-5 flex flex-col items-center h-full w-full">
    <div bind:this={el} id="el"></div>

    <div id="legend" class="flex flex-row gap-x-5 mt-5">
        <div class="flex flex-row gap-x-2 items-center">
            <span class="block h-3 w-3 rounded-full bg-blue-500"></span>
            Has Part
        </div>
        <div class="flex flex-row gap-x-2 items-center">
            <span class="block h-3 w-3 rounded-full bg-yellow-500"></span>
            Feeds
        </div>
        <div class="flex flex-row gap-x-2 items-center">
            <span class="block h-3 w-3 rounded-full bg-green-500"></span>
            Has Point
        </div>
    </div>
</div>

<!-- w-fulloverflow-y-scroll overflow-x-scroll -->
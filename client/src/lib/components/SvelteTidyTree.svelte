<script>
	import * as d3 from 'd3';

    export let data = {};

	let width, tree, root, dx, dy, height, x0, x1;

	$: dataReady = Object.keys(data).length
	
	// SVG D3 Initialisation
	$: if(dataReady){
		
		width = 928;

		// Compute the tree height; this approach will allow the height of the
		// SVG to scale according to the breadth (width) of the tree layout.
		root  = d3.hierarchy(data);
		dx = 10;
		dy = width / (root.height + 1);

		// Create a tree layout.
		tree = d3.tree().nodeSize([dx, dy]);

		// console.debug("regenerating tree")
		// Sort the tree and apply the layout.
		root.sort((a, b) => d3.ascending(a.data.type, b.data.type));
		tree(root);
	

		// Compute the extent of the tree. Note that x and y are swapped here
		// because in the tree layout, x is the breadth, but when displayed, the
		// tree extends right rather than down.
		x0 = Infinity;
		x1 = -x0;
		root.each((d) => {
			if (d.x > x1) x1 = d.x;
			if (d.x < x0) x0 = d.x;
		});

		// Compute the adjusted height of the tree.
		height = x1 - x0 + dx * 2

		// DEBUG
	}
	

	// HELPER: Function to set path color based on relationship type (from data)
	function pathColor(pathType){
		switch(pathType) {
			case 'hasPoint':
				return 'green'
			case 'hasPart':
				return 'blue'
			case 'feeds':
				return 'orange'
			default:
				return '#555'
		}
	}

</script>

<div class="border rounded-md my-1 py-5 flex flex-col items-center">
    
    <div>
		{#if dataReady}
		<svg 
			{width} 
			{height} 
			viewBox={[-dy / 3, x0 - dx, width, height].join(" ")} 
			style='max-width: 100%; height: auto; font: 10px sans-serif;'
		>
			<!-- Links first (z-lowest) -->
			<g fill='none' stroke='#555' stroke-opacity=0.4 stroke-width=1.5>
				{#each root.links() as l }
				<path d={d3.linkHorizontal().x((d) => d.y).y((d) => d.x)(l)} stroke={pathColor(l.target.data.rel)}></path>
				{/each}
			</g>
			<!-- Nodes and text (z-highest) -->
			<g style="stroke-width: 3; stroke-linejoin: 'round'">
				{#each root.descendants() as d }
				<g transform={`translate(${d.y},${d.x})`}>
					{#if d.data.type=="point"}
					<circle fill="#999" r=4></circle>
					{:else if d.data.type == 'entity'}
					<rect x=-4 y=-4 width=8 height=8 fill={d.data.name=='target' ? 'red' : 'black'}></rect>
					{/if}

					<text dy="0.31em" x={d.children ? -7 : 6} text-anchor={d.children ? 'end' : 'start'} stroke="white">{d.data.name}</text>
					<text dy="0.31em" x={d.children ? -7 : 6} text-anchor={d.children ? 'end' : 'start'}>{d.data.name}</text>
				</g>
				{/each}
			</g>
		</svg>
		{:else}
		<div class="border-solid border-blue-500 border rounded-md p-2">
			<p>Please select a match to view graph segment</p>
		</div>
		{/if}
		
	</div>

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
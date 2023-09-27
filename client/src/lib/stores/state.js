import { derived, writable } from "svelte/store";

const API_ADDR = "http://localhost:8080"

// function createStateStore(){
//     const { subscribe, set, update } = writable({
//         "selected_module": null, 
//         "selected_match": null, 
//         "modules": [], 
//         "matches": [],
//         "diagram": {}
//     })

//     // async function getModules(){
//     //     const modules = await fetch(`${API_ADDR}/get-modules`)  
//     //     update(store => {
//     //         store['modules'] = modules
//     //         return store
//     //     })
//     // }
//     return {
//         subscribe,
//         set,
//         update
//     }
// }

// export const state = createStateStore() 

export const selected_module = writable(null);
export const selected_target = writable(null);
export const selected_match = writable(null);
export const modules = writable([]);
export const matches = writable([]);
export const filteredMatches = derived([matches, selected_target], ([$matches, $selected_target]) => $matches.filter(r => r['?target'] == $selected_target))
export const targets = derived(matches, ($matches) => new Set($matches.map((match) => match['?target'])))
export const diagram = writable({})
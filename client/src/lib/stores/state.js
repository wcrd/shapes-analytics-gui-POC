import { writable } from "svelte/store";

const API_ADDR = "http://localhost:8080"

function createStateStore(){
    const { subscribe, set, update } = writable({
        "selected_module": null, 
        "selected_match": null, 
        "modules": [], 
        "matches": [],
        "diagram": {}
    })

    // async function getModules(){
    //     const modules = await fetch(`${API_ADDR}/get-modules`)  
    //     update(store => {
    //         store['modules'] = modules
    //         return store
    //     })
    // }
    return {
        subscribe,
        set,
        update
    }
}

export const state = createStateStore() 
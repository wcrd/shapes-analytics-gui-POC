import rdflib

# helper function to split URIs
def splitURI(URI):
    return URI.toPython().split('#')

# Expected format for TidyTree
# {
#   name: label,
#   children: [ {name, children:[] }, ... ]
# }

# We are only interested in these properties from our match example
# s->p->o ; p = { feeds, isPartOf, hasPoint }


def get_children(g:rdflib.Graph, forEnt:rdflib.URIRef):
    children = []

    for pred in ['feeds', 'hasPart', 'hasPoint']:
        children_ent = list(g.objects(forEnt, rdflib.Namespace("https://brickschema.org/schema/Brick#")[pred]))
    
        for ent in children_ent:
            classType = 'point' if pred=='hasPoint' else 'entity'
            children.append({ 'uri': ent, 'name': splitURI(ent)[1], 'type': classType, 'rel': pred, 'children': get_children(g, ent)})
    
    
    return children

def generate_tidy_tree(g:rdflib.Graph, match):
    target = rdflib.URIRef(match['?target'])
    tree_data = {
        'name': splitURI(target)[1],
        'type': 'entity',
        'children': get_children(g, target)
    }

    return tree_data


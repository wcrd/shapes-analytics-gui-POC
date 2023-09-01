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
            # get metadata for display
            e_label = next(g.objects(ent, rdflib.RDFS.label), '') 
            e_cls = next(g.objects(ent, rdflib.RDF.type), '')

            children.append({ 
                'uri': ent, 
                'name': splitURI(ent)[1], 
                'display': {'label': e_label, 'cls': dict(zip(['ont', 'slug'], splitURI(e_cls)))},
                'type': classType, 
                'rel': pred, 
                'children': get_children(g, ent)})
    
    
    return children

def generate_tidy_tree(g:rdflib.Graph, match):
    target = rdflib.URIRef(match['?target'])
    # additional metadata for display
    t_label = next(g.objects(target, rdflib.RDFS.label), rdflib.Literal('#')) 
    t_cls = next(g.objects(target, rdflib.RDF.type), rdflib.Literal('#'))

    tree_data = {
        'name': splitURI(target)[1],
        'display': {'label': t_label, 'cls': dict(zip(['ont', 'slug'], splitURI(t_cls)))},
        'type': 'entity',
        'children': get_children(g, target)
    }

    return tree_data


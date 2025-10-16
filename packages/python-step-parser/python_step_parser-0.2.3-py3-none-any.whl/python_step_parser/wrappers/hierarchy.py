from typing import List, Tuple, Dict
from .. import step_types
from .. import StepParser
from .product_wrapper import ProductWrapper

def get_product_key(parser: StepParser, shp: step_types.ProductDefinitionShape):
    if parser.get_entity_type(shp.definition.key) != 'NEXT_ASSEMBLY_USAGE_OCCURRENCE':
        return -1
    assm = step_types.NextAssemblyUsageOccurrence(parser, shp.definition.key)
    
    if parser.get_entity_type(assm.related_product_definition) != 'PRODUCT_DEFINITION':
        return -1
    prd_def = step_types.ProductDefinition(parser, assm.related_product_definition)
    
    if parser.get_entity_type(prd_def.formation.key) != 'PRODUCT_DEFINITION_FORMATION':
        return -1
    prd_def_frm = step_types.ProductDefinitionFormation(parser, prd_def.formation.key)

    return prd_def_frm.product.key

def build_tree(parser: StepParser,
               prods: Dict[str, Dict],
               shapes: Dict[str, step_types.ContextDependentShapeRepresentation], root_id):
    return {
        'name': root_id,
        'type': 'Root'
    } | (
        {
            'key': shapes[root_id].key,
            'type': str(shapes[root_id].product_def_shape.name),
            'product': get_product_key(parser, shapes[root_id].product_def_shape),
        }
        if root_id in shapes
        else {}
    ) | (
        {
            'n_children': len(prods[root_id]),
            'children': [build_tree(parser, prods[root_id], shapes, i) for i in prods[root_id].keys() if i != root_id]
        }
        if root_id in prods and len(prods[root_id].keys()) > 0
        else {}
    )

def insert_recursive(dict, path, val):
    if len(path) == 0:
        return
    if path[0] not in dict:
        dict[path[0]] = {}
    if len(path) == 1:
        dict[path[0]] |= { val: {} }
    elif len(path) > 1:
        insert_recursive(dict[path[0]], path[1:], val)

def build_prod_hierarchy(prods: Dict[str, List[str]], links: Dict[str, List[str]]):
    link_lookup = {}
    for k, v in links.items():
        for val in v:
            link_lookup[val] = k
    lookup = lambda x: [link_lookup[x]] + lookup(link_lookup[x]) if x in link_lookup else []
    vals = {}
    for k, v in prods.items():
        for val in v:
            hierarchy = list(reversed(([k] if k != val else []) + lookup(k)))
            insert_recursive(vals, hierarchy, val)
    return vals

def get_product_hierarchy(parser: StepParser, products: List[step_types.Product]):
    prods = {}
    links = {}
    shapes = {}
    for p in products:
        prods[p.id] = []
        wrapped_product = ProductWrapper(parser, p)
        for u in wrapped_product.usages:
            name = u.product_def_shape.definition.name
            prods[p.id].append(name)
            shapes[name] = u
        for l in wrapped_product.links:
            name = l.product_def_shape.definition.name
            if p.id not in links:
                links[p.id] = []
            links[p.id].append(name)
            
    product_tree = build_prod_hierarchy(prods, links)
    return build_tree(parser, product_tree, shapes, list(product_tree.keys())[0])
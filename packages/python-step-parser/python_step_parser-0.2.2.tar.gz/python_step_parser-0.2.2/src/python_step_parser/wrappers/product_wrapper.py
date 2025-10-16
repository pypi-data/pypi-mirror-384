from typing import Dict, List, Any

from ..step_parser import StepParser
from .. import step_types

class ProductWrapper():
    product: step_types.Product
    usages: List[step_types.ContextDependentShapeRepresentation]
    links: List[step_types.ContextDependentShapeRepresentation]

    def __init__(self, parser: StepParser, product: step_types.Product):
        self.product = product
        self.__parse_usages(parser)
    
    def __parse_usages(self, parser: StepParser):
        p1 = parser.get_parents_of_type(self.product.key, 'PRODUCT_DEFINITION_FORMATION')
        if len(p1) == 0:
            return
        
        p2 = parser.get_parents_of_type(p1[0], 'PRODUCT_DEFINITION')
        if len(p2) == 0:
            return
        
        assemblies = [
            (
                self.__parse_shape(parser, k),
                step_types.NextAssemblyUsageOccurrence(parser, k).related_product_definition == p2[0]
            )
            for k
            in parser.get_parents_of_type(p2[0], 'NEXT_ASSEMBLY_USAGE_OCCURRENCE')
        ]

        self.usages = [a[0] for a in assemblies if a[1]]
        self.links = [a[0] for a in assemblies if not a[1]]
    
    def __parse_shape(self, parser: StepParser, next_assembly_usage_key: int):
        p1 = parser.get_parents_of_type(next_assembly_usage_key, 'PRODUCT_DEFINITION_SHAPE')
        if len(p1) == 0:
            return
        
        p2 = parser.get_parents_of_type(p1[0], 'CONTEXT_DEPENDENT_SHAPE_REPRESENTATION')
        if len(p2) == 0:
            return
        
        return step_types.ContextDependentShapeRepresentation(parser, p2[0])


def get_product_wrappers(parser: StepParser, product_name: str) -> ProductWrapper:
    return [
        wrapper
        for wrapper
        in get_all_product_wrappers(parser)
        if wrapper.product.id == product_name
    ][0]

def get_all_product_wrappers(parser: StepParser) -> List[ProductWrapper]:
    return [
        ProductWrapper(parser, step_types.Product(parser, key))
        for key
        in parser.get_products()
    ]
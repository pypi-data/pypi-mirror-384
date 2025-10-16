from .helpers import clean_display, clean_display_list
from .transient import Transient
from .product_definition_shape import ProductDefinitionShape
from .shape_representation_relationship import ShapeRepresentationRelationship
from ..step_parser import StepParser

class ContextDependentShapeRepresentation(Transient):
    def __init__(self, parser: StepParser, key: int):
        super().__init__(parser, key)
        self.__get_arguments(parser)

    def __str__(self):
        return f'''CONTEXT_DEPENDENT_SHAPE_REPRESENTATION (
{self._str_args()}
)
'''
    
    def _str_args(self):
        return f'''{super()._str_args()}
    shape_rep    = {clean_display(self.shape_representation_rel)}
    pdef_shape   = {clean_display(self.product_def_shape)}'''
    
    def __get_arguments(self, parser: StepParser):
        args = parser.get_arguments(self.key)
        
        self.shape_representation_rel = ShapeRepresentationRelationship(parser, args[0])
        self.product_def_shape = ProductDefinitionShape(parser, args[1])
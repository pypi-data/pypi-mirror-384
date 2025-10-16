from .helpers import clean_display, clean_display_list
from . import product_definition_relationship
from ..step_parser import StepParser
from ..child_type_register import ChildTypeRegister

type_name = 'PRODUCT_DEFINITION_USAGE'
class ProductDefinitionUsage(product_definition_relationship.ProductDefinitionRelationship):
    type_name = type_name
    def __init__(self, parser: StepParser, key: int):
        super().__init__(parser, key)
        self.__get_arguments(parser)

    def __str__(self):
        return f'''{type_name} (
{self._str_args()}
)
'''
    
    def _str_args(self):
        return f'{super()._str_args()}'
    
    def __get_arguments(self, parser: StepParser):
        args = parser.get_arguments(self.key)
        
        # No additional args

child_type_register = ChildTypeRegister(type_name, product_definition_relationship.child_type_register)
child_type_register.register(type_name, lambda parser, key: ProductDefinitionUsage(parser, key))
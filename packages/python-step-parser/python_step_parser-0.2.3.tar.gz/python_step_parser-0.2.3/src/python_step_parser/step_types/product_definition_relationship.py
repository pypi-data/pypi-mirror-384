from . import transient
from .abstract_types import characterized_definition_register
from ..step_parser import StepParser
from ..child_type_register import ChildTypeRegister

type_name = 'PRODUDCT_DEFINITION_RELATIONSHIP'
class ProductDefinitionRelationship(transient.Transient):
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
        return f'''{super()._str_args()}
    id           = {self.id}
    name         = {self.name}
    description  = {self.description}
    relating_def = {self.relating_product_definition}
    related_def  = {self.related_product_definition}'''
    
    def __get_arguments(self, parser: StepParser):
        args = parser.get_arguments(self.key)
        
        self.id = args[0]
        self.name = args[1]
        self.description = args[2]
        self.relating_product_definition = args[3]
        self.related_product_definition = args[4]


child_type_register = ChildTypeRegister(type_name, [
    transient.child_type_register,
    characterized_definition_register
])
child_type_register.register(type_name, lambda parser, key: ProductDefinitionRelationship(parser, key))
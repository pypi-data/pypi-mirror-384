from .helpers import clean_display, clean_display_list
from . import assembly_component_usage 
from ..step_parser import StepParser
from ..child_type_register import ChildTypeRegister

type_name = 'NEXT_ASSEMBLY_USAGE_OCCURRENCE'
class NextAssemblyUsageOccurrence(assembly_component_usage.AssemblyComponentUsage):
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

child_type_register = ChildTypeRegister(type_name, assembly_component_usage.child_type_register)
child_type_register.register(type_name, lambda parser, key: NextAssemblyUsageOccurrence(parser, key))
from .helpers import clean_display
from .axis2_placement3d import Axis2Placement3d
from ..step_parser import StepParser
from . import transient
from ..step_parser import StepParser

type_name = 'ITEM_DEFINED_TRANSFORMATION'
class ItemDefinedTransformation(transient.Transient):
    type_name = type_name
    def __init__(self, parser: StepParser, key: int, resolve_children: bool = False):
        super().__init__(parser, key, resolve_children)
        self.__get_arguments(parser)

    def __str__(self):
        return f'''{type_name} (
{self._str_args()}
)
'''
    
    def _str_args(self):
        return f'''{super()._str_args()}
    name         = {self.name}
    description  = {self.description}
    trans_item1  = {clean_display(self.trans_item1) if self.resolve_children else self.trans_item1}
    trans_item2  = {clean_display(self.trans_item2) if self.resolve_children else self.trans_item2}'''
    
    
    def __get_arguments(self, parser: StepParser):
        args = parser.get_arguments(self.key)
        self.name = args[0]
        self.description = args[1]
        if self.resolve_children:
            self.trans_item1 = Axis2Placement3d(parser, args[2])
            self.trans_item2 = Axis2Placement3d(parser, args[3])
        else:
            self.trans_item1 = args[2]
            self.trans_item2 = args[3]
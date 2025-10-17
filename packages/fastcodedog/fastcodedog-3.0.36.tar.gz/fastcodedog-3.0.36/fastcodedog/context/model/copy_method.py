# -*- coding: utf-8 -*-
from fastcodedog.context.contextbase import ContextBase
from fastcodedog.context.model.parameter import Parameter

class CopyMethod(ContextBase):
    def __init__(self):
        super().__init__()
        self.title = ''
        self.name = ''
        # self.pydantic_type = ''
        self.comment = ''
        self.module = ''
        self.model_name = ''
        self.parameters = []
        self._types['parameters'] = Parameter
        self.specified_attribute_values = {}
        self._types['specified_attribute_values'] = dict
        self.relations_should_copy = {}
        self._types['relations_should_copy'] = dict
        self.relations_should_new_and_copy = {}
        self._types['relations_should_new_and_copy'] = dict
        # self.nullable = True
        self.script = ''
        self.import_ = []
        self._types['import_'] = str

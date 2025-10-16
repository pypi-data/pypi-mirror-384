# -*- coding: utf-8 -*-
from fastcodedog.context.contextbase import ContextBase


class Parameter(ContextBase):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.type = ''
        self.nullable = False
        self.default_value = ''
        # self.pydantic_type = ''
        self.comment = ''

    def load(self, json, force_set_value = False):
        """需要强行设置default_value"""
        super().load(json, force_set_value = True)

# -*- coding: utf-8 -*-
from fastcodedog.context.contextbase import ContextBase


class Tenant(ContextBase):
    def __init__(self):
        super().__init__()
        self.enabled = False
        self.local_column_code = "tenant_id"
        self.foreign_table_code = "base_tenant"
        self.foreign_column_code = "id"

# -*- coding: utf-8 -*-
from fastcodedog.prepare.pdm_to_model.column import Column


def fill_tenant_id(pdm, local_column_code, foreign_table_code, foreign_column_code):
    foreign_table = pdm.tables.get(foreign_table_code)
    foreign_column = foreign_table.columns.get(foreign_column_code)
    for table in pdm.tables.values():
        if table.is_join_table:
            continue
        if table.code == foreign_table_code:
            continue
        if local_column_code in table.columns:
            continue

        tenant_column = Column(table, None)
        tenant_column.code = local_column_code
        tenant_column.name = '租户'
        tenant_column.comment = f'租户id，关联{foreign_table_code}.{foreign_column_code}'
        tenant_column.data_type = foreign_column.data_type
        tenant_column.length = foreign_column.length
        tenant_column.nullable = True       # 需要后台稳定之后才改为必填
        tenant_column.identity = foreign_column.identity
        tenant_column.domain = foreign_column.domain
        tenant_column.set_foreign_key(foreign_table, foreign_column)

        new_columns = list(table.columns.items())
        # 在第二个位置插入
        if len(new_columns) > 0:
            new_columns.insert(1, (local_column_code, tenant_column))
        table.columns = dict(new_columns)

        # 调整唯一键
        for l in table.unique_keys.values():    # 原来的唯一键组合都需要增加tenant_id
            l.append(tenant_column)
        for column in table.columns.values():   # 不再存在独立的唯一键
            if column.unique:
                column.unique = False
                # table.unique_keys[f'UKEY_TENANT_{column.code.upper()}'] = [column, tenant_column]


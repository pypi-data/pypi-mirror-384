# -*- coding: utf-8 -*-
import json5
import os
import re

from fastcodedog.util.case_converter import camel_to_snake


def add_relationships(model_directory, additional_relationships):
    """系统默认建议的子对象，有时候不需要，比如定单表关联用户，但是不能在用户表创建用户的所有定单这个变量，否则数据量太大。所以需要禁用"""
    for additional_relationship in additional_relationships:
        module = additional_relationship.get('module')
        model_name = additional_relationship.get('model_name')
        name = additional_relationship.get('name')
        if module and model_name and name:
            json_file = os.path.join(model_directory, module, f'{camel_to_snake(model_name)}.json5')
            data = json5.load(open(json_file, 'r', encoding='utf-8'))
            # 移除 additional_relationship 中的 module 和 model_name
            additional_relationship.pop('module')
            additional_relationship.pop('model_name')
            data['relationships'][name] = additional_relationship
            json5.dump(data, open(json_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)



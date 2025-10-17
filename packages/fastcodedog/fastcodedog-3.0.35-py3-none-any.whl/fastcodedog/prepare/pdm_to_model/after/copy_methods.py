# -*- coding: utf-8 -*-
import json5
import os

from fastcodedog.util.case_converter import camel_to_snake


def add_copy_methods(model_directory, copy_methods):
    for copy_method in copy_methods:
        module = copy_method.get('module')
        model_name = copy_method.get('model_name')

        json_file = os.path.join(model_directory, module, f'{camel_to_snake(model_name)}.json5')
        data = json5.load(open(json_file, 'r', encoding='utf-8'))
        if 'copy_methods' not in data:
            data['copy_methods'] = {}
        data['copy_methods'][copy_method['name']] = copy_method
        json5.dump(data, open(json_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

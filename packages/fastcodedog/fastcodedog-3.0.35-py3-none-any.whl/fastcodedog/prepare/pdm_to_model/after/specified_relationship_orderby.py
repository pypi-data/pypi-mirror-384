# -*- coding: utf-8 -*-
import json5
import os
from fastcodedog.util.case_converter import camel_to_snake

def specified_relationship_orderby(model_directory, specified_relationship_by):
    for srb in specified_relationship_by:
        module = srb.get('module')
        model_name = srb.get('model_name')
        relationship_name = srb.get('relationship_name')
        order_by = srb.get('order_by')


        json_file = os.path.join(model_directory, module, f'{camel_to_snake(model_name)}.json5')
        data = json5.load(open(json_file, 'r', encoding='utf-8'))
        if 'relationships' not in data or relationship_name not in data['relationships']:
            continue
        data['relationships'][relationship_name]['order_by'] = order_by
        json5.dump(data, open(json_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)




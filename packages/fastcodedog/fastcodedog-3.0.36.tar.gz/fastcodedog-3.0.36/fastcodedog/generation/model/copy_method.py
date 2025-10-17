# -*- coding: utf-8 -*-
from fastcodedog.context.common.get_context_object import get_model_context
from fastcodedog.generation.base.function import Function
from fastcodedog.context.model.copy_method import CopyMethod as CopyMethodContext
from fastcodedog.generation.base.location_finder import LocationFinder
from fastcodedog.generation.base.text import Text
from fastcodedog.util.case_converter import camel_to_snake


class CopyMethod(Function):
    def __init__(self, context: CopyMethodContext):
        super().__init__(name=context.name, context=context, # decorators=[Function.Decorator('property')],
                         params={'self': Function.Parameter('self', nullable=False), 'session': Function.Parameter('session', nullable=False)},
                         comment=context.comment)
        for parameter in context.parameters:
            self.params[parameter.name] = Function.Parameter(name=parameter.name, type=parameter.type,
                                                             default_value=parameter.default_value,
                                                             nullable=parameter.nullable, comment=parameter.comment)
            if parameter.comment:
                self.comment += f'\n:param {parameter.name}: {parameter.comment}'
        self.specified_attribute_values = context.specified_attribute_values
        self.relations_should_copy = context.relations_should_copy
        self.relations_should_new_and_copy = context.relations_should_new_and_copy
        self.add_possible_imports(context.import_)
        # 内部使用的变量
        self.model = get_model_context(self.context.module, self.context.model_name)

        self.blocks.extend(self.get_copy_texts())

    def get_copy_texts(self):
        dest_instance_name = camel_to_snake(self.model.name)
        texts = self._get_model_copy_texts('self', dest_instance_name, self.model,
                                           self.specified_attribute_values, self.relations_should_copy, self.relations_should_new_and_copy)
        texts.append(Text(f'\nreturn {dest_instance_name}'))
        return texts

    @staticmethod
    def get_luckyname(name):
        if name.endswith('_id'):
            return name[:-3]
        if name.endswith('_uid'):
            return name[:-4]
        return name

    def _get_model_copy_texts(self, src_instance_name, dest_instance_name, model,
                              specified_attribute_values, relations_should_copy, relations_should_new_and_copy,indent=None):
        texts = []
        # 标准化参数
        if specified_attribute_values is None:
            specified_attribute_values = {}
        if relations_should_copy is None:
            relations_should_copy = {}
        if relations_should_new_and_copy is None:
            relations_should_new_and_copy = {}
        if indent is None:
            indent = ''
        # 添加import
        if model != self.model:
            package = LocationFinder.get_package(model.name, 'model', model.module)
            texts.append(Text(f'from {package} import {model.name}', indent=indent))
        # 添加初始化
        texts.append(Text(f'{dest_instance_name} = {model.name}()', indent=indent))
        for _, column in model.columns.items():
            if column.name in specified_attribute_values:
                if specified_attribute_values[column.name] is not None:
                    texts.append(Text(f'{dest_instance_name}.{column.name} = {specified_attribute_values[column.name]}', indent=indent))
                else:
                    texts.append(Text(f'# {dest_instance_name}.{column.name} = None', indent=indent))
            else:
                texts.append(Text(f'{dest_instance_name}.{column.name} = {src_instance_name}.{column.name}', indent=indent))

        # 在处理relationship之前，将dest_instance添加到session中，是否会报警
        texts.append(Text(f'session.add({dest_instance_name})', indent=indent))

        # 处理关联关系
        for _, relationship in model.relationships.items():
            if relationship.name in relations_should_copy:
                # 先处理直接用等号赋值的属性，relations_should_new_and_copy是需要新建对象的情况
                if relationship.name in relations_should_new_and_copy:
                    continue
                # 这里配置容易出错，给个报错
                if ((relationship.name in specified_attribute_values and specified_attribute_values[relationship.name])
                        or (relationship.name in relations_should_copy and relations_should_copy[relationship.name])):
                    raise ValueError(f'关联关系{relationship.name}配置错误，只有新创建的对象（relations_should_new_and_copy中）才支持配置specified_attribute_values、relations_should_copy。在没有配置relations_should_new_and_copy的情况下，只能采用=进行赋值')
                texts.append(Text(f'{dest_instance_name}.{relationship.name} = {src_instance_name}.{relationship.name}', indent=indent))
        for _, relationship in model.relationships.items():
            if relationship.name in relations_should_copy:
                # 再处理需要新建对象的属性
                if relationship.name not in relations_should_new_and_copy:
                    continue
                # 添加一个换行
                texts.append(Text('', indent=indent))
                sub_indent = indent + self.DEFAULT_INDENT
                if relationship.is_list:
                    sub_dest_instance_name = self.get_luckyname(relationship.original_name)
                    sub_src_instance_name = f'{sub_dest_instance_name}_'
                    # 添加for循环
                    texts.append(Text(f'for {sub_src_instance_name} in {src_instance_name}.{relationship.name}:', indent=indent))
                    texts.extend(self._get_model_copy_texts(sub_src_instance_name, sub_dest_instance_name,
                                                            get_model_context(relationship.back_populates_module, relationship.back_populates_model),
                                                            specified_attribute_values = specified_attribute_values[relationship.name] if relationship.name in specified_attribute_values else None,
                                                            relations_should_copy = relations_should_copy[relationship.name],
                                                            relations_should_new_and_copy = relations_should_new_and_copy[relationship.name] if relationship.name in relations_should_new_and_copy else None,
                                                            indent=sub_indent))
                    texts.append(Text(f'{dest_instance_name}.{relationship.name}.append({sub_dest_instance_name})', indent=sub_indent))
                else:
                    sub_dest_instance_name = relationship.name
                    sub_src_instance_name = f'{sub_dest_instance_name}_'
                    # 把原属性改为变量，简化代码，特别是多层级的代码
                    texts.append(Text(f'{sub_src_instance_name} = {src_instance_name}.{relationship.name}', indent=indent))
                    texts.extend(self._get_model_copy_texts(sub_src_instance_name, sub_dest_instance_name,
                                                            get_model_context(relationship.back_populates_module,
                                                                              relationship.back_populates_model),
                                                            specified_attribute_values = specified_attribute_values[
                                                                relationship.name] if relationship.name in specified_attribute_values else None,
                                                            relations_should_copy = relations_should_copy[relationship.name],
                                                            relations_should_new_and_copy = relations_should_new_and_copy[relationship.name] if relationship.name in relations_should_new_and_copy else None,
                                                            indent=sub_indent))
        return texts

    # def serialize(self, delimiter='\n', with_comment=True):
    #     return delimiter + super().serialize(delimiter=delimiter, with_comment=with_comment)

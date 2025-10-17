# -*- coding: utf-8 -*-
from fastcodedog.context.context import ctx_instance
from fastcodedog.generation.base.file import File
from fastcodedog.generation.base.location_finder import LocationFinder
from fastcodedog.generation.base.required_import import RequiredImport
from fastcodedog.generation.model.base import Base


class Init(File):
    def __init__(self):
        super().__init__('init', file_path=LocationFinder.get_path('__init__', 'model'), package='', context={})
        # self._init_required_imports()

    def get_required_imports(self):
        """File.serialize()调用，本方法里不能调用File.serialize()，因为可能会有循环依赖"""
        required_import = RequiredImport()
        required_import.add('Base', Base().package)
        for module, models in ctx_instance.models.items():
            for model in models.values():
                required_import.add(model.name, LocationFinder.get_package(model.name, 'model', module))
        # 支持自定义listener
        for listen in ctx_instance.listens:
            required_import.add(import_=listen.import_, from_=listen.from_, as_=listen.alias)
        return required_import

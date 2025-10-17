# -*- coding: utf-8 -*-
import os

from fastcodedog.common.write_file import write_python_file
from fastcodedog.context.context import ctx_instance
from fastcodedog.generation.base.file import File
from fastcodedog.generation.base.head_comment import HeadComment
from fastcodedog.generation.base.location_finder import LocationFinder
from fastcodedog.generation.base.required_import import Import
from fastcodedog.generation.base.text import Text
from fastcodedog.generation.api.db import Db
from fastcodedog.util.read_inc import read_inc


class ApiLogging(File):
    def __init__(self):
        super().__init__(name='api_logging',
                         file_path=os.path.join(ctx_instance.project.directory, 'util', 'api_logging.py'),
                         package=f'{ctx_instance.project.package}.util.api_logging')

        self.head_comment = HeadComment("""Middleware to log API requests and responses into operation_api_log (ApiLog).

Behavior:
- Before request: capture request metadata and body, create an ApiLog record.
- After response: capture response metadata and body, update the ApiLog record.

Notes:
- This middleware is defensive: DB errors will not prevent the HTTP response from being returned.
- It attempts to preserve the request body for downstream handlers.
        """, parent=self)
        self.blocks.append(Text(content=read_inc('inc/middleware/api_logging.file.in'),
                                possible_imports=['from starlette.middleware.base import BaseHTTPMiddleware',
                                                  'from starlette.requests import Request',
                                                  'from starlette.responses import Response',
                                                  'from starlette.responses import FileResponse',
                                                  'import time', 'import json', 'import datetime',
                                                  Import('Session', Db().package),
                                                  Import('ApiLog', LocationFinder.get_package('ApiLog', 'model', 'operation'))]))

    def save(self):
        write_python_file(self.file_path, self.serialize(), repalce_async=False)

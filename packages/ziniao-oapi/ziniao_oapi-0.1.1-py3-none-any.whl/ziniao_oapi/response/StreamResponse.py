#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json

from requests import Response

from ziniao_oapi.response.BaseResponse import BaseResponse
from ziniao_oapi.response.Event import Event


class EventResponse(BaseResponse):
    def __init__(self, line=None, event=True, **kwargs):
        if event:
            self.content = Event.parse(line)
            super().__init__(json.loads(self.content.data), **kwargs)
        else:
            super().__init__(json.loads(line), **kwargs)

    def get_content(self):
        return self.content


class StreamResponse(object):

    def __init__(self, response: Response):
        self.response = response

    def __iter__(self):
        return self.iter_content(1024)

    def iter_content(self, chunk_size=1024, decode_unicode=False, delimiter=None):
        for line in self.response.iter_lines(chunk_size=chunk_size, decode_unicode=decode_unicode, delimiter=delimiter):
            if line:
                if not isinstance(line, str):
                    line = line.decode('utf-8')
                content_type = self.response.headers.get('Content-Type')
                if "json" in content_type:
                    content_response = EventResponse(line, event=False)
                else:
                    content_response = EventResponse(line)
                yield content_response

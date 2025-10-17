import cli2
import cli2.display
from datetime import datetime
import os
import subprocess
import sys
import textwrap
import yaml

from artinator import settings
from .tool import Tool


class Context:
    PATH = settings.HOME / 'history'
    CURRENT_PATH = PATH / 'current'
    extension = 'yml'
    SYSTEM_PROMPT_DEFAULT = textwrap.dedent('''
    You are Artinator, an elite system, networks and coding assistant designed
    to solve system, network and programming problems using a strict tool-first
    workflow.
    NEVER ASK THE USER FOR INFORMATION YOU CAN FIND WITH A TOOL.
    ALWAYS TRY TO USE THE TOOLS.
    ''')

    def __init__(self, path=None, **data):
        self.path = path
        self.data = data

    @property
    def name(self):
        return self.data.get('name', self.path.name)

    @name.setter
    def name(self, value):
        self.data['name'] = value
        self.path = self.path.parent / f'{value}.yml'

    @property
    def messages(self):
        if 'messages' not in self.data:
            self.data['messages'] = [
                dict(role='system', content=self.SYSTEM_PROMPT_DEFAULT),
            ]
        return self.data['messages']

    @messages.setter
    def messages(self, value):
        self.data['messages'] = value

    def add(self, **kwargs):
        self.messages.append(dict(**kwargs))

    @classmethod
    def current(cls):
        if cls.CURRENT_PATH.exists():
            with cls.CURRENT_PATH.open('r') as f:
                data = yaml.safe_load(f.read())
            return Context(path=cls.CURRENT_PATH.resolve(), **data)
        return cls.factory()

    @classmethod
    def factory(cls):
        return cls(
            path=cls.PATH / '.'.join([
                datetime.now().strftime('%Y%m%d-%H%M'),
                'yml',
            ]),
        )
        context.save()

    def save(self):
        yaml_str = cli2.display.yaml_dump(self.data)
        self.path.parent.mkdir(exist_ok=True, parents=True)
        with self.path.open('w') as f:
            f.write(yaml_str)
        self.switch()

    def switch(self):
        if self.CURRENT_PATH.is_symlink():
            self.CURRENT_PATH.unlink()
        self.CURRENT_PATH.symlink_to(self.path)

    @property
    def tools(self):
        return [tool.definition() for tool in Tool.tools().values()]

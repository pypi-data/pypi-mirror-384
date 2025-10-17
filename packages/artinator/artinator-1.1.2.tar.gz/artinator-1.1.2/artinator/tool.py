import cli2
import importlib.metadata
import json


class Parameter:
    def __init__(self, description, type=None, required=True):
        self.type = type or 'string'
        self.description = description
        self.required = required

    def __get__(self, obj, objtype=None):
        return obj.data.get(self.name, self.default)

    def __set__(self, obj, value):
        obj.data[self.name] = value

    def definition(self):
        return dict(
            type=self.type,
            description=self.description,
        )

import re

def camel_to_snake(name):
    # Add underscore before any uppercase letter, then convert to lowercase
    # Example: camel_to_snake('CamelCase') == 'camel_case'
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class Tool:
    priority = 9

    def __init_subclass__(cls, **kwargs):
        cls._parameters = {}

        for attr, obj in cls.__dict__.items():
            if not isinstance(obj, Parameter):
                continue
            obj.name = attr
            cls._parameters[obj.name] = obj

        cls.name = camel_to_snake(cls.__name__)

    def __init__(self, name=None, _repr=None):
        if name:
            self.name = name
        self._repr = _repr

    def __repr__(self):
        return self._repr or self.name

    async def __call__(self, call):
        print(f'{cli2.t.o(call.function.name)}({call.function.arguments})')
        try:
            result = await self.run(**json.loads(call.function.arguments))
        except Exception as exc:
            cli2.log.exception()
            result = str(exc)

        return dict(
            role='tool',
            tool_call_id=call.id,
            name=call.function.name,
            content=result,
        )

    @classmethod
    def factory(cls, plugin):
        return cls(plugin.name, _repr=plugin.value)

    @classmethod
    def get(cls, name):
        return cls.tools()[name]

    @classmethod
    def tools(cls):
        if '_tools' not in cls.__dict__:
            cls._tools = {
                plugin.name: plugin.load().factory(plugin)
                for plugin in importlib.metadata.entry_points(group='artinator')
            }
        return cls._tools

    def definition(self):
        definition = {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': {
                        parameter.name: parameter.definition()
                        for parameter in self._parameters.values()
                    },
                },
            },
        }
        definition['function']['parameters']['required'] = [
            parameter.name
            for parameter in self._parameters.values()
            if parameter.required
        ]
        return definition


class FileRead(Tool):
    description = 'Read a file contents'
    path = Parameter(
        'Path of the file to read contents of',
        type='string',
    )

    async def run(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError as exc:
            return f'{exc}, call a bash script to find it'


class BashScript(Tool):
    description = 'Execute a bash shell script'
    script = Parameter(
        'Bash shell script to execute, allows all linux commands such as grep, find, and so on',
        type='string',
    )
    name = 'shell_command'

    async def run(self, script):
        proc = cli2.Proc('bash', '-xc', script)
        await proc.wait()
        return proc.stdout

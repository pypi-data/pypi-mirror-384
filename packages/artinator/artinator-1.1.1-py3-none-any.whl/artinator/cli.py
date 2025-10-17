import asyncio
import cli2
import litellm
import os
import re
import sys
import textwrap

try:
    import truststore
except ImportError:
    pass
else:
    truststore.inject_into_ssl()

from .model import Model
from .context import Context
from .tool import Tool
from . import settings
from . import project


context = Context.factory()


class Group(cli2.Group):
    def help(self, *args, short=False, **kwargs):
        if short:
            return super().help(short=short)

        print(cli2.t.o.b('SYNOPSIS'))
        print('Run artinator <your query>')
        print()

        print(cli2.t.o.b('EXAMPLE'))
        print('artinator how to develop skynet?')
        print()

        table = cli2.Table(
            (cli2.t.y.b('$MODE'), str(settings.MODE)),
            (cli2.t.y.b('$HOME'), str(settings.HOME)),
            (cli2.t.y.b('CONTEXT'), str(context.path)),
            (cli2.t.y.b('$MODEL'), str(os.getenv('MODEL'))),
        )
        table.print()
        print()

        table = cli2.Table(*[
            (
                (
                    getattr(cli2.t, command.color, command.color),
                    name,
                ),
                command.help(short=True),
            )
            for name, command in self.items()
        ])
        self.print('ORANGE', 'COMMANDS')
        table.print()


class EntryPoint(Group):
    # just a wrapper that calls main if unknown args are passed instead of
    # showing help
    def __call__(self, *argv):
        if settings.MODE == 'system':
            del self['project']

        self.exit_code = 0
        if not argv:
            return self.help()

        if argv[0] not in self:
            return asyncio.run(main(*argv))

        return super().__call__(*argv)

    def add(self, target, *args, **kwargs):
        # user might use "artinator help me do this"
        # we don't want that to be catched as a command
        # no-op the automatic help sub-command
        if target.__name__ == 'help':
            return
        super().add(target, *args, **kwargs)


cli = EntryPoint()


async def main(*prompt):
    return await run(prompt, Context.factory())


@cli.cmd(name='cont', color='yellow')
async def _continue(*prompt):
    """
    Continue the context with another prompt
    """
    return await run(prompt, Context.current())


context_cli = cli.group(
    'context',
    doc='Context management commands',
    grpclass=Group,
)


@context_cli.cmd(color='green')
def archive(*new_name):
    """
    Archiving this context will create a new current context.

    :param new_name: Optionnal name for this context to archive.
    """
    if new_name:
        name(*new_name)
    Context.CURRENT_PATH.unlink()


@context_cli.cmd(color='green')
def name(*name):
    """
    Rename current context.

        artinator context name This is the new name
    """
    context.name = ' '.join(name)
    context.save()


@context_cli.cmd(color='green')
def list():
    """
    List saved contexts
    """
    def get_file_time(path):
        """Get the best available time attribute for sorting"""
        try:
            stat = path.stat()

            # Prefer modification time
            if hasattr(stat, 'st_mtime') and stat.st_mtime > 0:
                return stat.st_mtime

            # Platform-specific creation time attributes
            if sys.platform == "darwin":  # macOS
                return getattr(stat, 'st_birthtime', stat.st_ctime)
            elif sys.platform == "win32":  # Windows
                return getattr(stat, 'st_ctime', 0)
            else:  # Linux and other Unix-like systems
                # st_ctime is metadata change time on Unix, not creation time
                return stat.st_ctime

        except (OSError, AttributeError):
            return 0

    def sorted_by_time(path, reverse=True):
        """Sort directory contents by time (mtime -> creation time fallback)"""
        items = [p for p in path.iterdir() if p.exists()]
        return sorted(items, key=get_file_time, reverse=reverse)

    return [
        file.name[:-4]  # strip .yml
        for file in sorted_by_time(Context.PATH)
    ]


@context_cli.cmd
def switch(*name):
    """
    Switch to an existing context
    """
    context = Context(path=Context.PATH / (' '.join(name) + '.yml'))
    context.switch()


@context_cli.cmd(color='green')
def show():
    """
    Dump the current context
    """
    return context.data


@context_cli.cmd(color='green')
def edit():
    """
    Edit with $EDITOR
    """
    cli2.editor(path=context.path)


project_cli = cli.group(
    'project',
    doc='Project',
    grpclass=Group,
)


@project_cli.cmd(color='green')
async def scan():
    """
    List registered tools.
    """
    print(cli2.t.o.b('SCANNING PROJECT SYMBOLS'))
    dir_indexer = scan_dir.CodeIndexer(self.project)
    paths = await dir_indexer.index_repo_async()
    print(cli2.t.o.b('ANALYZING IMPORTS'))
    import_analyzer = scan_files.ImportAnalyzer(self.project, paths, 'python')
    await import_analyzer.analyze_and_store_imports()
    print(cli2.t.o.b('GENERATING REPO MAP'))
    map_generator = repo_map.RepoMapGenerator(self.project)
    repo_map_string = await map_generator.get_map_string()
    # Consider printing the map or saving it, currently just returns
    # print(repo_map_string)
    return repo_map_string


tool_cli = cli.group(
    'tool',
    doc='AI Tools management commands',
    grpclass=Group,
)


@tool_cli.cmd(color='green')
def list():
    """
    List registered tools.
    """
    return {tool.name: repr(tool) for tool in Tool.tools().values()}


async def run(prompt, context):
    prompt = ' '.join(prompt)
    context.add(role='user', content=prompt)
    model = Model()
    while True:
        text, response = await model.send(context)
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            break

        tasks = [
            Tool.get(call.function.name)(call)
            for call in tool_calls
        ]
        for message in await asyncio.gather(*tasks):
            context.messages.append(message)
    context.save()

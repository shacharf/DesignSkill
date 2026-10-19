"""Fast local design bookkeeping. No model inference; no automatic search rebuilds."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .storage import Project, Error

HELP = '''docagent: rough documents → main ideas → modules → details

Direct commands run without an AI turn:
  status                         Resume saved focus and next step
  tree                           Show the design hierarchy
  module create TITLE --parent ID / select ID / show ID / move ID --parent ID
  discussion create TITLE [--module ID] / list / select ID / show ID
  discussion state ID open|closed|obsolete
  todo [TEXT --why REASON]        List outstanding work, or add a task
  todo --start ID / --done ID / --delete ID / --all / --next
  source add FILE_OR_URL / list / show ID
  search QUERY [--hybrid]         Search the project through GNO
  validate / checkpoint          Check files; checkpoint also refreshes navigation
  index status / flush            Inspect freshness or explicitly rebuild/retry

Files: design.md and modules/ explain the system; sources/ preserves inputs;
discussions/ preserves reasoning; TODO.md tracks work; WORK.md holds saved focus.
Edit Markdown directly. Run checkpoint after manual edits. Selection changes
saved pointers only: it cannot summarize an unsaved conversation.

Skills: doc-design guides and resumes; doc-sources extracts; doc-brainstorm
explores; doc-write explains; doc-review checks; doc-help answers workflow questions.
See DOC_WORKFLOW.md for examples and recovery. --json works with every command.
'''


def parser():
    cli = argparse.ArgumentParser(prog='docagent', description=__doc__)
    cli.add_argument('--project', type=Path, help='Explicit design project root')
    commands = cli.add_subparsers(dest='command', required=True)
    commands.add_parser('help')
    init = commands.add_parser('init', help='Initialize records and viewer; install skills with scripts/install_project.py')
    init.add_argument('directory', nargs='?', type=Path, default=Path.cwd())
    init.add_argument('--skip-gno', action='store_true', help='Initialize without search configuration')
    for name in ('status', 'tree', 'validate', 'checkpoint'):
        commands.add_parser(name)
    for kind in ('module', 'discussion', 'source'):
        operations = commands.add_parser(kind).add_subparsers(dest='operation', required=True)
        operations.add_parser('list')
        show = operations.add_parser('show'); show.add_argument('id')
        if kind == 'source':
            add = operations.add_parser('add'); add.add_argument('input'); add.add_argument('--title')
            continue
        create = operations.add_parser('create'); create.add_argument('title')
        create.add_argument('--parent', default='root') if kind == 'module' else create.add_argument('--module')
        select = operations.add_parser('select'); select.add_argument('id')
        if kind == 'module':
            move = operations.add_parser('move'); move.add_argument('id'); move.add_argument('--parent', required=True)
        else:
            state = operations.add_parser('state'); state.add_argument('id'); state.add_argument('state', choices=('open', 'closed', 'obsolete'))
    todo = commands.add_parser('todo')
    todo.add_argument('text', nargs='?'); todo.add_argument('--why', default=''); todo.add_argument('--module')
    group = todo.add_mutually_exclusive_group()
    for name in ('start', 'done', 'delete'):
        group.add_argument('--' + name)
    group.add_argument('--all', action='store_true'); group.add_argument('--next', action='store_true')
    index = commands.add_parser('index').add_subparsers(dest='operation', required=True)
    index.add_parser('status')
    flush = index.add_parser('flush'); flush.add_argument('--lexical-only', action='store_true')
    search = commands.add_parser('search'); search.add_argument('query'); search.add_argument('--limit', type=int, default=5)
    mode = search.add_mutually_exclusive_group()
    mode.add_argument('--hybrid', action='store_true'); mode.add_argument('--semantic', action='store_true')
    return cli


def run(args, project):
    command = args.command
    if command == 'status': return project.status()
    if command == 'tree': return project.tree()
    if command == 'validate': return project.validate()
    if command == 'checkpoint':
        with project.lock(): return project.checkpoint()
    if command in ('module', 'discussion', 'source'):
        if args.operation == 'list': return project.records(command)
        if args.operation == 'show':
            path, meta, body = project.record(command, args.id)
            return {**meta, 'path': str(path.relative_to(project.root)), 'body': body}
        with project.lock():
            if args.operation == 'select': return project.select(command, args.id)
            if command == 'source': return project.add_source(args.input, args.title)
            if command == 'module':
                if args.operation == 'move': return project.move_module(args.id, args.parent)
                return project.create_module(args.title, args.parent)
            if args.operation == 'state': return project.discussion_state(args.id, args.state)
            return project.create_discussion(args.title, args.module)
    if command == 'todo':
        operation = next((name for name in ('start', 'done', 'delete') if getattr(args, name)), None)
        if (args.text and (operation or args.all or args.next)) or (not args.text and (args.why or args.module)):
            raise Error('TODO text/metadata cannot be combined with list or update options')
        if args.text or operation:
            with project.lock():
                return project.add_todo(args.text, args.why, args.module) if args.text else project.update_todo(getattr(args, operation), operation)
        items = project.todos(args.all)
        return (items[0] if items else None) if args.next else items
    if command == 'index':
        from . import indexing
        if args.operation == 'status': return indexing.state(project.root)
        indexing.enqueue(project.root, project.content_files())
        return indexing.flush(project.root, semantic=not args.lexical_only)
    if command == 'search':
        from .indexing import search
        return search(project.root, args.query, mode='hybrid' if args.hybrid else ('semantic' if args.semantic else 'keyword'), limit=args.limit)
    raise Error('unknown command')


def display(value):
    if value is None or value == []: return 'No items.'
    if isinstance(value, str): return value
    if isinstance(value, list): return '\n'.join(display(item) for item in value)
    if isinstance(value, dict):
        if 'brief' in value:
            lines = [value['brief']['text'], f"\nModule: {value['active_module']} — {value['module']['title']}"]
            if 'discussion' in value:
                lines += [f"Discussion: {value['discussion']['id']} — {value['discussion']['title']}", value['discussion']['resume']['text']]
            else: lines.append('No active discussion.')
            state = value['indexing']
            if state.get('lexical_pending') or state.get('semantic_pending'):
                lines.append('Search indexing pending; saved Markdown is current.')
            for stage in ('lexical', 'semantic'):
                if state.get(stage + '_error'): lines.append(f"{stage} indexing failed: {state[stage + '_error']}")
            return '\n'.join(lines)
        if 'body' in value: return value['body']
        if 'id' in value and 'text' in value:
            return f"{value['id']} [{value['status']}] {value['text']} (module {value['module']})" + (f"\n  Why: {value['why']}" if value.get('why') else '') + (f"\n  Discussion: {value['discussion']}" if value.get('discussion') else '')
        if 'id' in value and 'title' in value:
            return '  ' * value.get('depth', 0) + f"{value['id']} {value['title']}" + (f" [{value['status']}]" if 'status' in value else '') + (f" — {value['path']}" if 'path' in value else '')
        return '\n'.join(f'{key}: {json.dumps(item, ensure_ascii=False) if isinstance(item, (list, dict)) else item}' for key, item in value.items())
    return str(value)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    machine = '--json' in argv
    argv = [arg for arg in argv if arg != '--json']
    # Accept --project anywhere, just like --json.
    if '--project' in argv:
        pos = argv.index('--project')
        if pos + 1 < len(argv):
            pair = argv[pos:pos + 2]
            del argv[pos:pos + 2]
            argv = pair + argv
    args = parser().parse_args(argv)
    try:
        if args.command == 'help': result = HELP
        elif args.command == 'init':
            project = Project.initialize(args.directory)
            from importlib.resources import files
            from .storage import atomic_write
            for name in ('index.html', 'DOC_WORKFLOW.md'):
                target = project.root / name
                if not target.exists(): atomic_write(target, files('docagent').joinpath('assets', name).read_bytes())
            if not args.skip_gno:
                from .indexing import configure
                configure(project.root)
            result = {'project': str(project.root), 'next': 'docagent status; install host skills with scripts/install_project.py'}
        else:
            project = Project(args.project) if args.project else Project.discover()
            result = run(args, project)
        print(json.dumps(result, ensure_ascii=False) if machine else display(result))
        return 1 if args.command == 'validate' and not result['valid'] else 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'error': str(exc)}) if machine else f'docagent: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

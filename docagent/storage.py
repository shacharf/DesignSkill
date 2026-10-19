"""Authoritative Markdown records, recoverable transactions, and design hierarchy."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import unquote, urlsplit
import yaml

BRIEF_LIMIT = 3000
RESUME_LIMIT = 5000
RESUME_FIELDS = ('Question', 'Current understanding', 'Immediate focus', 'Next step', 'Supporting material')


class Error(ValueError):
    pass


def atomic_write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content if isinstance(content, bytes) else content.encode())
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def read_doc(path):
    text = Path(path).read_text()
    if not text.startswith('---\n'):
        return {}, text
    match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.S)
    if not match:
        raise Error(f'{path}: unterminated frontmatter')
    try:
        meta = yaml.safe_load(match[1]) or {}
    except yaml.YAMLError as exc:
        raise Error(f'{path}: invalid YAML: {exc}') from exc
    if not isinstance(meta, dict):
        raise Error(f'{path}: frontmatter must be a mapping')
    for field in ('id', 'parent', 'module', 'active_module', 'active_discussion'):
        if field in meta and not isinstance(meta[field], str):
            raise Error(f'{path}: {field} must be a string; quote numeric IDs')
    return meta, text[match.end():]


def doc_text(meta, body):
    return '---\n' + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True) + '---\n' + body


def section(body, name):
    match = re.search(rf'<!-- doc:{name}:start -->\n?(.*?)<!-- doc:{name}:end -->', body, re.S)
    if not match:
        raise Error(f'missing {name} section')
    return match[1].strip()


def replace_section(body, name, value):
    begin, end = f'<!-- doc:{name}:start -->', f'<!-- doc:{name}:end -->'
    if body.count(begin) != 1 or body.count(end) != 1 or body.index(begin) > body.index(end):
        raise Error(f'malformed {name} section')
    return re.sub(rf'({re.escape(begin)}).*?({re.escape(end)})', lambda m: m[1] + '\n' + value.rstrip() + '\n' + m[2], body, flags=re.S)


def bounded(text, limit, location):
    return {'text': text if len(text) <= limit else text[:limit] + f'\n[Excerpt; read {location}]',
            'excerpt': len(text) > limit, 'location': location}


def title_text(title):
    title = ' '.join(title.split()).strip()
    if not title:
        raise Error('title cannot be empty')
    return title


def link_label(title):
    return str(title).replace('[', '&#91;').replace(']', '&#93;')


def resume_body(title):
    return (f'# {title}\n\n## Compact resume\n<!-- doc:resume:start -->\n' +
            '\n\n'.join(f'### {field}\n' + (title if field == 'Question' else 'Not established yet.') for field in RESUME_FIELDS) +
            '\n<!-- doc:resume:end -->\n\n## Discussion\n\n## Decisions and alternatives\n')


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if not (self.root / '.docagent/config.json').is_file():
            raise Error('no docagent project; use docagent init or the project installer')

    @classmethod
    def discover(cls):
        for root in (Path.cwd(), *Path.cwd().parents):
            if (root / '.docagent/config.json').is_file():
                return cls(root)
        raise Error('no docagent project found')

    @classmethod
    def initialize(cls, root):
        root = Path(root).resolve()
        if (root / '.rs').exists():
            raise Error('Existing research project: initialize a separate directory; automatic migration is not supported')
        if (root / '.docagent/config.json').exists():
            return cls(root)
        defaults = {
            'design.md': doc_text({'id': 'root', 'title': 'Main ideas', 'parent': ''}, '# Main ideas\n\n## Purpose\nTo be established from the source material.\n\n## Core idea\nNot established yet.\n\n## Context\nNot established yet.\n\n## Parts\n<!-- doc:children:start -->\n<!-- doc:children:end -->\n'),
            'WORK.md': doc_text({'active_module': 'root', 'active_discussion': ''}, '# Working context\n\n<!-- doc:brief:start -->\nExplain the system clearly, then refine one module at a time.\n<!-- doc:brief:end -->\n'),
            'TODO.md': '# TODO\n\n## Current work\n\n<details>\n<summary>Done</summary>\n\n<!-- doc:done:start -->\n<!-- doc:done:end -->\n\n</details>\n',
            '_sidebar.md': '<!-- doc:navigation:start -->\n<!-- doc:navigation:end -->\n',
        }
        conflicts = [name for name in defaults if (root / name).exists()]
        if conflicts:
            raise Error('Initialization would overwrite existing files: ' + ', '.join(conflicts))
        root.mkdir(parents=True, exist_ok=True)
        for directory in ('.docagent', 'modules', 'discussions', 'sources/files'):
            (root / directory).mkdir(parents=True, exist_ok=True)
        for name, text in defaults.items():
            atomic_write(root / name, text)
        atomic_write(root / '.docagent/config.json', json.dumps({'schema': 1, 'high_water': {}}))
        readme = root / 'README.md'
        if not readme.exists():
            atomic_write(readme, '# Design project\n\nThis project develops a progressively detailed system design.\n\n- [Main design ideas](design.md): start here to understand the system.\n- [Work to do](TODO.md): open tasks and design questions.\n- [Workflow help](DOC_WORKFLOW.md): skills, commands, and how to continue.\n')
        project = cls(root)
        with project.lock():
            project.refresh_navigation()
        return project

    @contextmanager
    def lock(self):
        with (self.root / '.docagent/project.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                self.recover()
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def local(self, relative):
        path = (self.root / relative).resolve()
        path.relative_to(self.root)
        return path

    def enqueue(self, paths):
        from .indexing import enqueue
        enqueue(self.root, paths)

    def transaction(self, changes):
        journal = {}
        for path, content in changes.items():
            relative = self.local(path).relative_to(self.root).as_posix()
            if relative.startswith('.docagent/'):
                raise Error('content transaction cannot modify runtime state')
            journal[relative] = content
        atomic_write(self.root / '.docagent/transaction.json', json.dumps(journal))
        self.recover()

    def recover(self):
        journal = self.root / '.docagent/transaction.json'
        if not journal.exists():
            return
        changes = json.loads(journal.read_text())
        for name, content in changes.items():
            atomic_write(self.local(name), content)
        self.enqueue(list(changes))
        journal.unlink()

    def records(self, kind):
        paths = [self.root / 'design.md', *sorted((self.root / 'modules').glob('*.md'))] if kind == 'module' else sorted((self.root / (kind + 's')).glob('*.md'))
        result = []
        for path in paths:
            meta, _ = read_doc(path)
            result.append({**meta, 'path': path.relative_to(self.root).as_posix()})
        return result

    def record(self, kind, identifier):
        matches = [item for item in self.records(kind) if item.get('id') == identifier]
        if len(matches) != 1:
            raise Error(f'{kind} {identifier} does not identify one record')
        item = matches[0]
        meta, body = read_doc(self.local(item['path']))
        return self.local(item['path']), meta, body

    def allocate(self, kind):
        config_path = self.root / '.docagent/config.json'
        config = json.loads(config_path.read_text())
        prefix = {'module': 'm', 'discussion': 'd', 'todo': 't', 'source': 's'}[kind]
        items = self.todos(True) if kind == 'todo' else self.records(kind)
        observed = [int(item['id'][1:]) for item in items if re.fullmatch(prefix + r'\d+', item.get('id', ''))]
        number = max(config['high_water'].get(kind, 0), max(observed, default=0)) + 1
        config['high_water'][kind] = number
        atomic_write(config_path, json.dumps(config, indent=2))
        return f'{prefix}{number:03d}'

    def context(self):
        return read_doc(self.root / 'WORK.md')

    def status(self):
        meta, body = self.context()
        from .indexing import state
        result = {**meta, 'brief': bounded(section(body, 'brief'), BRIEF_LIMIT, 'WORK.md'), 'indexing': state(self.root)}
        _, module, _ = self.record('module', meta['active_module'])
        result['module'] = module
        if meta.get('active_discussion'):
            path, discussion, content = self.record('discussion', meta['active_discussion'])
            result['discussion'] = {**discussion, 'resume': bounded(section(content, 'resume'), RESUME_LIMIT, str(path))}
        return result

    def select(self, kind, identifier):
        _, item, _ = self.record(kind, identifier)
        meta, body = self.context()
        if kind == 'discussion':
            if item.get('status') != 'open':
                raise Error('reopen the discussion before selecting it')
            meta['active_module'] = item['module']
        elif identifier != meta['active_module']:
            meta['active_discussion'] = ''
        meta['active_' + kind] = identifier
        self.transaction({'WORK.md': doc_text(meta, body)})
        return {'active_' + kind: identifier}

    def create_module(self, title, parent='root'):
        title = title_text(title)
        self.record('module', parent)
        identifier = self.allocate('module')
        path = f'modules/{identifier}.md'
        body = f'# {title}\n\n## Purpose\nNot established yet.\n\n## Core idea\nNot established yet.\n\n## Context\nNot established yet.\n\n## Parts and deeper detail\n<!-- doc:children:start -->\n<!-- doc:children:end -->\n'
        self.transaction({path: doc_text({'id': identifier, 'title': title, 'parent': parent}, body)})
        self.refresh_navigation()
        return {'id': identifier, 'path': path}

    def move_module(self, identifier, parent):
        if identifier == 'root':
            raise Error('cannot move root')
        path, meta, body = self.record('module', identifier)
        cursor, visited = parent, {identifier}
        while cursor:
            if cursor in visited:
                raise Error('module hierarchy would contain a cycle')
            visited.add(cursor)
            _, ancestor, _ = self.record('module', cursor)
            cursor = ancestor['parent']
        meta['parent'] = parent
        self.transaction({path: doc_text(meta, body)})
        self.refresh_navigation()
        return {'id': identifier, 'parent': parent}

    def tree(self):
        errors, _ = self.validate_hierarchy()
        if errors:
            raise Error('; '.join(errors))
        records = self.records('module')
        rows = []
        def visit(parent, depth):
            for item in records:
                if item['parent'] == parent:
                    rows.append({**item, 'depth': depth})
                    visit(item['id'], depth + 1)
        visit('', 0)
        return rows

    def create_discussion(self, title, module=None):
        title = title_text(title)
        module = module or self.context()[0]['active_module']
        self.record('module', module)
        identifier = self.allocate('discussion')
        path = f'discussions/{identifier}.md'
        self.transaction({path: doc_text({'id': identifier, 'title': title, 'module': module, 'status': 'open'}, resume_body(title))})
        return {'id': identifier, 'path': path}

    def discussion_state(self, identifier, status):
        path, meta, body = self.record('discussion', identifier)
        meta['status'] = status
        context, work = self.context()
        if status != 'open' and context.get('active_discussion') == identifier:
            context['active_discussion'] = ''
        self.transaction({path: doc_text(meta, body), 'WORK.md': doc_text(context, work)})
        return {'id': identifier, 'status': status}

    def todos(self, include_done=False):
        text = (self.root / 'TODO.md').read_text()
        rows = []
        pattern = r'^- \[([ x])\] <!-- doc:todo:(t\d+) (\{.*\}) --> (.*)$'
        for match in re.finditer(pattern, text, re.M):
            try:
                meta = json.loads(match[3])
            except ValueError as exc:
                raise Error(f'invalid TODO metadata: {match[2]}') from exc
            if not isinstance(meta, dict) or meta.get('status') not in ('pending', 'active', 'done'):
                raise Error(f'invalid TODO status: {match[2]}')
            if (match[1] == 'x') != (meta['status'] == 'done'):
                raise Error(f'TODO checkbox/status mismatch: {match[2]}')
            rows.append({**meta, 'id': match[2], 'text': match[4]})
        if text.count('<!-- doc:todo:') != len(rows):
            raise Error('malformed TODO record')
        if len({row['id'] for row in rows}) != len(rows):
            raise Error('duplicate TODO IDs')
        return rows if include_done else [row for row in rows if row['status'] != 'done']

    def todo_line(self, item):
        meta = {key: value for key, value in item.items() if key not in ('id', 'text')}
        return f"- [{'x' if item['status'] == 'done' else ' '}] <!-- doc:todo:{item['id']} {json.dumps(meta, ensure_ascii=False)} --> {item['text']}"

    def add_todo(self, text, why='', module=None):
        module = module or self.context()[0]['active_module']
        self.record('module', module)
        item = {'id': self.allocate('todo'), 'text': title_text(text), 'why': ' '.join(why.split()), 'module': module,
                'discussion': '', 'origin': self.context()[0].get('active_discussion', ''), 'status': 'pending'}
        path = self.root / 'TODO.md'
        content = path.read_text()
        position = content.index('<details>') if '<details>' in content else len(content)
        content = content[:position].rstrip() + '\n\n' + self.todo_line(item) + '\n\n' + content[position:]
        self.transaction({path: content})
        return item

    def update_todo(self, identifier, operation):
        item = next((item for item in self.todos(True) if item['id'] == identifier), None)
        if not item:
            raise Error(f'unknown TODO {identifier}')
        path = self.root / 'TODO.md'
        content = path.read_text()
        changes = {}
        if operation == 'start':
            if item['status'] == 'done':
                raise Error('TODO is already done')
            if not item['discussion']:
                discussion = self.allocate('discussion')
                item['discussion'] = discussion
                discussion_path = f'discussions/{discussion}.md'
                changes[discussion_path] = doc_text({'id': discussion, 'title': item['text'], 'module': item['module'], 'status': 'open'}, resume_body(item['text']) + f"\nStarted from TODO {identifier}.\n\nMotivation: {item['why']}\n")
            else:
                discussion_path, meta, body = self.record('discussion', item['discussion'])
                meta['status'] = 'open'
                changes[discussion_path] = doc_text(meta, body)
            context, body = self.context()
            context.update(active_module=item['module'], active_discussion=item['discussion'])
            changes['WORK.md'] = doc_text(context, body)
            item['status'] = 'active'
        elif operation == 'done':
            if item['status'] == 'done':
                return item
            item['status'] = 'done'
        pattern = rf'^- \[[ x]\] <!-- doc:todo:{re.escape(identifier)} .*? --> .*\n?'
        replacement = self.todo_line(item) + '\n' if operation == 'start' else ''
        content = re.sub(pattern, lambda _: replacement, content, flags=re.M)
        if operation == 'done':
            content = replace_section(content, 'done', section(content, 'done') + '\n' + self.todo_line(item))
        changes[path] = content
        self.transaction(changes)
        return item if operation != 'delete' else {'deleted': identifier}

    def add_source(self, value, title=None):
        parsed = urlsplit(value)
        local = parsed.scheme not in ('http', 'https')
        data = None
        if local:
            original = Path(value).expanduser().resolve()
            if not original.is_file():
                raise Error('source must be an existing file or HTTP(S) URL')
            data = original.read_bytes()
            identity = 'sha256:' + hashlib.sha256(data).hexdigest()
            title = title or original.name
        else:
            identity = value
            title = title or value
        for item in self.records('source'):
            if item.get('identity') == identity:
                return {**item, 'duplicate': True}
        identifier = self.allocate('source')
        path = f'sources/{identifier}.md'
        attachment = f'sources/files/{identifier}{original.suffix.lower()}' if local else ''
        # Copy original bytes before publishing the note; a failure cannot reference a partial copy.
        if local:
            atomic_write(self.root / attachment, data)
        meta = {'id': identifier, 'title': title_text(title), 'identity': identity, 'original': str(original) if local else value, 'file': attachment}
        reference = f'files/{Path(attachment).name}' if local else value
        body = f'# {title_text(title)}\n\n[Original material]({reference})\n\n## Ideas and constraints\nNot read yet.\n\n## Contradictions and questions\n\n## Source locations\nRecord page, section, or line locations with extracted claims.\n'
        self.transaction({path: doc_text(meta, body)})
        if local:
            self.enqueue([attachment])
        return {**meta, 'path': path}

    def validate_hierarchy(self):
        errors, warnings = [], []
        rows = self.records('module')
        ids = [row.get('id') for row in rows]
        if len(set(ids)) != len(ids):
            errors.append('duplicate module IDs')
        mapping = {row.get('id'): row for row in rows}
        if mapping.get('root', {}).get('path') != 'design.md':
            errors.append('design.md must be the root module')
        for row in rows:
            identifier, parent = row.get('id'), row.get('parent')
            if not isinstance(identifier, str) or not identifier:
                errors.append(f"{row['path']}: missing module ID")
            if not row.get('title'):
                errors.append(f"{row['path']}: missing title")
            if identifier == 'root' and parent != '':
                errors.append('root must have no parent')
            if identifier != 'root' and parent not in mapping:
                errors.append(f"{row['path']}: unknown parent {parent}")
            visited, cursor = set(), identifier
            while cursor in mapping:
                if cursor in visited:
                    errors.append(f"{row['path']}: hierarchy cycle")
                    break
                visited.add(cursor)
                cursor = mapping[cursor].get('parent')
            children = sum(child.get('parent') == identifier for child in rows)
            if children > 5:
                warnings.append(f"{row['path']}: {children} children; consider meaningful grouping")
        return errors, warnings

    def content_files(self):
        return [self.root / name for name in ('design.md', 'WORK.md', 'TODO.md')] + [self.local(row['path']) for kind in ('module', 'discussion', 'source') for row in self.records(kind) if row['path'] != 'design.md']

    def validate(self):
        errors, warnings = self.validate_hierarchy()
        module_ids = {row.get('id') for row in self.records('module')}
        discussions = self.records('discussion')
        discussion_ids = [row.get('id') for row in discussions]
        if len(set(discussion_ids)) != len(discussion_ids):
            errors.append('duplicate discussion IDs')
        for row in discussions:
            if row.get('module') not in module_ids:
                errors.append(f"{row['path']}: missing module")
            if row.get('status') not in ('open', 'closed', 'obsolete'):
                errors.append(f"{row['path']}: invalid discussion status")
            _, body = read_doc(self.local(row['path']))
            try:
                resume = section(body, 'resume')
                if len(resume) > RESUME_LIMIT:
                    errors.append(f"{row['path']}: resume exceeds {RESUME_LIMIT} characters")
                for field in RESUME_FIELDS:
                    if f'### {field}' not in resume:
                        errors.append(f"{row['path']}: missing resume field {field}")
            except Error as exc:
                errors.append(f"{row['path']}: {exc}")
        context, work = self.context()
        if context.get('active_module') not in module_ids:
            errors.append('active module does not exist')
        active = context.get('active_discussion')
        if active:
            selected = next((row for row in discussions if row.get('id') == active), {})
            if selected.get('status') != 'open' or selected.get('module') != context.get('active_module'):
                errors.append('active discussion must be open and belong to active module')
        try:
            if len(section(work, 'brief')) > BRIEF_LIMIT:
                errors.append('working brief exceeds bounded size')
        except Error as exc:
            errors.append(str(exc))
        for item in self.todos(True):
            if item.get('module') not in module_ids:
                errors.append(f"TODO {item['id']}: missing module")
            for key in ('discussion', 'origin'):
                if item.get(key) and item[key] not in discussion_ids:
                    errors.append(f"TODO {item['id']}: missing {key}")
        for path in self.content_files():
            _, body = read_doc(path)
            # Ignore code examples; local file targets only, anchors are handled by the viewer.
            body = re.sub(r'```.*?```|~~~.*?~~~|`[^`]*`', '', body, flags=re.S)
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', body):
                parsed = urlsplit(target.strip('<>'))
                if parsed.scheme or not parsed.path or parsed.netloc:
                    continue
                destination = (path.parent / unquote(parsed.path)).resolve()
                try:
                    destination.relative_to(self.root)
                except ValueError:
                    errors.append(f'{path.name}: link leaves project: {target}')
                    continue
                if not destination.exists():
                    errors.append(f'{path.name}: broken link {target}')
        for row in self.records('source'):
            if row.get('file') and not self.local(row['file']).is_file():
                errors.append(f"{row['path']}: missing source attachment")
        return {'valid': not errors, 'diagnostics': errors, 'warnings': warnings}

    def refresh_navigation(self):
        rows = self.tree()
        changes = {}
        for row in rows:
            path = self.local(row['path'])
            meta, body = read_doc(path)
            children = [child for child in rows if child['parent'] == row['id']]
            links = '\n'.join(f"- [{link_label(child['title'])}]({os.path.relpath(self.local(child['path']), path.parent)})" for child in children)
            if '<!-- doc:children:start -->' in body:
                changes[path] = doc_text(meta, replace_section(body, 'children', links))
        navigation = '- [Project home](README.md)\n' + '\n'.join('  ' * row['depth'] + f"- [{link_label(row['title'])}]({row['path']})" for row in rows)
        navigation += '\n- [TODO](TODO.md)\n- [Working context](WORK.md)\n- [Help](DOC_WORKFLOW.md)'
        sidebar = self.root / '_sidebar.md'
        if sidebar.exists() and '<!-- doc:navigation:start -->' in sidebar.read_text():
            changes[sidebar] = replace_section(sidebar.read_text(), 'navigation', navigation)
        if changes:
            self.transaction(changes)

    def checkpoint(self):
        result = self.validate()
        if not result['valid']:
            raise Error('checkpoint incomplete: ' + '; '.join(result['diagnostics']))
        self.refresh_navigation()
        self.enqueue(self.content_files())
        from .indexing import state
        return {'checkpoint': 'Saved Markdown validated; navigation refreshed; indexing queued.', 'warnings': result['warnings'], 'indexing': state(self.root)}

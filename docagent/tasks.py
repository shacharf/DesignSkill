"""Two-level, progressively planned agenda stored entirely in readable Markdown."""
from __future__ import annotations
import hashlib
import json
import re
import yaml
from .storage import Error, doc_text, section, replace_section, resume_body, title_text, BRIEF_LIMIT

OPEN = ('pending', 'active')
CLOSED = ('done', 'deferred', 'dropped')


def origins(item):
    return ([item['followup_for']] if item.get('followup_for') else []) + item.get('related_origins', [])


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def line(item):
    meta = {key: value for key, value in item.items() if key not in ('id', 'text', '_notes')}
    encoded = json.dumps(meta, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e')
    return f"- [{'x' if item['status'] in CLOSED else ' '}] <!-- doc:todo:{item['id']} {encoded} --> {item['text']}"


def load(project, include_done=False):
    text = (project.root / 'TODO.md').read_text()
    rows = []
    for match in re.finditer(r'^- \[([ x])\] <!-- doc:todo:(t\d+) (\{.*\}) --> (.*)$', text, re.M):
        try:
            meta = json.loads(match[3])
        except ValueError as exc:
            raise Error(f'invalid TODO metadata: {match[2]}') from exc
        if not isinstance(meta, dict) or meta.get('status') not in (*OPEN, *CLOSED):
            raise Error(f'invalid TODO status: {match[2]}')
        if (match[1] == 'x') != (meta['status'] in CLOSED):
            raise Error(f'TODO checkbox/status mismatch: {match[2]}')
        item = {**meta, 'id': match[2], 'text': match[4]}
        item.setdefault('parent', '')  # Existing flat tasks remain top-level topics.
        item.setdefault('followup_for', '')
        item.setdefault('model', '')
        item.setdefault('reason', '')
        item.setdefault('related_origins', [])
        if not isinstance(item['related_origins'], list) or any(not isinstance(value, str) for value in item['related_origins']):
            raise Error(f'invalid TODO related origins: {item["id"]}')
        for field in ('parent', 'followup_for', 'model', 'reason', 'module', 'discussion', 'origin', 'why'):
            if not isinstance(item.get(field), str):
                raise Error(f'invalid TODO {field}: {item["id"]}')
        notes = f'notes:{item["id"]}'
        if f'<!-- doc:{notes}:start -->' in text:
            item['_notes'] = section(text, notes)
        rows.append(item)
    if text.count('<!-- doc:todo:') != len(rows):
        raise Error('malformed TODO record')
    if len({row['id'] for row in rows}) != len(rows):
        raise Error('duplicate TODO IDs')
    return rows if include_done else [row for row in rows if row['status'] in OPEN]


def get(rows, identifier):
    item = next((row for row in rows if row['id'] == identifier), None)
    if item is None:
        raise Error(f'unknown TODO {identifier}')
    return item


def check(project, rows, context=None):
    mapping = {item['id']: item for item in rows}
    errors = []
    for item in rows:
        parent = item['parent']
        if parent and (parent not in mapping or mapping[parent]['parent'] or parent == item['id']):
            errors.append(f"TODO {item['id']}: parent must be a top-level topic")
        if parent in mapping and item['status'] in OPEN and mapping[parent]['status'] in CLOSED:
            errors.append(f"TODO {item['id']}: unfinished work under a closed topic")
        for origin in origins(item):
            if origin not in mapping or origin == item['id']:
                errors.append(f"TODO {item['id']}: missing or invalid follow-up origin")
    if context is None:
        context, _ = project.context()
    current = context.get('active_topic', '')
    active = context.get('active_todo', '')
    if current and (current not in mapping or mapping[current]['parent'] or mapping[current]['status'] != 'active'):
        errors.append('current topic must identify an active top-level TODO')
    if active and (active not in mapping or mapping[active]['status'] != 'active' or
                   (mapping[active]['parent'] or active) != current):
        errors.append('active TODO must belong to the current topic')
    for item in rows:
        if item['status'] == 'active' and not item['parent'] and current and item['id'] != current:
            errors.append('only one top-level topic can be active')
    return errors


def render_item(project, item, staged):
    header = '####' if item['parent'] else '###'
    module_path, module, _ = project.record('module', item['module'])
    pieces = [f'<a id="{item["id"]}"></a>', f'{header} {item["id"]} — {item["text"]}', line(item),
              f'**Status:** {item["status"]}. **Module:** [{module["title"]}]({module_path.relative_to(project.root).as_posix()}).']
    if item.get('why'): pieces.append(f'**Why:** {item["why"]}')
    if item['parent']: pieces.append(f'**Topic:** [{item["parent"]}](#{item["parent"]}).')
    if item.get('discussion'):
        staged_path = next((name for name in staged if str(name).endswith(f'discussions/{item["discussion"]}.md')), None)
        path = project.local(staged_path) if staged_path else project.record('discussion', item['discussion'])[0]
        pieces.append(f'**Brief, discussion, and outcome:** [{item["discussion"]}]({path.relative_to(project.root).as_posix()}).')
    if item.get('origin') and item['origin'] != item.get('discussion'):
        path, _, _ = project.record('discussion', item['origin'])
        pieces.append(f'**Originating discussion:** [{item["origin"]}]({path.relative_to(project.root).as_posix()}).')
    if item.get('model'): pieces.append(f'**Model recommendation:** {item["model"]}')
    if origins(item):
        pieces.append('**Follow-up for:** ' + ', '.join(f'[{origin}](#{origin})' for origin in origins(item)) + '.')
    if item.get('reason'): pieces.append(f'**Reason:** {item["reason"]}')
    pieces.append(f'<!-- doc:notes:{item["id"]}:start -->\n{item.get("_notes", "")}\n<!-- doc:notes:{item["id"]}:end -->')
    return '\n\n'.join(pieces)


def save(project, rows, changes=None):
    """Replace managed records, preserving surrounding prose and per-item notes."""
    changes = dict(changes or {})
    proposed_work = changes.get('WORK.md')
    context = yaml.safe_load(proposed_work.split('---', 2)[1]) if proposed_work else None
    errors = check(project, rows, context)
    if errors:
        raise Error('; '.join(errors))
    text = (project.root / 'TODO.md').read_text()
    if '<!-- doc:agenda:start -->' not in text:
        # Upgrade only recognized legacy task lines, leaving unrelated prose untouched.
        text = re.sub(r'^- \[[ x]\] <!-- doc:todo:t\d+ .* --> .*\n?', '', text, flags=re.M)
        position = text.find('<details>')
        if position < 0: position = len(text)
        text = text[:position].rstrip() + '\n\n<!-- doc:agenda:start -->\n<!-- doc:agenda:end -->\n\n' + text[position:]
    if '<!-- doc:done:start -->' not in text:
        text = text.rstrip() + '\n\n<details>\n<summary>Done</summary>\n\n<!-- doc:done:start -->\n<!-- doc:done:end -->\n\n</details>\n'
    roots = [row for row in rows if not row['parent']]
    def group(root):
        return '\n\n'.join(render_item(project, row, changes) for row in [root, *[item for item in rows if item['parent'] == root['id']]])
    text = replace_section(text, 'agenda', '\n\n'.join(group(row) for row in roots if row['status'] in OPEN))
    text = replace_section(text, 'done', '\n\n'.join(group(row) for row in roots if row['status'] in CLOSED))
    changes['TODO.md'] = text
    project.transaction(changes)


def stage_discussion(project, item, changes):
    if item.get('discussion'):
        return
    identifier = project.allocate('discussion')
    item['discussion'] = identifier
    title = item['text']
    body = resume_body(title)
    body = replace_section(body, 'resume', '\n\n'.join([
        f'### Question\n{title}', f'### Current understanding\n{item.get("why") or "Not established yet."}',
        '### Immediate focus\nRead the topic brief below before discussing.',
        '### Next step\nPrepare or verify the brief using WORK.md and the linked sources.',
        f'### Supporting material\n[Agenda](../TODO.md#{item["id"]}) and [planning summary](../WORK.md).']))
    body += (f'\n## Topic brief\n<!-- doc:topic-brief:start -->\n'
             f'### Question and purpose\n{title}\n\n{item.get("why", "")}\n\n'
             '### Starting point\n_Not prepared: record decisions, assumptions, and unknowns._\n\n'
             '### Watch points\n_Not prepared: identify constraints and scenarios without prescribing an answer._\n\n'
             '### Evidence and dependencies\n_Not prepared: link exact source passages and relevant modules or outcomes._\n\n'
             '### Expected outcome and model recommendation\n_Not prepared: define useful completion and suitable model/effort with reasons._\n'
             '<!-- doc:topic-brief:end -->\n\n## Outcome and handoff\n<!-- doc:outcome:start -->\n<!-- doc:outcome:end -->\n')
    if item['parent']: body += f'\nParent topic: [Agenda {item["parent"]}](../TODO.md#{item["parent"]}).\n'
    if item.get('origin'):
        path, _, _ = project.record('discussion', item['origin'])
        body += f'\nOrigin: [{item["origin"]}]({path.name}).\n'
    changes[f'discussions/{identifier}.md'] = doc_text({'id': identifier, 'title': title, 'module': item['module'], 'status': 'open', 'todo': item['id']}, body)


def add(project, text, why='', module=None, parent='', model='', followup_for=''):
    rows = load(project, True)
    context, _ = project.context()
    if parent:
        ancestor = get(rows, parent)
        if ancestor['parent']: raise Error('only two planning levels are supported')
        if parent != context.get('active_topic') or ancestor['status'] != 'active':
            raise Error('plan subtopics only for the current topic; start its parent first')
        module = module or ancestor['module']
    if followup_for: get(rows, followup_for)
    module = module or context['active_module']
    project.record('module', module)
    item = {'id': project.allocate('todo'), 'text': title_text(text), 'why': ' '.join(why.split()), 'module': module,
            'parent': parent, 'discussion': '', 'origin': context.get('active_discussion', ''),
            'status': 'pending', 'followup_for': followup_for, 'model': ' '.join(model.split()), 'reason': ''}
    rows.append(item)
    changes = {}
    if parent: stage_discussion(project, item, changes)
    save(project, rows, changes)
    return item


def show(project, identifier):
    item = get(load(project, True), identifier)
    result = {**item, 'planning_summary': section(project.context()[1], 'brief')}
    if item['parent']:
        parent = get(load(project, True), item['parent'])
        result['parent_discussion'] = parent.get('discussion', '')
    if item.get('discussion'):
        path, _, body = project.record('discussion', item['discussion'])
        result.update(path=path.relative_to(project.root).as_posix(), body=body)
    return result


def next_item(project):
    rows = load(project, True)
    current = project.context()[0].get('active_topic', '')
    if current:
        parent = get(rows, current)
        children = [row for row in rows if row['parent'] == current]
        for state in ('active', 'pending'):
            candidate = next((row for row in children if row['status'] == state), None)
            if candidate: return candidate
        return {'action': 'finish-topic' if children else 'plan-topic', 'topic': current,
                'message': 'Save the topic outcome and planning summary before advancing.' if children else 'Plan this topic now; future subtopics have not been created.',
                'discussion': parent.get('discussion', '')}
    return next((row for row in rows if not row['parent'] and row['status'] in OPEN), None)


def update(project, identifier, operation, reason='', model=None):
    rows = load(project, True)
    item = get(rows, identifier)
    context, work = project.context()
    changes = {}
    if operation == 'start':
        if item['status'] in CLOSED: raise Error('TODO is already completed or retired')
        topic = item['parent'] or identifier
        current = context.get('active_topic', '')
        if current and current != topic:
            raise Error('finish the current topic and save its handoff before starting another')
        if item['parent'] and current != topic:
            raise Error('start the parent topic before its subtopic')
        if item['parent']:
            for row in rows:
                if row['parent'] == topic and row['status'] == 'active' and row['id'] != identifier:
                    row['status'] = 'pending'
        elif not current:
            for row in rows:
                if not row['parent'] and row['status'] == 'active' and row['id'] != identifier:
                    row['status'] = 'pending'
            context['planning_baseline'] = digest(section(work, 'brief'))
        stage_discussion(project, item, changes)
        if model is not None: item['model'] = title_text(model)
        item['status'] = 'active'
        context.update(active_topic=topic, active_todo=identifier, active_module=item['module'], active_discussion=item['discussion'])
        if f'discussions/{item["discussion"]}.md' not in changes:
            path, meta, body = project.record('discussion', item['discussion'])
            meta['status'] = 'open'
            if '<!-- doc:outcome:start -->' not in body:
                body += '\n## Outcome and handoff\n<!-- doc:outcome:start -->\n<!-- doc:outcome:end -->\n'
            changes[path] = doc_text(meta, body)
    elif operation in ('done', 'defer', 'drop', 'delete'):
        target = {'done': 'done', 'defer': 'deferred', 'drop': 'dropped', 'delete': 'dropped'}[operation]
        if item['status'] == target: return item
        if item['status'] in CLOSED: raise Error('TODO is already completed or retired')
        children = [row for row in rows if row['parent'] == identifier and row['status'] in OPEN]
        if children: raise Error('complete, defer with follow-up, or drop unfinished subtopics first')
        closing_parent = not item['parent'] and context.get('active_topic') == identifier
        if operation == 'done' or closing_parent:
            if operation == 'done' and not item['parent'] and not closing_parent:
                raise Error('start this top-level topic before completing it')
            if not item.get('discussion'): raise Error('start the topic and save its outcome before completing it')
            path, meta, body = project.record('discussion', item['discussion'])
            outcome = section(body, 'outcome')
            if not outcome or outcome.startswith('_Not prepared'):
                raise Error('save a meaningful outcome and handoff in the discussion outcome block first')
            if closing_parent:
                brief = section(work, 'brief')
                if len(brief) > BRIEF_LIMIT: raise Error('planning summary exceeds the working brief limit')
                if digest(brief) == context.get('planning_baseline') or path.relative_to(project.root).as_posix() not in brief:
                    raise Error('update WORK.md planning summary with this topic outcome link before advancing')
        if operation != 'done':
            if not reason.strip(): raise Error('record a reason for deferring or dropping work')
            item['reason'] = title_text(reason)
            if operation == 'defer' and not any(identifier in origins(row) and row['status'] in OPEN for row in rows):
                raise Error('create or link an open follow-up TODO with --follow-up-for before deferring this question')
        item['status'] = target
        if item.get('discussion'):
            path, meta, body = project.record('discussion', item['discussion'])
            meta['status'] = 'closed'
            if operation != 'done':
                body += f'\n## Work disposition\n{target.capitalize()}: {item["reason"]}\n'
            changes[path] = doc_text(meta, body)
        if context.get('active_todo') == identifier:
            context['active_todo'] = ''
        if context.get('active_discussion') == item.get('discussion'):
            context['active_discussion'] = ''
        if context.get('active_topic') == identifier:
            context.update(active_topic='', active_todo='', planning_baseline='')
    else:
        raise Error('unknown TODO operation')
    changes['WORK.md'] = doc_text(context, work)
    save(project, rows, changes)
    return item


def link(project, identifier, origin):
    """Reuse an existing open follow-up without duplicating the question."""
    rows = load(project, True)
    item = get(rows, identifier)
    get(rows, origin)
    if item['status'] not in OPEN:
        raise Error('follow-up must be an open TODO')
    if not item['followup_for']:
        item['followup_for'] = origin
    elif origin not in origins(item):
        item['related_origins'].append(origin)
    save(project, rows)
    return item

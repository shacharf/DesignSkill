"""Behavioral checks for progressive planning, task preservation, and fresh-context handoffs."""
import json
import pytest
from docagent.cli import main
from docagent.storage import Project, Error, read_doc, doc_text, atomic_write, section, replace_section


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv('DOCAGENT_DISABLE_WORKER', '1')
    return Project.initialize(tmp_path / 'design')


def outcome(project, item, text='A stable operation ID prevents duplicate execution; validate capacity next.'):
    row = next(row for row in project.todos(True) if row['id'] == item['id'])
    path, meta, body = project.record('discussion', row['discussion'])
    atomic_write(path, doc_text(meta, replace_section(body, 'outcome', text)))
    return path


def summary(project, path):
    context, body = project.context()
    atomic_write(project.root / 'WORK.md', doc_text(context, replace_section(body, 'brief',
        f'Current direction: use stable operation IDs. Reason: retries can duplicate work. '
        f'Open: capacity limits. Next: plan scaling. [Recovery outcome]({path.relative_to(project.root).as_posix()}).')))


def test_future_topics_have_no_discussions_or_subtopics(project):
    topics = [project.add_todo(f'Topic {i}', f'Purpose {i}') for i in range(9)]
    assert len(project.todos()) == 9
    assert not project.records('discussion')
    with pytest.raises(Error, match='current topic'):
        project.add_todo('Premature detail', parent=topics[1]['id'])
    project.update_todo(topics[0]['id'], 'start')
    current = project.add_todo('Current question', parent=topics[0]['id'])
    assert current['discussion']
    assert len(project.records('discussion')) == 2
    assert all(not row['discussion'] for row in project.todos() if row['id'] in [t['id'] for t in topics[1:]])
    with pytest.raises(Error, match='two planning levels'):
        project.add_todo('Too deep', parent=current['id'])


def test_next_never_advances_parent_automatically(project):
    first = project.add_todo('Recovery')
    second = project.add_todo('Scaling')
    assert project.next_todo()['id'] == first['id']
    project.update_todo(first['id'], 'start')
    assert project.next_todo()['action'] == 'plan-topic'
    child = project.add_todo('Retry rules', parent=first['id'])
    assert project.next_todo()['id'] == child['id']
    with pytest.raises(Error, match='finish the current topic'):
        project.update_todo(second['id'], 'start')
    project.update_todo(child['id'], 'start')
    outcome(project, child)
    project.update_todo(child['id'], 'done')
    assert project.next_todo()['action'] == 'finish-topic'
    assert project.context()[0]['active_topic'] == first['id']
    assert next(row for row in project.todos() if row['id'] == second['id'])['status'] == 'pending'


def test_completion_requires_outcome_and_parent_handoff(project):
    topic = project.add_todo('Recovery')
    project.update_todo(topic['id'], 'start')
    child = project.add_todo('Retry rules', parent=topic['id'])
    with pytest.raises(Error, match='unfinished subtopics'):
        project.update_todo(topic['id'], 'done')
    project.update_todo(child['id'], 'start')
    with pytest.raises(Error, match='meaningful outcome'):
        project.update_todo(child['id'], 'done')
    outcome(project, child)
    project.update_todo(child['id'], 'done')
    path = outcome(project, topic)
    with pytest.raises(Error, match='planning summary'):
        project.update_todo(topic['id'], 'done')
    summary(project, path)
    project.update_todo(topic['id'], 'done')
    assert not project.context()[0]['active_topic']
    assert project.validate()['valid']


def test_old_and_new_questions_survive_deferral(project):
    first = project.add_todo('Recovery')
    second = project.add_todo('Scaling')
    project.update_todo(first['id'], 'start')
    unresolved = project.add_todo('Partition handling', 'Unsettled ownership', parent=first['id'])
    with pytest.raises(Error, match='reason'):
        project.update_todo(unresolved['id'], 'defer')
    with pytest.raises(Error, match='open follow-up'):
        project.update_todo(unresolved['id'], 'defer', 'Requires consistency decision')
    followup = project.add_todo('Choose consistency policy', 'Revisit partition ownership', followup_for=unresolved['id'])
    project.update_todo(unresolved['id'], 'defer', 'Requires consistency decision')
    path = outcome(project, first, f'Recovery approach is recorded; ownership remains open in {followup["id"]}.')
    summary(project, path)
    project.update_todo(first['id'], 'done')
    remaining = project.todos()
    assert [row['id'] for row in remaining] == [second['id'], followup['id']]
    assert not next(row for row in remaining if row['id'] == followup['id'])['discussion']
    archived = next(row for row in project.todos(True) if row['id'] == unresolved['id'])
    assert archived['status'] == 'deferred' and archived['reason']
    assert project.validate()['valid']


def test_replanning_drops_obsolete_work_with_history(project):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    old = project.add_todo('Design lock server', parent=topic['id'])
    with pytest.raises(Error, match='reason'):
        project.update_todo(old['id'], 'drop')
    project.update_todo(old['id'], 'drop', 'Stable IDs remove the need for a lock server')
    new = project.add_todo('Validate operation IDs', parent=topic['id'], followup_for=old['id'])
    assert project.next_todo()['id'] == new['id']
    assert 'Stable IDs remove' in project.show_todo(old['id'])['body']
    assert project.validate()['valid']


def test_fresh_context_reads_summary_prepared_brief_and_prior_outcomes(project):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    child = project.add_todo('Retry rules', 'Prevent duplicate work', parent=topic['id'], model='Lower-cost / medium: bounded analysis')
    path, meta, body = project.record('discussion', child['discussion'])
    prepared = 'Question: when can retry run?\nStarting point: stable IDs.\nWatch: restart races.\nEvidence: [Main ideas](../design.md).\nExpected outcome: retry rule.'
    atomic_write(path, doc_text(meta, replace_section(body, 'topic-brief', prepared)))
    project.update_todo(child['id'], 'start')
    resumed = Project(project.root)
    handoff = resumed.show_todo(child['id'])
    assert prepared in handoff['body']
    assert handoff['parent_discussion']
    assert handoff['planning_summary'] == section(resumed.context()[1], 'brief')
    outcome(resumed, child); resumed.update_todo(child['id'], 'done')
    parent_path = outcome(resumed, topic)
    summary(resumed, parent_path)
    resumed.update_todo(topic['id'], 'done')
    next_topic = resumed.add_todo('Scaling'); resumed.update_todo(next_topic['id'], 'start')
    next_handoff = Project(project.root).show_todo(next_topic['id'])
    assert 'Reason: retries can duplicate work' in next_handoff['planning_summary']
    assert str(parent_path.relative_to(project.root)) in next_handoff['planning_summary']


def test_upgrade_legacy_tasks_preserves_ids_order_prose_and_links(project):
    d = project.create_discussion('Old discussion')['id']
    meta = {'why': 'Keep this rationale', 'module': 'root', 'discussion': d, 'origin': '', 'status': 'pending'}
    text = '# My backlog\n\nMy custom introduction.\n\n'
    for identifier in ('t014','t003'):
        text += f'- [ ] <!-- doc:todo:{identifier} {json.dumps(meta)} --> Old {identifier}\n'
    text += '\n<details>\n<summary>Done</summary>\n\nA custom archive note.\n\n<!-- doc:done:start -->\n<!-- doc:done:end -->\n</details>\n'
    (project.root / 'TODO.md').write_text(text)
    assert not any(row['parent'] for row in project.todos())
    added = project.add_todo('New topic')
    assert added['id'] == 't015'
    assert [row['id'] for row in project.todos()] == ['t014','t003','t015']
    upgraded = (project.root / 'TODO.md').read_text()
    assert 'My custom introduction.' in upgraded and 'A custom archive note.' in upgraded
    assert '**Why:** Keep this rationale' in upgraded
    assert '(discussions/d001.md)' in upgraded
    project.update_todo('t014','start')
    assert '<!-- doc:outcome:start -->' in project.record('discussion',d)[2]
    assert project.validate()['valid']


def test_notes_and_origins_are_visible_and_preserved(project):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    child = project.add_todo('Retry rules', 'Must survive restart', parent=topic['id'])
    path = project.root / 'TODO.md'
    path.write_text(replace_section(path.read_text(), f'notes:{child["id"]}', 'User note: consider slow workers.'))
    project.add_todo('Future topic')
    project.checkpoint()
    text = path.read_text()
    assert 'User note: consider slow workers.' in text
    assert '**Why:** Must survive restart' in text
    assert '**Originating discussion:**' in text
    assert '#### ' + child['id'] in text


def test_invalid_parent_does_not_disappear_during_mutation(project):
    project.add_todo('Recovery')
    path = project.root / 'TODO.md'
    path.write_text(path.read_text().replace('"parent": ""', '"parent": "t999"'))
    before = path.read_bytes()
    with pytest.raises(Error, match='parent must'):
        project.add_todo('Another topic')
    assert path.read_bytes() == before


def test_todo_start_recovery_preserves_child_and_selection(project, monkeypatch):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    child = project.add_todo('Retry rules', parent=topic['id'])
    before = len(project.records('discussion'))
    enqueue = project.enqueue
    monkeypatch.setattr(project,'enqueue',lambda paths: (_ for _ in ()).throw(OSError('interrupted')))
    with pytest.raises(OSError): project.update_todo(child['id'],'start')
    monkeypatch.setattr(project,'enqueue',enqueue)
    with project.lock(): project.update_todo(child['id'],'start')
    assert len(project.records('discussion')) == before
    assert project.status()['active_todo'] == child['id']


def test_cli_topic_lifecycle_and_metadata_validation(project,capsys):
    prefix = ['--project',str(project.root)]
    assert main(prefix + ['todo','Recovery','--why','Avoid duplicates','--json']) == 0
    root=json.loads(capsys.readouterr().out)['id']
    assert main(prefix + ['todo','--start',root]) == 0
    capsys.readouterr()
    assert main(prefix + ['todo','Retry rules','--parent',root,'--model','Lower-cost / medium','--json']) == 0
    child=json.loads(capsys.readouterr().out)['id']
    assert main(prefix + ['todo','--show',child]) == 0
    assert 'Topic brief' in capsys.readouterr().out
    assert main(prefix + ['todo','--done',child,'--json']) == 2
    assert 'outcome' in json.loads(capsys.readouterr().err)['error']
    assert main(prefix + ['todo','--next','--model','Ignored']) == 2
    capsys.readouterr()


def test_existing_successor_can_be_reused_without_duplication(project):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    old = project.add_todo('Partition policy', parent=topic['id'])
    existing = project.add_todo('Consistency policy', 'Review after recovery')
    before = len(project.todos(True))
    project.link_todo(existing['id'], old['id'])
    project.update_todo(old['id'], 'defer', 'Covered by the existing consistency topic')
    assert len(project.todos(True)) == before
    assert next(row for row in project.todos() if row['id'] == existing['id'])['followup_for'] == old['id']
    assert project.validate()['valid']


def test_retiring_current_parent_also_needs_a_handoff(project):
    topic = project.add_todo('Lock server'); project.update_todo(topic['id'], 'start')
    with pytest.raises(Error, match='outcome'):
        project.update_todo(topic['id'], 'drop', 'Architecture changed')
    path = outcome(project, topic, 'Locking is superseded by operation IDs. Reassess retries next.')
    with pytest.raises(Error, match='planning summary'):
        project.update_todo(topic['id'], 'drop', 'Architecture changed')
    summary(project, path)
    project.update_todo(topic['id'], 'drop', 'Architecture changed')
    assert not project.context()[0]['active_topic']


def test_one_existing_followup_can_cover_several_unresolved_questions(project):
    topic = project.add_todo('Recovery'); project.update_todo(topic['id'], 'start')
    first = project.add_todo('Ownership during partition', parent=topic['id'])
    second = project.add_todo('Ownership after restart', parent=topic['id'])
    successor = project.add_todo('Consistency and ownership policy')
    project.link_todo(successor['id'], first['id'])
    project.link_todo(successor['id'], second['id'])
    project.link_todo(successor['id'], second['id'])
    project.update_todo(first['id'], 'defer', 'Requires the consistency decision')
    project.update_todo(second['id'], 'defer', 'Requires the same consistency decision')
    row = next(row for row in project.todos() if row['id'] == successor['id'])
    assert row['followup_for'] == first['id']
    assert row['related_origins'] == [second['id']]
    assert project.validate()['valid']

import json
from pathlib import Path
import pytest
from docagent.storage import Project, Error, atomic_write, read_doc, doc_text, replace_section
from docagent.cli import main


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv('DOCAGENT_DISABLE_WORKER', '1')
    return Project.initialize(tmp_path / 'design')


def test_initialize_and_no_research_migration(tmp_path, project):
    assert project.status()['active_module'] == 'root'
    assert project.validate()['valid']
    assert not (project.root / 'paper.md').exists()
    assert Project.initialize(project.root).status()['active_module'] == 'root'
    old = tmp_path / 'old'; (old / '.rs').mkdir(parents=True)
    with pytest.raises(Error, match='research project'): Project.initialize(old)
    assert not (old / '.docagent').exists()


def test_initialization_preserves_existing_content(tmp_path):
    (tmp_path / 'design.md').write_text('existing')
    with pytest.raises(Error, match='overwrite'): Project.initialize(tmp_path)
    assert (tmp_path / 'design.md').read_text() == 'existing'
    assert not (tmp_path / '.docagent').exists()


def test_hierarchy_navigation_move_and_cycles(project):
    a = project.create_module('Coordination')['id']
    b = project.create_module('Assignment', a)['id']
    assert [r['depth'] for r in project.tree()] == [0, 1, 2]
    assert '(m002.md)' in (project.root / 'modules/m001.md').read_text()
    with pytest.raises(Error, match='cycle'): project.move_module(a, b)
    project.move_module(b, 'root')
    assert [r['depth'] for r in project.tree()] == [0, 1, 1]
    assert '(m002.md)' not in (project.root / 'modules/m001.md').read_text()
    assert project.validate()['valid']
    assert '(modules/m002.md)' in (project.root / 'design.md').read_text()


def test_warning_does_not_reject_six_children(project):
    for i in range(6): project.create_module(f'Module {i}')
    result = project.validate()
    assert result['valid'] and '6 children' in result['warnings'][0]


def test_todo_lifecycle_retains_reason_and_idempotent_discussion(project):
    module = project.create_module('Coordination')['id']
    todo = project.add_todo('Recovery?', 'Avoid duplicate work', module)
    started = project.update_todo(todo['id'], 'start')
    again = project.update_todo(todo['id'], 'start')
    assert started == again
    assert len(project.records('discussion')) == 1
    assert project.todos()[0]['status'] == 'active'
    assert 'Avoid duplicate work' in project.record('discussion', started['discussion'])[2]
    project.update_todo(todo['id'], 'done')
    assert project.todos() == []
    assert project.todos(True)[0]['why'] == 'Avoid duplicate work'
    content = (project.root / 'TODO.md').read_text()
    assert content.index('[x]') > content.index('<summary>Done</summary>')
    project.update_todo(todo['id'], 'done')
    assert len(project.todos(True)) == 1
    assert project.add_todo('Next')['id'] != todo['id']
    assert project.validate()['valid']


def test_selection_and_close_preserve_module_consistency(project):
    m = project.create_module('Control')['id']
    d = project.create_discussion('Question', m)['id']
    project.select('discussion', d)
    assert project.status()['active_module'] == m
    project.select('module', 'root')
    assert project.status()['active_discussion'] == ''
    project.select('discussion', d)
    project.discussion_state(d, 'closed')
    assert project.status()['active_discussion'] == ''
    with pytest.raises(Error, match='reopen'): project.select('discussion', d)


def test_sources_are_preserved_and_deduplicated(project, tmp_path):
    original = tmp_path / 'notes.md'; original.write_bytes(b'# Rough ideas\n\xff')
    source = project.add_source(str(original))
    assert (project.root / source['file']).read_bytes() == original.read_bytes()
    assert project.add_source(str(original))['id'] == source['id']
    assert project.add_source(str(original))['duplicate']
    url = project.add_source('https://example.org/design', 'Remote reference')
    assert not url['file']
    assert project.validate()['valid']


def test_checkpoint_validates_before_refresh(project):
    project.create_module('Control')
    p = project.root / 'modules/m001.md'
    p.write_text(p.read_text() + '\n[Missing](absent.md)\n')
    assert not project.validate()['valid']
    with pytest.raises(Error, match='broken link'): project.checkpoint()
    p.write_text(p.read_text().replace('[Missing](absent.md)', '`[Example](absent.md)`'))
    assert project.checkpoint()['checkpoint']


def test_resume_excerpt_and_checkpoint_limit(project):
    d = project.create_discussion('Question')['id']; project.select('discussion', d)
    path, meta, body = project.record('discussion', d)
    atomic_write(path, doc_text(meta, replace_section(body, 'resume', 'x' * 6000)))
    assert project.status()['discussion']['resume']['excerpt']
    with pytest.raises(Error, match='resume exceeds'): project.checkpoint()


def test_journal_recovers_interrupted_todo_start(project, monkeypatch):
    todo = project.add_todo('Recovery')
    original = project.enqueue
    monkeypatch.setattr(project, 'enqueue', lambda paths: (_ for _ in ()).throw(OSError('interrupted')))
    with pytest.raises(OSError): project.update_todo(todo['id'], 'start')
    assert (project.root / '.docagent/transaction.json').exists()
    monkeypatch.setattr(project, 'enqueue', original)
    with project.lock(): result = project.update_todo(todo['id'], 'start')
    assert result['status'] == 'active'
    assert len(project.records('discussion')) == 1
    assert not (project.root / '.docagent/transaction.json').exists()


def test_validate_manual_cycle_and_duplicate_todo(project):
    project.create_module('A'); project.create_module('B', 'm001')
    path, meta, body = project.record('module', 'm001'); meta['parent'] = 'm002'
    atomic_write(path, doc_text(meta, body))
    assert any('cycle' in e for e in project.validate()['diagnostics'])
    with pytest.raises(Error, match='cycle'): project.tree()
    todo = project.add_todo('One')
    path = project.root / 'TODO.md'
    path.write_text(path.read_text() + project.todo_line(todo) + '\n')
    with pytest.raises(Error, match='duplicate TODO'): project.todos()


def test_cli_help_outside_project_and_json(project, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(['help']) == 0
    assert 'No model' not in capsys.readouterr().err
    assert main(['module', 'create', 'Coordinator', '--project', str(project.root), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['id'] == 'm001'
    assert main(['--project', str(project.root), 'module', 'select', 'missing', '--json']) == 2
    assert 'error' in json.loads(capsys.readouterr().err)
    assert main(['--project', str(project.root), 'validate', '--json']) == 0
    assert json.loads(capsys.readouterr().out)['valid']


def test_cli_init_packaged_assets(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('DOCAGENT_DISABLE_WORKER', '1')
    root = tmp_path / 'new'
    assert main(['init', str(root), '--skip-gno']) == 0
    assert (root / 'index.html').exists()
    assert (root / 'DOC_WORKFLOW.md').exists()
    assert main(['--project', str(root), 'checkpoint']) == 0


def test_read_commands_do_not_sync_or_mutate_content(project, monkeypatch):
    from docagent import indexing
    monkeypatch.setattr(indexing, '_run', lambda *args: pytest.fail('read invoked GNO'))
    before = {p: p.read_bytes() for p in project.content_files()}
    project.status(); project.tree(); project.todos(); project.validate()
    assert before == {p: p.read_bytes() for p in project.content_files()}

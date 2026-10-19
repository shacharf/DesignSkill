import json
from pathlib import Path
import pytest
from scripts.install_project import install
from docagent.storage import Project


@pytest.fixture(autouse=True)
def no_worker(monkeypatch):
    monkeypatch.setenv('DOCAGENT_DISABLE_WORKER', '1')
    # Avoid probing real host processes in unit tests.
    monkeypatch.setattr('scripts.install_project.shutil.which', lambda name: None)


def test_both_hosts_reinstall_preserves_content(tmp_path):
    root = tmp_path / 'project'
    install(root, 'codex', True)
    module = Project(root).create_module('Human edits')
    path = root / module['path']; path.write_text(path.read_text() + '\nCustom prose.\n')
    original = path.read_bytes()
    install(root, 'claude', True); install(root, 'codex', True)
    assert path.read_bytes() == original
    for host in ('.agents', '.claude'):
        assert len(list((root / host / 'skills').glob('*/SKILL.md'))) == 6
        assert (root / host / 'skills/doc-write/references/reading-contract.md').exists()
    assert Project(root).validate()['valid']


def test_modified_skill_conflict_no_partial_install(tmp_path):
    install(tmp_path, 'codex', True)
    skill = tmp_path / '.agents/skills/doc-design/SKILL.md'
    skill.write_text('my instructions')
    before = (tmp_path / 'design.md').read_bytes()
    with pytest.raises(ValueError, match='modified installed'): install(tmp_path, 'codex', True)
    assert skill.read_text() == 'my instructions'
    assert (tmp_path / 'design.md').read_bytes() == before


def test_preserve_custom_viewer_and_surrounding_instructions(tmp_path):
    (tmp_path / 'AGENTS.md').write_text('My rules.\n')
    (tmp_path / 'index.html').write_text('Custom viewer')
    install(tmp_path, 'codex', True)
    assert (tmp_path / 'AGENTS.md').read_text().startswith('My rules.')
    assert (tmp_path / 'index.html').read_text() == 'Custom viewer'
    p = tmp_path / '_sidebar.md'; p.write_text('Custom sidebar\n')
    install(tmp_path, 'codex', True)
    assert p.read_text() == 'Custom sidebar\n'


def test_conflicting_claude_settings_preserved(tmp_path):
    (tmp_path / '.claude').mkdir()
    settings = tmp_path / '.claude/settings.json'
    settings.write_text('{"respondToBashCommands": true, "custom": 1}')
    before = settings.read_bytes()
    result = install(tmp_path, 'claude', True)
    assert settings.read_bytes() == before
    assert result['startup'] == 'claude --settings .docagent/claude-settings.json'


def test_missing_gno_and_legacy_fail_before_writes(tmp_path):
    root = tmp_path / 'new'
    with pytest.raises(ValueError, match='GNO'): install(root, 'codex')
    assert not root.exists()
    root.mkdir(); (root / '.rs').mkdir()
    with pytest.raises(ValueError, match='research project'): install(root, 'codex', True)
    assert not (root / '.docagent').exists()


def test_skill_contract_and_packaged_assets_match():
    root = Path(__file__).resolve().parents[1]
    contracts = [p.read_text() for p in (root / 'skills').glob('*/references/reading-contract.md')]
    assert len(contracts) == 3 and len(set(contracts)) == 1
    assert (root / 'README.md').read_bytes() == (root / 'docagent/assets/DOC_WORKFLOW.md').read_bytes()
    assert (root / 'index.html').read_bytes() == (root / 'docagent/assets/index.html').read_bytes()

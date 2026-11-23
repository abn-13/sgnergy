#!/usr/bin/env python3
"""Scoped SGnergy PreToolUse gate; validates locally and never sends mail."""
import copy
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].resolve()
sys.path.insert(0, str(ROOT / 'pipeline'))


def check(event):
    cwd = Path(event.get('cwd') or '/').resolve()
    if not cwd.is_relative_to(ROOT):
        return
    args = event.get('tool_input') or {}
    name = str(event.get('tool_name', '')).lower()
    # Lazy MCP wrappers carry the real identifier and arguments in their input.
    while isinstance(args, dict) and isinstance(args.get('arguments'), dict):
        name = str(args.get('toolName', args.get('name', name))).lower()
        args = args['arguments']
    command = str(args.get('command', ''))
    # Only explicit pipeline operations and client delivery artifacts are gated.
    tokens = shlex.split(command) if command else []
    operation = name.rsplit('__', 1)[-1]
    linked = args.get('report_content_path', args.get('reportContentPath'))
    path = args.get('file_path', args.get('filePath', args.get('path', '')))
    target = (cwd / str(path)).resolve() if path else None
    artifact = bool(target and target.is_relative_to(ROOT / 'clients')
                    and len(target.relative_to(ROOT / 'clients').parts) == 3
                    and target.name in {'report_content.json', 'report.pdf', 'email_draft.md', 'email_draft.txt', 'report_delivery_email.md'})
    pipeline = any((cwd / t).resolve() in {ROOT / 'pipeline' / 'make_report.py', ROOT / 'pipeline' / 'report_pdf.py'}
                   for t in tokens if t.endswith('.py'))
    draft_operation = bool(re.fullmatch(r'(?:.*[_-])?(?:draft[_-]?(?:mail|email)|create[_-]?(?:mail|email)[_-]?draft|create[_-]?draft)', operation))
    delivery_draft = draft_operation and bool(linked or args.get('client'))
    operation_tokens = [operation] + [Path(t).name.lower() for t in tokens if not any(c.isspace() for c in t)]
    email_send = any(re.fullmatch(r'(?:.*[_-])?send[_-]?(?:mail|email|message)(?:\.py)?|sendmail|smtp(?:\.py)?|sendmessage', t) for t in operation_tokens)
    email_send = email_send or ('send' in operation_tokens and any(t in {'mail', 'email', 'outlook', 'dws'} for t in operation_tokens))
    if email_send:
        raise ValueError('SGnergy: email sending is blocked; drafts only.')
    mutation = operation in {'write', 'edit', 'create', 'write_file', 'edit_file', 'create_file'}
    if not (pipeline or delivery_draft or artifact and mutation):
        return
    identity = operation
    if delivery_draft or artifact and target.name in {'email_draft.md', 'email_draft.txt', 'report_delivery_email.md'}:
        identity += ' draft'
    elif pipeline:
        identity += ' make_report report'
    elif artifact:
        identity += ' report'
    client = str(args.get('client', 'demo-office-2'))
    month = str(args.get('month', '2026-09'))
    linked = args.get('report_content_path', args.get('reportContentPath'))
    if target and target.is_relative_to(ROOT / 'clients'):
        parts = target.relative_to(ROOT / 'clients').parts
        if len(parts) >= 3:
            client, month = parts[:2]
    if command:
        tokens = shlex.split(command)
        for flag, field in [('--client', 'client'), ('--month', 'month'), ('--content', 'linked')]:
            if flag in tokens:
                value = tokens[tokens.index(flag) + 1]
                if field == 'client':
                    client = value
                elif field == 'month':
                    month = value
                else:
                    linked = value
    directory = ROOT / 'clients' / client / month
    if not directory.resolve().is_relative_to(ROOT / 'clients'):
        raise ValueError('SGnergy: invalid client/month path.')
    content = args.get('content', args.get('body', args.get('new_string', args.get('newString'))))
    if target and target.name == 'report_content.json' and 'edit' not in name and content is not None:
        document = json.loads(content)
    else:
        source = (cwd / str(linked)).resolve() if linked else directory / 'report_content.json'
        document = json.loads(source.read_text())
    validate(document, directory)
    # Actual draft wording must pass too, not merely its linked report.
    if 'draft' in identity or target and 'draft' in str(target).lower():
        if content is None:
            raise ValueError('SGnergy: opaque draft operation blocked; supply body and linked report_content_path.')
        draft = copy.deepcopy(document)
        draft['sections'] = [{'heading': str(args.get('subject', 'Draft')), 'paragraphs': [str(content)]}]
        draft['disclosure'] = ''
        validate(draft, directory)
    elif 'edit' in name or pipeline and not any(Path(t).name == 'make_report.py' for t in tokens):
        raise ValueError('SGnergy: opaque report edit/render blocked; use the validated make_report.py pipeline.')


def validate(document, directory):
    import common
    import validate_report
    csv = directory / 'meter_data.csv'
    errors = validate_report.validate(document, common.load_csv(csv),
        common.load_client(directory.parent)['gfa_m2'], common.load_config(), csv)
    if errors:
        raise ValueError('SGnergy report validator: ' + '; '.join(errors))


if __name__ == '__main__':
    try:
        check(json.load(sys.stdin))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

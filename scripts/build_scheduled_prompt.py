#!/usr/bin/env python3
"""Build a private, standalone Scheduled Tasks prompt; never schedule or query."""
import argparse
import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path


def build(profile, checkpoint, language='English', policy='changes_only'):
    if not isinstance(profile, dict):
        raise ValueError('config must be a JSON object')
    for key in ('first_name', 'last_name', 'exam_no', 'title_code', 'list_no'):
        if not isinstance(profile.get(key), str) or not profile[key].strip():
            raise ValueError(key + ' must be a nonempty string')
    if 'mi' not in profile or (profile['mi'] is not None and not isinstance(profile['mi'], str)):
        raise ValueError('mi must be explicitly provided as a string or null')
    if not profile['exam_no'].isdigit() or not profile['title_code'].isdigit():
        raise ValueError('exam_no and title_code must be digit strings')
    try:
        number = Decimal(profile['list_no'])
        if not number.is_finite() or number < 0:
            raise ValueError('list_no must be a finite nonnegative decimal string')
    except InvalidOperation:
        raise ValueError('list_no must be an exact decimal string') from None
    if policy not in ('changes_only', 'digest'):
        raise ValueError('unsupported notification policy')
    for label, value in (('checkpoint', checkpoint), ('language', language)):
        if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
            raise ValueError(label + ' must be a nonempty single line')
    template = (Path(__file__).resolve().parent.parent / 'references' / 'scheduled-task-prompt.md').read_text()
    values = {'PRIVATE_PROFILE_JSON': json.dumps(profile, ensure_ascii=False, indent=2),
              'CHECKPOINT_REFERENCE': json.dumps(checkpoint), 'OUTPUT_LANGUAGE': json.dumps(language),
              'NOTIFICATION_POLICY': policy}
    # Replace original markers in one pass so profile text is never reinterpreted.
    import re
    return re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: values[m[1]], template)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--checkpoint-ref', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--language', default='English')
    parser.add_argument('--policy', choices=('changes_only', 'digest'), default='changes_only')
    args = parser.parse_args()
    tmp = None
    try:
        if args.config.resolve() == args.output.resolve():
            raise ValueError('output must not overwrite the config')
        prompt = build(json.loads(args.config.read_text()), args.checkpoint_ref, args.language, args.policy)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=args.output.parent, delete=False) as stream:
            tmp = stream.name
            os.chmod(tmp, 0o600)
            stream.write(prompt)
        os.replace(tmp, args.output)
        tmp = None
    except (OSError, ValueError, KeyError) as error:
        # Do not echo private config values or parser excerpts.
        parser.exit(2, 'Prompt generation failed (' + type(error).__name__ + '); check private config and output path.\n')
    finally:
        if tmp:
            os.unlink(tmp)


if __name__ == '__main__':
    main()

# ChatGPT Scheduled Tasks

For users without GitHub integration or Skill installation, use the complete copy-and-paste [START-HERE.md](../START-HERE.md). Do not require repository fetching during setup or execution. Workflow version: 2026-10-25.1; preserve the existing private task/checkpoint on upgrades.

## Default path

Use a standalone task prompt, not a shell command or “read this GitHub repo” as the whole task. Default to English; preserve a user's explicitly saved language override. Python stays optional. Do not claim that every scheduled host has direct HTTPS, arbitrary tools, private writable state or silent notification support.

1. Reuse the already confirmed candidate/settings. For first-time setup only, follow onboarding. Offer minimum/all ties, agency focus, monthly batches, annual history and material-change alerts; skip values already supplied.
2. Complete [scheduled-task-prompt.md](scheduled-task-prompt.md) **privately** with a JSON identity/profile, an actually accessible private checkpoint reference (or `none`), notification policy and language. Embed the whole filled prompt in the task. Keep exam/List No quoted. Never commit the filled copy.
3. Preflight the direct official endpoints and checkpoint read/write using the actual available tools. Test in a normal chat first, while recognizing that this does not guarantee scheduled-runtime capabilities. No shell/Python/attachment is mandatory. If no direct tool can retrieve complete official data, label verification incomplete. If state is unavailable, explain that changes-only alerts cannot be reliable; do not silently replace them with a digest.
4. For an existing task, update its instructions through supported scheduling tools while retaining its ID, schedule, private identity, checkpoint reference, observation history and notified events. Do not create another task. A request to edit repository documentation alone does not authorize changing live schedules. Only claim task creation/update after host success.
5. At runtime fetch and compare, then persist to the same supported private checkpoint item. Never depend on a scratch path surviving another run; use actual host-provided storage or accessible dated task-run records. A profile/prompt is configuration, not state. No state reference is a baseline only on genuinely first setup; lost prior access is a comparison failure. Preserve pending delivery events; runtime silence is host-specific.

## Optional private prompt builder

If Python is available during setup, generate the filled prompt locally; scheduled execution itself need not use Python:

```bash
python3 scripts/build_scheduled_prompt.py \
  --config /private/config.json \
  --checkpoint-ref 'PRIVATE_PERSISTENT_ITEM_REFERENCE' \
  --output /private/scheduled-task.txt
```

Use the same exact identity config as the optional monitor. All six identity values including `mi` must be explicitly present; null MI is accepted. The builder checks configuration syntax only: it does not verify the identity, network, checkpoint access or create/update any task. It atomically writes an owner-only private prompt. Default language is English, policy changes_only. Pass `--language Chinese` only for an explicit preference, or `--policy digest` for an agreed digest. A value of `none` is allowed for initial baseline preparation, not a promise of durable monitoring.

## Platform reference

Official OpenAI documentation: https://learn.chatgpt.com/docs/automations (checked 2026-10-24). Tool access and context depend on task setup; invoke the Skill explicitly where supported. A public Skill/repository is not itself a running Scheduled Task. Keep this implementation's source/completeness/state requirements even when the platform cannot meet them.

# Tooling

Adopted skills, hooks, MCP servers and plugins for this project.

### P-001 — mattpocock-skills@claude-plugins-official
**Date:** 2026-09-25
**Type:** plugin
**Approved by:** owner
**Why:** Fills gaps devsystem doesn't cover: `prototype` (quick UI direction tests), `tdd`
(agent routing/context-switch logic test-first), `diagnosing-bugs`, `grill-me`. Enabled at
project scope only (`.claude/settings.json`) and disabled at user scope: the plugin toggles
as a whole (37 skills), so user scope loaded every description into every project and risked
auto-invoking the wrong skill (its `handoff` collides with devsystem's `/handoff`). Not used:
`to-spec`, `implement`, `handoff`, `code-review` — devsystem owns those. Rule recorded in
`CLAUDE.md` → Skills.

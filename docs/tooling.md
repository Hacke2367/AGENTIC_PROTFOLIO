# Tooling

Adopted skills, hooks, MCP servers and plugins for this project.

### P-001 — mattpocock-skills@claude-plugins-official
**Date:** 2026-09-25
**Type:** plugin
**Approved by:** owner
**Why:** Fills gaps devsystem doesn't cover: `prototype` (quick UI direction tests), `tdd`
(agent routing/context-switch logic test-first), `diagnosing-bugs`, `grilling`. Enabled at
project scope only (`.claude/settings.json`) and disabled at user scope: the plugin toggles
as a whole (37 skills), so user scope loaded every description into every project and risked
auto-invoking the wrong skill (its `handoff` collides with devsystem's `/handoff`). Not used:
`to-spec`, `implement`, `handoff`, `code-review` — devsystem owns those. Rule recorded in
`CLAUDE.md` → Skills.

### P-002 — frontend-design@claude-plugins-official
**Date:** 2026-09-26
**Type:** plugin
**Approved by:** owner
**Why:** Design skill (`frontend-design:frontend-design`) for this project's UI work: aesthetic
direction, typography, layout and self-critique. Used for the step 02 prototype rounds; the
owner picked variant D (Geist + electric blue agent console) and wants it polished to a premium
finish. Already enabled at user scope; also enabled at project scope (`.claude/settings.json`)
so the dependency is explicit. Rule recorded in `CLAUDE.md` → Skills.

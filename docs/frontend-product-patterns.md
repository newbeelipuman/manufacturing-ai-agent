# Frontend Product Patterns

This file collects reusable frontend product patterns found during MVP hardening.
Keep examples factual and small so they can later become Codex skills or checklists.

## Frequency-Based Secondary Navigation

Use secondary navigation when one top-level module contains multiple views with
different usage frequencies.

Example:

```text
部署状态
  日志查看
  服务状态
  部署报告
```

Decision rule:

- 高频查看内容 should become the default secondary view and receive the largest
  content area. Example: deployment logs.
- 中频查看内容 can stay in the same top-level module, but should not compete
  with the default high-frequency workflow. Example: service status cards.
- 低频查看内容 should move behind a secondary item or lower-priority region.
  Example: deployment report file references.

Why this works:

- It keeps the primary workflow visible without scrolling through low-frequency
  supporting information.
- It makes the left navigation communicate the product structure instead of
  forcing users to discover sections inside a long page.
- It matches common admin-console patterns used by cloud consoles, DevOps tools,
  CI/CD dashboards, and observability products.

Implementation notes:

- Keep the top-level nav item active while rendering an indented secondary nav.
- Default the top-level item to the highest-frequency secondary view.
- Use smaller typography and a subtle left border for secondary nav items.
- Do not translate raw log content or file paths when they are operational
  evidence. Translate only UI labels and status words.
- For log viewers, prefer vertical scrolling and wrapped long lines over
  horizontal scrolling unless exact column alignment is the core task.

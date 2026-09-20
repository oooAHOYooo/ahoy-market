# Release Types

Determine the workflow based on the magnitude of the release.

## Major / Minor Releases (e.g., v1.1.0, v2.0.0)
- **Scope:** Introduces new features, significant architectural changes, or large UI updates.
- **Workflow Requirements:**
  - Full platform checklist must be completed for ALL supported platforms (iOS, Android, Mac, Linux).
  - Release notes should be highly detailed, featuring a "Highlights" section at the top.
  - Q&A generation must focus heavily on how new features change user workflows.

## Patch / Hotfix Releases (e.g., v1.0.8.1, v1.0.8.2)
- **Scope:** Fixes specific, critical bugs or regressions in a very recently deployed version.
- **Workflow Requirements:**
  - Identify exactly which platforms are affected. It may not be necessary to release on all platforms if the bug is isolated (e.g., an iOS-only UI bug).
  - Keep the release notes extremely brief. Focus ONLY on what was broken and how it is fixed.
  - Q&A should focus on "How do I know if I was affected by this bug?" and "Do I need to force update?"
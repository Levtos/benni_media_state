# CLAUDE.md - media-state

## GitLab Workflow

- GitLab project `ha-platform/control` is the central workflow truth.
- Relevant work requires a GitLab issue in `ha-platform/control`.
- Before work starts, read the issue description and all issue notes.
- Document current state, decisions, scope changes, tests, commits, merge requests, blockers, and completion in the issue.
- Code changes happen in the matching GitLab repository. `origin` must point to GitLab.
- GitHub is only the public distribution and HACS mirror. Do not develop directly on GitHub and do not push manually to GitHub.
- Release flow: create version bumps and tags in GitLab; GitLab CI triggers the configured GitLab push mirror and verifies mirror status plus GitHub tag arrival. GitHub Actions creates or detects the published GitHub Release and verifies the GitHub tag/release plus manifest version. Agents do not push to GitHub manually, create GitHub Releases manually, or run `gh release` for HACS repos.
- Plane is historical only and is not used for active work.
- Forgejo is out of service; do not use it and do not treat it as a blocker.
- Full rules live in `ha-platform/control/AGENTS.md`, `ha-platform/control/CLAUDE.md`, and `ha-platform/control/docs/workflow/`.

## Safety

- Do not put secrets in issues, commits, logs, or reports.
- Do not touch production Home Assistant systems without explicit approval.
- No admin, delete, runner, or bulk actions without explicit approval.

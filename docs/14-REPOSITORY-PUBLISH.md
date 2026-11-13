**Publication status (2026-11-13):** Private repository created and v0.1 documentation committed to `main`. The creation and push steps below are historical setup guidance. Branch protection and secret scanning remain to be verified.

# Private GitHub Repository Bootstrap

## Desired repository
- Owner: linked GitHub user `vinodkumar-Hegde` (confirmed via connected GitHub account; no passwords stored).
- Repository: `doctutorials-zoom-suite`
- Visibility: **private**
- Default branch: `main`
- On creation: leave "Add a README", `.gitignore`, and license **unchecked** because they already exist here.
- Do not use existing public repositories for confidential project details.

## One-time creation
Use GitHub's **New repository** interface (`https://github.com/new`), choose the owner and exact name above, select **Private**, and create it. The connected ChatGPT GitHub integration presently cannot create repositories but can push text files once an existing repository is available.

## Publish from a local machine (alternative to ChatGPT connector)
```bash
cd doctutorials-zoom-suite
git init -b main
git add .
git commit -m "docs: initialize DocTutorials Zoom Suite v0.1"
git remote add origin git@github.com:vinodkumar-Hegde/doctutorials-zoom-suite.git
git push -u origin main
```
Use GitHub's HTTPS Git remote if SSH is not configured. **Never paste GitHub tokens or Zoom secrets into chat or committed files.**

## Post-publish checks
1. Verify repository visibility is Private.
2. Verify all expected Markdown documents and `AGENTS.md` appear.
3. Enable secret scanning / push protection where available, require PR review, and protect `main`.
4. Record the initial commit SHA and date in `docs/SESSION-NOTES.md`.
5. Run a secret scan before adding any Zoom developer application credentials.

## Milestone 1 status
The operator has confirmed Zoom automatic cloud recording was implemented for the four host accounts. Acceptance tests and supporting redacted evidence remain open in `10-ROADMAP-ACCEPTANCE.md`. The next technical milestone is Zoom Server-to-Server OAuth app configuration, not repeating live cloud recording settings.

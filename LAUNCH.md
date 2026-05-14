# Launch checklist — flip the distribution toggles

The release workflows + Docker file + mkdocs config are all in place
(see `v0.6.0`+ tags). They fire on `git push` and `git tag` events but
won't do anything until **you** flip four toggles on the GitHub and
PyPI side. Total time: ~15 minutes.

After all four toggles are on, the next `git tag vX.Y.Z && git push --tags`
automatically:

- Publishes a sdist + wheel to PyPI → `pip install architect-companion-mcp` works.
- Builds and pushes a multi-arch Docker image to GHCR → `docker pull ghcr.io/nbschultz97/architect-companion-mcp:latest` works.
- Deploys the mkdocs site to GitHub Pages → `https://nbschultz97.github.io/cots-catalog/` works.

---

## 1) PyPI Trusted Publishing  (~5 min)

This is the cleanest way to publish — no API token to manage, GitHub
Actions authenticates via OIDC.

1. Sign in at https://pypi.org. Create an account if you don't have one
   (and enable 2FA).
2. Go to https://pypi.org/manage/account/publishing/.
3. Under **Add a new pending publisher**, fill in:
   - **PyPI Project Name:** `architect-companion-mcp`
   - **Owner:** `nbschultz97`
   - **Repository name:** `cots-catalog`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
4. Click **Add**.

On the GitHub side, create the matching environment:

5. Repo Settings → **Environments** → **New environment** → name it `pypi`.
6. (Optional but recommended) Add required reviewers (yourself) so a
   release waits for your click before publishing.

**Test it:** bump the version in `pyproject.toml` to `0.11.1`,
`git tag v0.11.1 && git push --tags`. The `release.yml` workflow
should build + publish + create a GitHub Release within ~5 minutes.

---

## 2) GHCR packages permission  (~1 min)

The release workflow also builds a multi-arch Docker image and pushes
to GitHub Container Registry. The default `GITHUB_TOKEN` permissions
don't let it push to GHCR unless you toggle this:

1. Repo Settings → **Actions** → **General**.
2. Scroll to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Check **Allow GitHub Actions to create and approve pull requests**.
5. Click **Save**.

That's it. The next tag push includes the Docker image at
`ghcr.io/nbschultz97/architect-companion-mcp:0.11.1` and `:latest`.

**Verify it:** after the tag-triggered workflow completes, run

```bash
docker pull ghcr.io/nbschultz97/architect-companion-mcp:latest
docker run --rm -i ghcr.io/nbschultz97/architect-companion-mcp:latest
```

---

## 3) GitHub Pages deploy  (~3 min)

The `docs.yml` workflow runs `mkdocs gh-deploy` on every push to `main`
that touches `docs/`, `mkdocs.yml`, README, or CHANGELOG. It writes to
a `gh-pages` branch. You need to point GitHub Pages at that branch.

1. Push any change to `main` (or wait for the next docs change) so
   `docs.yml` runs once and creates the `gh-pages` branch.
2. Repo Settings → **Pages**.
3. Under **Source**, select **Deploy from a branch**.
4. **Branch:** `gh-pages` / `/ (root)`.
5. Click **Save**.

Within ~60 seconds the site is live at
`https://nbschultz97.github.io/cots-catalog/`.

**Verify it:** open the URL. You should see the mkdocs Material theme
landing page with the table of contents.

---

## 4) MCP server registry submission  (~5 min)

Anthropic maintains a community list of MCP servers. Submitting puts
the project in front of the entire Claude Desktop / Code user base.

1. Go to https://github.com/modelcontextprotocol/servers.
2. Click **Fork**.
3. In your fork, edit the appropriate registry file (the repo's README
   has the current category list; usually `README.md` itself has a
   "Community Servers" section).
4. Add an entry under the appropriate category. Suggested entry:

   ```markdown
   - [Architect Companion](https://github.com/nbschultz97/cots-catalog) — FPV / sUAS build advisor with parts catalog, compatibility checks, cruise-aware physics, and validated against real flight times. MIT, Python.
   ```

5. Commit and open a **Pull Request** against `modelcontextprotocol/servers`.

The PR will sit until a maintainer reviews — usually a few days.

---

## After all four toggles are on

Tag a release to fire the workflows end-to-end:

```bash
# Bump version
sed -i 's/0.11.0/0.11.1/' pyproject.toml src/architect_companion_mcp/__init__.py
git add -A && git commit -m "chore: bump to 0.11.1"

# Tag and push
git tag -a v0.11.1 -m "v0.11.1 — first PyPI + Docker release"
git push origin main
git push origin v0.11.1
```

Watch the **Actions** tab. You should see `release.yml` succeed and
both PyPI + GHCR get the new package + image. The docs site updates
on the next push that touches docs/.

---

## Optional follow-ups (skip until adoption justifies the work)

| Task | Effort | When |
|---|---|---|
| Pin a custom domain on GH Pages (`architect-companion.dev`) | 30 min | When you have a domain |
| Deploy the web UI to Vercel / Fly.io / Railway as a hosted demo | 60 min | After PyPI is live |
| Submit to Awesome MCP list | 5 min | After PyPI is live |
| Submit to FPV-builder forums (rcgroups, r/Multicopter) | 30 min | After web UI is hosted |
| Launch post on Hacker News | 60 min | After everything above |

The first four toggles unlock everything else. Run them when you have
15 minutes — none of them require domain expertise, just clicks.

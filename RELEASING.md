# Releasing Espresso

Maintainer notes. Contributors don't need any of this — see
[CONTRIBUTING.md](CONTRIBUTING.md).

**Merging to `master` does not create a release.** A merge only runs `ci.yml`.
Releases are built by `.github/workflows/release.yml`, which triggers on a
pushed tag matching `v*` — and on nothing else.

## Once, before your first release

Check **Settings → Actions → General → Workflow permissions** is set to
**Read and write**. Without it all three builds succeed and the publish step
fails with a 403.

## 1. Prepare the release on a branch

```bash
git checkout development
git pull origin master          # start from what's on master
```

- Bump `__version__` in `src/espresso/__init__.py`. That is the **only** place
  a version number is written — `pyproject.toml` and `Espresso.spec` both read
  it from there.
- In `CHANGELOG.md`, move the `Unreleased` entries under the new version and
  update the link definitions at the bottom.

```bash
make check                      # lint + tests, same as CI
git commit -am "Release v1.2.0"
git push origin development
```

Open a PR to `master` and merge it once CI is green.

## 2. Tag master

The tag must point at the *merged* commit, so pull first — tagging a stale
local `master` is the easiest mistake to make here.

```bash
git checkout master
git pull origin master
git describe --tags --abbrev=0   # sanity check: what is the last release?
grep __version__ src/espresso/__init__.py

git tag v1.2.0
git push origin v1.2.0
```

Nothing enforces that the tag matches `__version__`, so compare them yourself
before pushing.

## 3. Watch it build

Pushing the tag starts three parallel jobs (macOS, Windows, Linux). Each builds
with `Espresso.spec` and uploads a zip; a final job publishes a GitHub release
with all three attached. It takes a few minutes.

The release is **published immediately**, not drafted. To review it first, add
`draft: true` under the `softprops/action-gh-release` step — and note that tag
pushes run the workflow *as it exists at the tagged commit*, so that change has
to be merged to `master` before you create the tag.

## If a build fails

Delete the tag locally and remotely, fix the problem, and tag again:

```bash
git tag -d v1.2.0
git push --delete origin v1.2.0
```

If a release was already published for that tag, re-running updates it in place
rather than starting clean. Delete the release in the GitHub UI first if you
want no leftover assets from the failed attempt.

You can also re-run a build without re-tagging: **Actions → Release → Run
workflow**, passing the tag name as the input.

## Release checklist

- [ ] `__version__` bumped in `src/espresso/__init__.py`
- [ ] `CHANGELOG.md` updated, `Unreleased` emptied, links at the bottom fixed
- [ ] `make check` green locally
- [ ] PR merged to `master`, CI green
- [ ] Local `master` pulled, tag matches `__version__`
- [ ] Tag pushed, all three build jobs green
- [ ] Release page shows three zips, and one of them actually runs

## Code signing

Releases are currently **unsigned**, so Windows SmartScreen and macOS Gatekeeper
both warn on first run. This is the single biggest friction point for new users,
and it is a provenance problem, not a code problem — nothing about the binary
can fix it. Only a signature can.

Two things that reduce false positives are already in place: builds are
**onedir** (a onefile executable that unpacks to `%TEMP%` on every launch is a
well-known AV heuristic trigger) and **UPX is disabled**.

The realistic routes:

| Option | Cost | Catch |
| --- | --- | --- |
| [SignPath Foundation](https://signpath.org/) | Free for OSS | Manual approval per release; project must look established |
| [Azure Artifact Signing](https://azure.microsoft.com/en-us/products/artifact-signing) (was Trusted Signing) | ~$10/month | Individuals are only eligible in the USA and Canada |
| OV certificate (DigiCert, Sectigo) | ~$150–300/year | Reputation still has to build up |

**SignPath Foundation is the best fit.** It issues an OV certificate, keeps the
private key in its own HSM (you never handle it), and needs no personal identity
verification. Espresso already meets the structural requirements: an
OSI-approved licence with no proprietary components, a public repo, and
reproducible CI builds that a signing pipeline can verify.

Two things to be aware of before applying:

- **The keystroke feature needs explaining.** SignPath excludes "potentially
  unwanted programs", and a tool that synthesises input can look like one at a
  glance. Say plainly that Espresso is a power-management utility in the
  tradition of Caffeine and Amphetamine, that the default mode sends no input at
  all, and that F15 is opt-in and documented.
- **Maturity matters.** They expect an actively maintained project with real
  releases behind it. A project at its second-ever release may be told to come
  back later.

Also worth setting expectations: signing does **not** make the SmartScreen
warning vanish overnight. Reputation accrues per-file-hash as downloads
accumulate; a signed binary starts from a much better place than an unsigned
one, but a brand-new certificate is not instant trust.

macOS is a separate track: Gatekeeper needs an Apple Developer ID ($99/year)
plus notarisation, which has no free equivalent.

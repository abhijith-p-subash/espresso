# Security Policy

## Supported versions

Only the latest release receives fixes.

| Version | Supported |
| ------- | --------- |
| 1.2.x   | ✅        |
| < 1.2   | ❌        |

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Use [GitHub's private vulnerability reporting](https://github.com/abhijith-p-subash/espresso/security/advisories/new),
or email <abhijith.p.subash@gmail.com>. Include what you did, what happened,
and the platform and version you saw it on. You can expect an acknowledgement
within a week.

## What Espresso does on your machine

Worth knowing before you audit it:

- **Synthetic keyboard input.** In *Sleep + activity* and *Simulate activity
  only* modes, Espresso presses and releases **F15** on a timer. It never
  reads, records, or intercepts input. On macOS this requires Accessibility
  permission, which you grant explicitly.
- **Helper processes.** It runs `caffeinate` (macOS) or `systemd-inhibit`
  (Linux) with a fixed argument list — no user input is ever interpolated into
  a command, and no shell is involved.
- **Local files only.** Config, log and lock files, in the standard per-platform
  locations listed in the README.
- **No network access.** Espresso makes no outbound connections of any kind. It
  has no telemetry, no update check, and no analytics.

## Note on unsigned binaries

The released binaries are not code-signed or notarised. macOS and Windows will
warn you. If that is a problem for your environment, build from source — the
`Espresso.spec` recipe is committed and produces the same artefacts.

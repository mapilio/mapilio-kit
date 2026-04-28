# Configuration

Mapilio Kit reads configuration from environment variables. Sensitive values
(DSNs, tokens) **must never** be committed; copy `.env.example` to `.env` and
set them locally, or export them in your shell.

## Telemetry / Sentry

By default Sentry is **disabled** — no DSN is shipped with the package, so no
events are sent. To opt in, set:

| Variable | Default | Description |
| --- | --- | --- |
| `MAPILIO_KIT_SENTRY_DSN` | _(empty)_ | Your Sentry project DSN. Leave empty to disable. |
| `MAPILIO_KIT_DISABLE_TELEMETRY` | `0` | Set to `1`/`true` to force-disable Sentry even if a DSN is set. |
| `MAPILIO_KIT_SENTRY_TRACES_RATE` | `0.1` | Sampling rate for performance traces, between `0.0` and `1.0`. |
| `MAPILIO_KIT_SENTRY_PROFILES_RATE` | `0.1` | Sampling rate for profiles, between `0.0` and `1.0`. |

If `sentry-sdk` is not installed, the CLI silently skips initialization — the
package is treated as an optional runtime dependency.

### Privacy

Telemetry, when enabled, only captures uncaught exceptions and (if traces are
enabled) span timings for the CLI. No image content, no GPS coordinates, and
no Mapilio credentials are sent.

## Local `.env` file

The recommended workflow:

```bash
cp .env.example .env
# edit .env with your editor of choice
```

`.env` is in `.gitignore`, so your local secrets stay on your machine. The CLI
itself does **not** auto-load `.env`; export the variables in your shell
(e.g. `set -a; source .env; set +a`) or use a tool like
[`direnv`](https://direnv.net/) or `python-dotenv`.

## Mapilio account credentials

Account credentials are stored in the per-user config file managed by
`mapilio_kit authenticate` — they are not read from environment variables.
See `mapilio_kit authenticate --help` for details.

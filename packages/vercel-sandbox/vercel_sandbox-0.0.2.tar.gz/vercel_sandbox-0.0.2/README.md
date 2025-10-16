# Python SDK for Vercel Sandbox

This is a minimal Python SDK that mirrors the core features of the TypeScript SDK:

- Create sandboxes
- Run commands (detached or wait for completion)
- Stream command logs
- Read/Write files, mkdir
- Stop sandbox
- Resolve exposed port domain

**Quickstart**

```bash
pip install vercel-sandbox
```

Or locally:

```bash
pip install -e .
```

**Example**

```python
import asyncio
from vercel.sandbox import AsyncSandbox as Sandbox

async def main():
    async with await Sandbox.create(
        source={"type": "git", "url": "https://github.com/vercel/sandbox-example-next.git"},
        resources={"vcpus": 4},
        ports=[3000],
        timeout=600_000,
        runtime="node22",
    ) as sandbox:
        print("Installing dependencies...")
        result = await sandbox.run_command("npm", ["install", "--loglevel", "info"])  # waits
        if result.exit_code != 0:
            raise SystemExit("install failed")

        print("Starting dev server...")
        cmd = await sandbox.run_command_detached("npm", ["run", "dev"])  # detached
        print("Visit:", sandbox.domain(3000))

asyncio.run(main())
```

Using or not using the context manager

```python
# Preferred: automatic cleanup
async with await Sandbox.create(timeout=60_000, runtime="node22") as sandbox:
    await sandbox.run_command("echo", ["hello"])

# Manual cleanup
sandbox = await Sandbox.create(timeout=60_000, runtime="node22")
try:
    await sandbox.run_command("echo", ["hello"])
finally:
    await sandbox.stop()
    await sandbox.client.aclose()
```

Authentication

The SDK prefers Vercel OIDC tokens when available:

- Local: use `vercel env pull` and place credentials in a `.env` file (auto-loaded).
- Alternatively provide `VERCEL_TOKEN`, `VERCEL_TEAM_ID`, and `VERCEL_PROJECT_ID`.

Environment variables

- `VERCEL_OIDC_TOKEN` plus `VERCEL_TEAM_ID` and `VERCEL_PROJECT_ID`
- or `VERCEL_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_PROJECT_ID`

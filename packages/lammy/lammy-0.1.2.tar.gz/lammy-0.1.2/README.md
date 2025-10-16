# lammy

`lammy` is a minimal command line helper for day-to-day Lambda Cloud management.
It focuses on the flow of picking an instance type, launching it, wiring up SSH,
then shutting it down when you are done.

```
lammy --help
```

## Quick Start

1. **Install dependencies**

   ```
   uv tool install lammy
   ```

2. **Authenticate**

```
   lammy auth login
```

   Paste your Lambda API key when prompted. You can generate keys in the Lambda
   Cloud dashboard. `lammy` also discovers `LAMBDA_API_KEY` from the environment
   or a local `.env`.

3. **Set your defaults (optional but recommended)**

```
   lammy settings set --region us-west-1 --ssh-key my-default-key
```

4. **Pick a machine**

```
   lammy list
```

   This prints the instance types that currently have capacity. Add
   `--all` if you want the full catalog.

5. **Launch, connect, terminate**

```
   lammy up              # guided launch flow (press enter to accept defaults)
   lammy ssh             # jumps straight into SSH for the most recent instance
   lammy down            # terminates the most recent instance (with confirm)
```

   `lammy up` writes an SSH host entry automatically. Use the printed alias in
   your Remote Explorer / editor of choice if you prefer a GUI connection.

## Commands

### Authentication

| Command | Description |
| ------- | ----------- |
| `lammy auth login` | Prompt for an API key and store it in `~/.config/lammy/config.json`. |
| `lammy auth show` | Display the masked API key currently in use and the config path. |

### Everyday flow

| Command | Description |
| ------- | ----------- |
| `lammy list` | Show instance types with live capacity (`--running` flips to currently running servers, `--all` includes types without capacity). |
| `lammy up` | Guided launcher. Prompts for type/region/SSH key if not already configured, auto-picks the GPU Base 24.04 image when available, waits for the public IP, and writes your SSH config. |
| `lammy ssh [name]` | Connect to the most recent instance (or a named one). Any extra arguments (e.g. `-L ...`) are passed through to `ssh`. |
| `lammy down [name]` | Terminate the most recent (or a named) instance. Use `--force` to skip the confirm.

### Advanced catalog commands

| Command | Description |
| ------- | ----------- |
| `lammy list --all` | Include instance types without reported capacity (defaults to capacity-only). |
| `lammy list --running` | Show currently running instances instead of the catalog. |

### SSH helpers

| Command | Description |
| ------- | ----------- |
| `lammy ssh setup <id-or-name>` | Write/update a dedicated host block in `~/.ssh/config`. |
| `lammy ssh connect [id-or-name]` | Same as the bare `lammy ssh` command, but lets you spell out an identifier/alias and optional extra args. |
| `lammy ssh keys` | List SSH keys registered with Lambda Cloud. |

### Settings

`lammy settings` stores lightweight defaults inside `~/.config/lammy/config.json`.
The values are:

| Key | Purpose |
| --- | ------- |
| `default_region` | Region used when `--region` is omitted on `lammy up`. |
| `default_ssh_key_name` | SSH key name assumed when `--ssh-key` flags are omitted. |
| `default_image` | Image string applied on launch (`family:gpu-base-24-04` by default). |
| `ssh_user` | Default user used in generated SSH host blocks and ad-hoc connections. |
| `ssh_identity_file` | Optional path to an identity file (`~/.ssh/id_ed25519`, etc.) written into the SSH config. |
| `ssh_alias_prefix` | Prefix applied to generated host aliases (default `lammy`). |

Inspect the stored configuration with:

```
lammy settings show
```

### Images

`lammy` pins launches to the `gpu-base-24-04` family out of the box. Change it
whenever you like:

```
lammy settings set --image family:<family-name>
```

Prefer an explicit image ID? Use `--image id:<uuid>`.


## Publishing

```
uv build
uv publish --token ...
```

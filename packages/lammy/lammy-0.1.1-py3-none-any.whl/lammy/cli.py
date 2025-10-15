from __future__ import annotations

import json
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .api import LammyApiError, LammyClient, LammyNetworkError
from .config import DEFAULT_IMAGE, ConfigManager, LammyConfig, read_env_api_key
from .models import InstanceRecord, InstanceTypeSummary
from .render import instance_table, instance_types_table, ssh_keys_table
from .ssh import default_alias, ensure_ssh_entry, open_ssh_session, sanitize_alias


@dataclass
class AppContext:
    console: Console
    config_manager: ConfigManager
    config: LammyConfig
    api_key: Optional[str] = None
    _client: Optional[LammyClient] = field(default=None, init=False, repr=False)

    def resolve_api_key(self) -> str:
        key = self.api_key or self.config.api_key
        if not key:
            raise click.UsageError(
                "No API key configured. Run `lammy auth login` or provide --api-key."
            )
        return key

    def client(self) -> LammyClient:
        if self._client is None:
            self._client = LammyClient(
                api_key=self.resolve_api_key(),
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def refresh_config(self) -> None:
        self.config = self.config_manager.load()

    def replace_api_key(self, api_key: str) -> None:
        self.api_key = api_key
        if self._client is not None:
            self._client.close()
            self._client = None

    def remember_instance(
        self, *, instance_id: str, alias: str, name: Optional[str] = None
    ) -> None:
        self.config = self.config_manager.remember_instance(
            instance_id=instance_id, alias=alias, name=name
        )

    def clear_last_instance(self) -> None:
        self.config = self.config_manager.clear_last_instance()


@contextmanager
def handle_api_errors(console: Console):
    try:
        yield
    except LammyApiError as exc:
        console.print(f"[bold red]API error:[/] {exc}")
        raise click.Abort() from exc
    except LammyNetworkError as exc:
        console.print(f"[bold red]Network error:[/] {exc}")
        raise click.Abort() from exc


def main() -> None:
    cli(prog_name="lammy")


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    lammy is a lightweight CLI for managing Lambda Cloud VMs.
    """

    console = Console()
    config_manager = ConfigManager()
    config = config_manager.load()
    env_api_key = read_env_api_key()
    resolved_api_key = env_api_key or config.api_key
    app = AppContext(
        console=console,
        config_manager=config_manager,
        config=config,
        api_key=resolved_api_key,
    )
    ctx.obj = app
    ctx.call_on_close(app.close)


@cli.group()
@click.pass_context
def auth(ctx: click.Context) -> None:
    """Manage stored Lambda credentials."""


@auth.command("login")
@click.option("--api-key", prompt=True, hide_input=True, help="Lambda API key to save.")
@click.pass_obj
def auth_login(app: AppContext, api_key: str) -> None:
    """Store your Lambda API key locally."""

    api_key = api_key.strip()
    if not api_key:
        raise click.BadParameter("API key cannot be empty.")

    config = app.config_manager.set_api_key(api_key)
    app.replace_api_key(api_key)
    app.config = config
    app.console.print(
        f"[green]API key saved to[/] {app.config_manager.config_path.expanduser()}"
    )


@auth.command("show")
@click.pass_obj
def auth_show(app: AppContext) -> None:
    """Show the currently configured authentication source."""

    key = app.api_key or app.config.api_key
    if not key:
        app.console.print("[yellow]No API key configured.[/]")
        return
    masked = f"{key[:6]}…{key[-4:]}" if len(key) > 10 else key
    app.console.print(f"Using API key: [cyan]{masked}[/]")
    app.console.print(f"Config file: {app.config_manager.config_path.expanduser()}")


@cli.command("list")
@click.option(
    "--running",
    is_flag=True,
    help="Show running instances instead of available machine types.",
)
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Include instance types without current capacity when listing types.",
)
@click.pass_obj
def list_simple(app: AppContext, running: bool, show_all: bool) -> None:
    """Quick access: list instance types or running instances."""

    if running:
        with handle_api_errors(app.console):
            instances = app.client().list_instances()
        if not instances:
            app.console.print("[yellow]No instances are currently running.[/]")
            return
        app.console.print(instance_table(instances))
        return

    with handle_api_errors(app.console):
        types = app.client().list_instance_types()
    if not show_all:
        types = [item for item in types if item.regions_with_capacity]
    if not types:
        app.console.print("[yellow]No instance types found.[/]")
        return
    app.console.print(instance_types_table(types))


@cli.command("up")
@click.option(
    "--type",
    "instance_type_name",
    help="Instance type to launch. If omitted, lammy prompts with available options.",
)
@click.option("--region", help="Region code for the instance.")
@click.option("--ssh-key", "ssh_key_name", help="Lambda SSH key name to authorize.")
@click.option("--name", "instance_name", help="Display name for the instance.")
@click.pass_obj
def up_simple(
    app: AppContext,
    instance_type_name: Optional[str],
    region: Optional[str],
    ssh_key_name: Optional[str],
    instance_name: Optional[str],
) -> None:
    """Launch an instance with minimal fuss."""

    with handle_api_errors(app.console):
        all_types = app.client().list_instance_types()
        available_types = [item for item in all_types if item.regions_with_capacity]
        if not available_types:
            app.console.print("[red]Lambda reports no capacity right now.[/]")
            raise click.Abort()

        selected_type = _select_instance_type(
            app, available_types, instance_type_name
        )
        region_name = _select_region(app, selected_type, region)
        if not region_name:
            raise click.Abort()

        ssh_key = _select_ssh_key(app, ssh_key_name)
        if not ssh_key:
            raise click.Abort()

        desired_name = _select_instance_name(
            app, selected_type, instance_name
        )

        image_payload = _choose_default_image_payload(app, region_name)

        instance_ids = app.client().launch_instance(
            region_name=region_name,
            instance_type_name=selected_type.name,
            ssh_key_names=[ssh_key],
            name=desired_name,
            image=image_payload,
        )

        if not instance_ids:
            app.console.print("[yellow]Launch accepted; waiting for provisioning...[/]")
            raise click.Abort()

        instance_id = instance_ids[0]
        app.console.print(
            f"[green]Launch request accepted:[/] {instance_id} ({selected_type.name} in {region_name})"
        )

        instance = _wait_for_instance_ready(app, instance_id)

    alias = default_alias(
        app.config.ssh_alias_prefix,
        instance.preferred_display_name(),
        instance.id,
    )

    if instance.ip:
        path = ensure_ssh_entry(
            alias,
            instance.ip,
            user=app.config.ssh_user,
            identity_file=app.config.ssh_identity_file,
        )
        app.console.print(
            f"[green]SSH ready:[/] Host [cyan]{alias}[/] → {instance.ip} "
            f"(config: {path.expanduser()})"
        )
    else:
        app.console.print(
            "[yellow]Instance is still acquiring a public IP. "
            "Run `lammy ssh setup` in a minute if needed.[/]"
        )

    app.remember_instance(
        instance_id=instance.id,
        alias=alias,
        name=instance.preferred_display_name(),
    )
    app.console.print(
        f"Connect now with `uv run lammy ssh` or via your editor (Host {alias})."
    )


@cli.command("down")
@click.argument("identifier", required=False)
@click.option(
    "--force",
    is_flag=True,
    help="Skip the confirmation prompt.",
)
@click.pass_obj
def down_simple(
    app: AppContext,
    identifier: Optional[str],
    force: bool,
) -> None:
    """Terminate the most recent instance (or a specific one)."""

    with handle_api_errors(app.console):
        target = _determine_target_instance(app, identifier)
        if target is None:
            return

        if not force:
            confirm = Confirm.ask(
                f"Terminate [cyan]{target.preferred_display_name()}[/] ({target.id})?",
                default=False,
            )
            if not confirm:
                app.console.print("[yellow]Termination cancelled.[/]")
                return

        terminated = app.client().terminate_instances([target.id])

    if terminated:
        term = terminated[0]
        app.console.print(
            f"[green]Terminated:[/] {term.id} ({term.preferred_display_name()})"
        )
    else:
        app.console.print("[yellow]Termination requested.[/]")

    if app.config.last_instance_id == target.id:
        app.clear_last_instance()

@cli.command("types")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Include instance types without current capacity.",
)
@click.pass_obj
def list_types(app: AppContext, show_all: bool) -> None:
    """List available instance types."""

    with handle_api_errors(app.console):
        types = app.client().list_instance_types()
    if not show_all:
        types = [item for item in types if item.regions_with_capacity]
    if not types:
        app.console.print("[yellow]No instance types found.[/]")
        return
    app.console.print(instance_types_table(types))


@cli.group()
@click.pass_context
def instances(ctx: click.Context) -> None:
    """Work with Lambda instances."""


@instances.command("list")
@click.option("--region", help="Filter instances by region.")
@click.pass_obj
def instances_list(app: AppContext, region: Optional[str]) -> None:
    """List running instances."""

    with handle_api_errors(app.console):
        instances = app.client().list_instances()
    if region:
        region_lower = region.lower()
        instances = [
            inst for inst in instances if inst.region.name.lower() == region_lower
        ]
    if not instances:
        app.console.print("[yellow]No instances found.[/]")
        return
    app.console.print(instance_table(instances))


@instances.command("launch")
@click.option(
    "--instance-type",
    "instance_type_name",
    required=True,
    help="Instance type name to launch (e.g., gpu_1x_a10).",
)
@click.option("--region", help="Region code to launch the instance in (e.g., us-west-1).")
@click.option("--name", help="Optional display name for the instance.")
@click.option("--hostname", help="Optional hostname to assign to the instance.")
@click.option(
    "--ssh-key",
    "ssh_key_names",
    multiple=True,
    help="Name of an SSH key already registered with Lambda. Repeat to pass multiple.",
)
@click.option(
    "--image",
    help="Image to use. Use `family:<name>` or `id:<uuid>`. Defaults to GPU BASE 24.04.",
)
@click.option("--user-data", type=click.Path(exists=True, dir_okay=False), help="Path to cloud-init user data.")
@click.option(
    "--configure-ssh/--no-configure-ssh",
    default=True,
    show_default=True,
    help="Automatically add the instance to your SSH config once it has an IP.",
)
@click.option("--ssh-alias", help="Override the SSH host alias to write.")
@click.option("--ssh-user", help="Override the SSH username for the config entry.")
@click.option("--identity-file", help="Path to the SSH identity file for connections.")
@click.pass_obj
def instances_launch(
    app: AppContext,
    instance_type_name: str,
    region: Optional[str],
    name: Optional[str],
    hostname: Optional[str],
    ssh_key_names: Sequence[str],
    image: Optional[str],
    user_data: Optional[str],
    configure_ssh: bool,
    ssh_alias: Optional[str],
    ssh_user: Optional[str],
    identity_file: Optional[str],
) -> None:
    """Launch a new instance."""

    region_name = region or app.config.default_region
    if not region_name:
        raise click.UsageError(
            "Region is required. Provide --region or set a default with "
            "`lammy settings set --region <code>`."
        )

    key_names = list(ssh_key_names) or (
        [app.config.default_ssh_key_name] if app.config.default_ssh_key_name else []
    )
    if not key_names:
        raise click.UsageError(
            "At least one --ssh-key is required. Register a key in Lambda and reference it here."
        )

    image_payload = _parse_image(image)
    user_data_payload = _load_user_data(user_data) if user_data else None

    with handle_api_errors(app.console):
        instance_ids = app.client().launch_instance(
            region_name=region_name,
            instance_type_name=instance_type_name,
            ssh_key_names=key_names,
            name=name,
            hostname=hostname,
            image=image_payload,
            user_data=user_data_payload,
        )
    if not instance_ids:
        app.console.print("[yellow]Launch request submitted, awaiting provisioning.[/]")
        return

    app.console.print(
        f"[green]Launch request accepted for instance ID(s):[/] {', '.join(instance_ids)}"
    )

    if not configure_ssh:
        return

    ssh_user = ssh_user or app.config.ssh_user
    identity = identity_file or app.config.ssh_identity_file

    with handle_api_errors(app.console):
        details = _collect_instances(app, instance_ids)

    for inst in details:
        if not inst.ip:
            app.console.print(
                f"[yellow]Instance {inst.id} is provisioning; no public IP yet. "
                "Re-run `lammy ssh setup` once it is ready.[/]"
            )
            continue
        alias = ssh_alias or default_alias(
            app.config.ssh_alias_prefix, inst.preferred_display_name(), inst.id
        )
        path = ensure_ssh_entry(
            alias,
            inst.ip,
            user=ssh_user,
            identity_file=identity,
        )
        app.console.print(
            f"[green]SSH entry ready:[/] Host [cyan]{alias}[/] → {inst.ip} (config: {path.expanduser()})"
        )
        app.remember_instance(
            instance_id=inst.id,
            alias=alias,
            name=inst.preferred_display_name(),
        )


@instances.command("restart")
@click.argument("identifiers", nargs=-1)
@click.pass_obj
def instances_restart(app: AppContext, identifiers: Sequence[str]) -> None:
    """Restart one or more instances by ID or name."""

    instance_ids = _resolve_instance_ids(app, identifiers)
    if not instance_ids:
        app.console.print("[yellow]No matching instances found to restart.[/]")
        return
    with handle_api_errors(app.console):
        restarted = app.client().restart_instances(instance_ids)
    for inst in restarted:
        app.console.print(
            f"[green]Restarted:[/] {inst.id} ({inst.preferred_display_name()}) → {inst.status}"
        )


@instances.command("terminate")
@click.argument("identifiers", nargs=-1)
@click.option(
    "--yes",
    is_flag=True,
    help="Skip the interactive confirmation prompt.",
)
@click.pass_obj
def instances_terminate(
    app: AppContext, identifiers: Sequence[str], yes: bool
) -> None:
    """Terminate one or more instances."""

    instance_ids = _resolve_instance_ids(app, identifiers)
    if not instance_ids:
        app.console.print("[yellow]No matching instances found to terminate.[/]")
        return

    if not yes:
        confirmed = Confirm.ask(
            f"Terminate {len(instance_ids)} instance(s)? This cannot be undone.",
            default=False,
        )
        if not confirmed:
            app.console.print("[yellow]Termination aborted.[/]")
            return

    with handle_api_errors(app.console):
        terminated = app.client().terminate_instances(instance_ids)
    for inst in terminated:
        app.console.print(
            f"[green]Terminated:[/] {inst.id} ({inst.preferred_display_name()})"
        )
        if app.config.last_instance_id == inst.id:
            app.clear_last_instance()


@cli.group(invoke_without_command=True)
@click.pass_context
def ssh(ctx: click.Context) -> None:
    """SSH helpers (run without subcommand to connect)."""

    if ctx.invoked_subcommand is None:
        identifier = ctx.args[0] if ctx.args else None
        extra_args = ctx.args[1:] if len(ctx.args) > 1 else None
        app: AppContext = ctx.obj
        _connect_via_ssh(
            app,
            identifier=identifier,
            alias_override=None,
            extra_args=list(extra_args) if extra_args else None,
        )


@ssh.command("setup")
@click.argument("identifier")
@click.option("--alias", "alias_override", help="Set a custom host alias.")
@click.option("--user", "ssh_user", help="SSH username to use.")
@click.option("--identity-file", help="Path to the identity file to reference.")
@click.pass_obj
def ssh_setup(
    app: AppContext,
    identifier: str,
    alias_override: Optional[str],
    ssh_user: Optional[str],
    identity_file: Optional[str],
) -> None:
    """Add an instance to your SSH config."""

    instance = _resolve_single_instance(app, identifier)
    if not instance.ip:
        app.console.print(
            "[yellow]Instance does not currently have a public IP. Try again once it is running.[/]"
        )
        return

    alias = alias_override or default_alias(
        app.config.ssh_alias_prefix, instance.preferred_display_name(), instance.id
    )
    user = ssh_user or app.config.ssh_user
    identity = identity_file or app.config.ssh_identity_file

    path = ensure_ssh_entry(alias, instance.ip, user=user, identity_file=identity)
    app.console.print(
        f"[green]SSH entry updated:[/] Host [cyan]{alias}[/] → {instance.ip} (config: {path.expanduser()})"
    )
    if app.config.last_instance_id == instance.id or app.config.last_instance_id is None:
        app.remember_instance(instance_id=instance.id, alias=alias, name=instance.name)


@ssh.command("connect")
@click.argument("identifier", required=False)
@click.option("--alias", help="Use an explicit host alias instead of resolving.")
@click.option("--ssh-args", help="Extra arguments to append to the ssh command.")
@click.pass_obj
def ssh_connect(
    app: AppContext,
    identifier: Optional[str],
    alias: Optional[str],
    ssh_args: Optional[str],
) -> None:
    """Open an interactive SSH session."""

    extra = ssh_args.split() if ssh_args else None
    _connect_via_ssh(
        app,
        identifier=identifier,
        alias_override=alias,
        extra_args=extra,
    )


@cli.group()
@click.pass_context
def settings(ctx: click.Context) -> None:
    """Adjust lammy defaults."""


@settings.command("show")
@click.pass_obj
def settings_show(app: AppContext) -> None:
    """Show stored defaults."""

    data = {
        "default_region": app.config.default_region,
        "default_ssh_key_name": app.config.default_ssh_key_name,
        "default_image": app.config.default_image or DEFAULT_IMAGE,
        "ssh_user": app.config.ssh_user,
        "ssh_identity_file": app.config.ssh_identity_file,
        "ssh_alias_prefix": app.config.ssh_alias_prefix,
    }
    formatted = json.dumps(data, indent=2)
    app.console.print(formatted)


@settings.command("set")
@click.option("--region", help="Set a default region.")
@click.option("--ssh-key", help="Set a default SSH key name.")
@click.option(
    "--image",
    help="Set the default image (family:<name> or id:<uuid>, use 'default' for GPU BASE 24.04).",
)
@click.option("--ssh-user", help="Set the default SSH username.")
@click.option("--identity-file", help="Set the default SSH identity file path.")
@click.option("--alias-prefix", help="Set the prefix used for SSH host aliases.")
@click.pass_obj
def settings_set(
    app: AppContext,
    region: Optional[str],
    ssh_key: Optional[str],
    image: Optional[str],
    ssh_user: Optional[str],
    identity_file: Optional[str],
    alias_prefix: Optional[str],
) -> None:
    """Update default settings."""

    image_value: Optional[str]
    if image is None:
        image_value = None
    else:
        normalized = image.strip()
        if not normalized or normalized.lower() in {"none", "null"}:
            image_value = ""
        elif normalized.lower() in {"default", "gpu-base-24-04"}:
            image_value = DEFAULT_IMAGE
        else:
            payload = _parse_image(normalized)
            if not payload:
                raise click.BadParameter(
                    "Image must be formatted as family:<name> or id:<uuid>.",
                    param_hint="--image",
                )
            image_value = normalized

    config = app.config_manager.update_defaults(
        default_region=region,
        default_ssh_key_name=ssh_key,
        default_image=image_value,
        ssh_user=ssh_user,
        ssh_identity_file=identity_file,
        ssh_alias_prefix=alias_prefix,
    )
    app.config = config
    app.console.print("[green]Settings updated.[/]")


@ssh.command("keys")
@click.pass_obj
def ssh_keys(app: AppContext) -> None:
    """List SSH keys stored with Lambda."""

    with handle_api_errors(app.console):
        keys = app.client().list_ssh_keys()
    if not keys:
        app.console.print("[yellow]No SSH keys found on your Lambda account.[/]")
        return
    app.console.print(ssh_keys_table(keys))


def _parse_image(image: Optional[str]) -> Optional[dict]:
    if not image:
        return None
    image = image.strip()
    if image.startswith("family:"):
        return {"family": image.split(":", 1)[1]}
    if image.startswith("id:"):
        return {"id": image.split(":", 1)[1]}
    return {"family": image}


def _load_user_data(path_str: str) -> str:
    path = Path(path_str).expanduser()
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Unable to read user data file: {exc}") from exc


def _collect_instances(app: AppContext, identifiers: Sequence[str]) -> Sequence[InstanceRecord]:
    details: list[InstanceRecord] = []
    for instance_id in identifiers:
        with handle_api_errors(app.console):
            details.append(app.client().get_instance(instance_id))
    return details


def _resolve_instance_ids(app: AppContext, identifiers: Sequence[str]) -> Sequence[str]:
    if not identifiers:
        return []
    with handle_api_errors(app.console):
        instances = app.client().list_instances()
    id_map = {inst.id: inst for inst in instances}
    name_map = {inst.preferred_display_name(): inst for inst in instances}
    resolved: list[str] = []
    for identifier in identifiers:
        inst = id_map.get(identifier) or name_map.get(identifier)
        if inst:
            resolved.append(inst.id)
        else:
            app.console.print(f"[yellow]No instance found for '{identifier}'.[/]")
    return resolved


def _resolve_single_instance(app: AppContext, identifier: str) -> InstanceRecord:
    with handle_api_errors(app.console):
        instances = app.client().list_instances()
    for inst in instances:
        if inst.id == identifier or inst.preferred_display_name() == identifier:
            return inst
    raise click.ClickException(f"No instance found for '{identifier}'.")


def _select_instance_type(
    app: AppContext,
    types: Sequence[InstanceTypeSummary],
    provided: Optional[str],
) -> InstanceTypeSummary:
    if provided:
        match = _find_type_by_name(types, provided)
        if match:
            return match
        app.console.print(
            f"[yellow]Instance type '{provided}' not found or lacks capacity. Choose from the list below.[/]"
        )

    app.console.print(instance_types_table(types))
    default_choice = types[0].name
    while True:
        selection = Prompt.ask(
            "Instance type",
            default=default_choice,
        ).strip()
        match = _find_type_by_name(types, selection)
        if match:
            return match
        app.console.print(f"[red]'{selection}' is not in the available list.[/]")


def _find_type_by_name(
    types: Sequence[InstanceTypeSummary], name: str
) -> Optional[InstanceTypeSummary]:
    lowered = name.lower()
    for item in types:
        if item.name.lower() == lowered:
            return item
    # allow numeric shorthand (1-based)
    if lowered.isdigit():
        index = int(lowered) - 1
        if 0 <= index < len(types):
            return types[index]
    return None


def _select_region(
    app: AppContext,
    instance_type: InstanceTypeSummary,
    provided: Optional[str],
) -> Optional[str]:
    available = instance_type.regions_with_capacity
    if not available:
        app.console.print(
            f"[red]{instance_type.name} has no available regions at the moment.[/]"
        )
        return None

    def _normalize(value: str) -> str:
        return value.strip().lower()

    if provided:
        provided_lower = _normalize(provided)
        for region in available:
            if _normalize(region.name) == provided_lower:
                return region.name
        app.console.print(
            f"[yellow]Region '{provided}' is not available for {instance_type.name}. Pick another.[/]"
        )

    if app.config.default_region:
        default_lower = _normalize(app.config.default_region)
        for region in available:
            if _normalize(region.name) == default_lower:
                return region.name

    if len(available) == 1:
        return available[0].name

    region_names = [region.name for region in available]
    default_choice = region_names[0]
    while True:
        selection = Prompt.ask(
            "Region",
            default=default_choice,
        ).strip()
        selection_lower = _normalize(selection)
        for region in available:
            if _normalize(region.name) == selection_lower:
                return region.name
        app.console.print(f"[red]'{selection}' is not one of the offered regions.[/]")


def _select_ssh_key(app: AppContext, provided: Optional[str]) -> Optional[str]:
    keys = app.client().list_ssh_keys()

    if provided:
        for key in keys:
            if key.name == provided:
                return key.name
        app.console.print(f"[yellow]SSH key '{provided}' not found in your account.[/]")
        # fall through to prompt

    if app.config.default_ssh_key_name:
        for key in keys:
            if key.name == app.config.default_ssh_key_name:
                return key.name
        app.console.print(
            f"[yellow]Stored default SSH key '{app.config.default_ssh_key_name}' is not available anymore.[/]"
        )

    if not keys:
        app.console.print(
            "[red]You have no SSH keys registered with Lambda. Add one via the dashboard first.[/]"
        )
        return None

    if len(keys) == 1:
        return keys[0].name

    app.console.print(ssh_keys_table(keys))
    default_choice = keys[0].name
    while True:
        selection = Prompt.ask(
            "SSH key name",
            default=default_choice,
        ).strip()
        for key in keys:
            if key.name == selection:
                return key.name
        app.console.print(f"[red]SSH key '{selection}' was not found.[/]")


def _select_instance_name(
    app: AppContext,
    instance_type: InstanceTypeSummary,
    provided: Optional[str],
) -> str:
    if provided:
        return provided
    default_name = _generate_default_instance_name(app, instance_type)
    return Prompt.ask("Instance name", default=default_name).strip()


def _generate_default_instance_name(
    app: AppContext, instance_type: InstanceTypeSummary
) -> str:
    base = sanitize_alias(instance_type.name)
    suffix = secrets.token_hex(1)
    prefix = sanitize_alias(app.config.ssh_alias_prefix or "lammy")
    return f"{prefix}-{base}-{suffix}"


def _choose_default_image_payload(
    app: AppContext, _region_name: str
) -> Optional[dict]:
    for candidate in (app.config.default_image, DEFAULT_IMAGE):
        if not candidate:
            continue
        payload = _parse_image(candidate)
        if payload:
            return payload
    return None


def _wait_for_instance_ready(
    app: AppContext,
    instance_id: str,
    *,
    timeout: int = 300,
    poll_interval: int = 5,
) -> InstanceRecord:
    deadline = time.monotonic() + timeout
    with app.console.status(
        "Waiting for Lambda to assign a public IP…", spinner="dots"
    ):
        instance = app.client().get_instance(instance_id)
        while True:
            if instance.ip:
                return instance
            if time.monotonic() >= deadline:
                return instance
            time.sleep(poll_interval)
            instance = app.client().get_instance(instance_id)


def _determine_target_instance(
    app: AppContext, identifier: Optional[str]
) -> Optional[InstanceRecord]:
    if identifier:
        return _resolve_single_instance(app, identifier)

    if app.config.last_instance_id:
        try:
            return app.client().get_instance(app.config.last_instance_id)
        except LammyApiError:
            # Fall back to prompting if the remembered instance no longer exists.
            pass

    instances = app.client().list_instances()
    if not instances:
        app.console.print("[yellow]No running instances detected.[/]")
        return None
    if len(instances) == 1:
        return instances[0]

    app.console.print(instance_table(instances))
    default_choice = instances[0].preferred_display_name()
    while True:
        selection = Prompt.ask(
            "Select instance",
            default=default_choice,
        ).strip()
        match = _find_instance_match(instances, selection)
        if match:
            return match
        app.console.print(f"[red]No instance matches '{selection}'.[/]")


def _find_instance_match(
    instances: Sequence[InstanceRecord], identifier: str
) -> Optional[InstanceRecord]:
    lowered = identifier.lower()
    if lowered.isdigit():
        index = int(lowered) - 1
        if 0 <= index < len(instances):
            return instances[index]
    for inst in instances:
        if inst.id.lower() == lowered or inst.preferred_display_name().lower() == lowered:
            return inst
    return None


def _connect_via_ssh(
    app: AppContext,
    *,
    identifier: Optional[str],
    alias_override: Optional[str],
    extra_args: Optional[Sequence[str]],
) -> None:
    alias_to_use = alias_override
    instance: Optional[InstanceRecord] = None

    if identifier or not alias_to_use:
        with handle_api_errors(app.console):
            instance = _determine_target_instance(app, identifier)
        if instance is None:
            return
        alias_to_use = alias_to_use or default_alias(
            app.config.ssh_alias_prefix,
            instance.preferred_display_name(),
            instance.id,
        )

        if not instance.ip:
            app.console.print(
                "[yellow]Instance does not currently have a public IP. Try again shortly.[/]"
            )
            return

        ensure_ssh_entry(
            alias_to_use,
            instance.ip,
            user=app.config.ssh_user,
            identity_file=app.config.ssh_identity_file,
        )

        app.remember_instance(
            instance_id=instance.id,
            alias=alias_to_use,
            name=instance.preferred_display_name(),
        )

    if not alias_to_use:
        app.console.print(
            "[red]Unable to determine which SSH host to use. Specify a name or alias.[/]"
        )
        return

    try:
        exit_code = open_ssh_session(alias_to_use, extra_args=extra_args)
    except RuntimeError as exc:
        app.console.print(f"[red]{exc}[/]")
        raise click.Abort() from exc
    if exit_code != 0:
        app.console.print(f"[yellow]ssh exited with status {exit_code}[/]")

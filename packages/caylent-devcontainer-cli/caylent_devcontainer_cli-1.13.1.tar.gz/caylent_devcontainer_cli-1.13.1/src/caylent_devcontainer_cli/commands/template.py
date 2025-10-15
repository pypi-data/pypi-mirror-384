"""Template command for the Caylent Devcontainer CLI."""

import json
import os

import semver

from caylent_devcontainer_cli import __version__
from caylent_devcontainer_cli.commands.setup import EXAMPLE_ENV_VALUES
from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template
from caylent_devcontainer_cli.utils.constants import TEMPLATES_DIR
from caylent_devcontainer_cli.utils.env import is_single_line_env_var
from caylent_devcontainer_cli.utils.ui import confirm_action, log


def get_missing_single_line_vars(container_env):
    """Get missing single-line environment variables from EXAMPLE_ENV_VALUES."""
    missing_vars = {}
    for key, value in EXAMPLE_ENV_VALUES.items():
        if key not in container_env and is_single_line_env_var(value):
            missing_vars[key] = value
    return missing_vars


def prompt_for_missing_vars(missing_vars):
    """Prompt user for missing environment variables."""
    import questionary

    updated_vars = {}
    for var_name, default_value in missing_vars.items():
        log("INFO", f"New environment variable '{var_name}' needs to be added to your template")

        use_default = questionary.confirm(f"Use default value '{default_value}' for {var_name}?", default=True).ask()

        if use_default:
            updated_vars[var_name] = default_value
        else:
            custom_value = questionary.text(f"Enter custom value for {var_name}:", default=str(default_value)).ask()
            updated_vars[var_name] = custom_value

    return updated_vars


def register_command(subparsers):
    """Register the template command."""
    template_parser = subparsers.add_parser("template", help="Template management")
    template_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    template_subparsers = template_parser.add_subparsers(dest="template_command")

    # 'template save' command
    save_parser = template_subparsers.add_parser("save", help="Save current environment as a template")
    save_parser.add_argument("name", help="Template name")
    save_parser.add_argument("-p", "--project-root", help="Project root directory (default: current directory)")
    save_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    save_parser.set_defaults(func=handle_template_save)

    # 'template load' command
    load_template_parser = template_subparsers.add_parser("load", help="Load a template into current project")
    load_template_parser.add_argument("name", help="Template name")
    load_template_parser.add_argument(
        "-p", "--project-root", help="Project root directory (default: current directory)"
    )
    load_template_parser.add_argument(
        "-y", "--yes", action="store_true", help="Automatically answer yes to all prompts"
    )
    load_template_parser.set_defaults(func=handle_template_load)

    # 'template list' command
    list_parser = template_subparsers.add_parser("list", help="List available templates")
    list_parser.set_defaults(func=handle_template_list)

    # 'template delete' command
    delete_parser = template_subparsers.add_parser("delete", help="Delete one or more templates")
    delete_parser.add_argument("names", nargs="+", help="Template names to delete")
    delete_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    delete_parser.set_defaults(func=handle_template_delete)

    # 'template create' command
    create_parser = template_subparsers.add_parser("create", help="Create a new template interactively")
    create_parser.add_argument("name", help="Template name")
    create_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    create_parser.set_defaults(func=handle_template_create)

    # 'template upgrade' command
    upgrade_parser = template_subparsers.add_parser("upgrade", help="Upgrade a template to the current CLI version")
    upgrade_parser.add_argument("name", help="Template name to upgrade")
    upgrade_parser.add_argument("-y", "--yes", action="store_true", help="Automatically answer yes to all prompts")
    upgrade_parser.add_argument(
        "-f", "--force", action="store_true", help="Force full upgrade with interactive prompts for missing variables"
    )
    upgrade_parser.set_defaults(func=handle_template_upgrade)


def ensure_templates_dir():
    """Ensure templates directory exists."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def handle_template_save(args):
    """Handle the template save command."""
    project_root = args.project_root or os.getcwd()
    save_template(project_root, args.name)


def handle_template_load(args):
    """Handle the template load command."""
    project_root = args.project_root or os.getcwd()
    load_template(project_root, args.name)


def handle_template_list(args):
    """Handle the template list command."""
    list_templates()


def handle_template_delete(args):
    """Handle the template delete command."""
    for name in args.names:
        delete_template(name)


def handle_template_create(args):
    """Handle the template create command."""
    create_new_template(args.name)


def create_new_template(template_name):
    """Create a new template interactively."""
    from caylent_devcontainer_cli.commands.setup_interactive import create_template_interactive, save_template_to_file

    ensure_templates_dir()

    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    # Check if template already exists
    if os.path.exists(template_path):
        if not confirm_action(f"Template '{template_name}' already exists. Overwrite?"):
            log("INFO", "Template creation cancelled")
            return

    log("INFO", f"Creating new template '{template_name}'")

    # Use current CLI version
    template_data = create_template_interactive()
    save_template_to_file(template_data, template_name)

    log("OK", f"Template '{template_name}' created successfully")


def handle_template_upgrade(args):
    """Handle the template upgrade command."""
    upgrade_template_file(args.name, force=args.force)


def save_template(project_root, template_name):
    """Save current environment as a template."""
    ensure_templates_dir()
    env_vars_json = os.path.join(project_root, "devcontainer-environment-variables.json")

    if not os.path.exists(env_vars_json):
        log("ERR", f"No devcontainer-environment-variables.json found in {project_root}")
        import sys

        sys.exit(1)

    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    # Ask for confirmation before saving
    if os.path.exists(template_path):
        if not confirm_action(f"This will overwrite the existing template at:\n{template_path}"):
            import sys

            sys.exit(1)
    else:
        if not confirm_action(f"This will create a new template at:\n{template_path}"):
            import sys

            sys.exit(1)

    try:
        log("INFO", f"Saving template from {env_vars_json}")

        # Read the environment variables file
        with open(env_vars_json, "r") as f:
            env_data = json.load(f)

        # Add CLI version information
        env_data["cli_version"] = __version__

        # Write to template file
        with open(template_path, "w") as f:
            json.dump(env_data, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"Template saved as: {template_name} at {template_path}")
    except Exception as e:
        log("ERR", f"Failed to save template: {e}")
        import sys

        sys.exit(1)


def load_template(project_root, template_name):
    """Load a template into the current project."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        import sys

        sys.exit(1)

    env_vars_json = os.path.join(project_root, "devcontainer-environment-variables.json")

    # Ask for confirmation before loading
    if os.path.exists(env_vars_json):
        if not confirm_action(f"This will overwrite your existing configuration at:\n{env_vars_json}"):
            import sys

            sys.exit(1)
    else:
        if not confirm_action(f"This will create a new configuration at:\n{env_vars_json}"):
            import sys

            sys.exit(1)

    try:
        # Read the template file
        with open(template_path, "r") as f:
            template_data = json.load(f)

        # Check version compatibility
        if "cli_version" in template_data:
            template_version = template_data["cli_version"]
            current_version = __version__

            try:
                # Parse versions using semver
                template_semver = semver.VersionInfo.parse(template_version)
                current_semver = semver.VersionInfo.parse(current_version)

                # Check if major versions differ
                if template_semver.major < current_semver.major:
                    log(
                        "WARN",
                        f"Template was created with CLI version {template_version}, "
                        f"but you're using version {current_version}",
                    )
                    print("\nPlease choose one of the following options:")
                    print("1. Upgrade the profile to the current version")
                    print("2. Create a new profile from scratch")
                    print("3. Try to use the profile anyway (may fail)")
                    print("4. Exit and revert changes")

                    while True:
                        choice = input("\nEnter your choice (1-4): ").strip()
                        if choice == "1":
                            # Upgrade the template
                            template_data = upgrade_template(template_data)
                            log("OK", f"Template upgraded to version {current_version}")
                            break
                        elif choice == "2":
                            log("INFO", "Please use 'cdevcontainer template save' to create a new profile")
                            import sys

                            sys.exit(0)
                        elif choice == "3":
                            if not confirm_action("The template format may be incompatible. Continue anyway?"):
                                log("INFO", "Operation cancelled by user")
                                import sys

                                sys.exit(0)
                            break
                        elif choice == "4":
                            log("INFO", "Operation cancelled by user")
                            import sys

                            sys.exit(0)
                        else:
                            print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                # If version parsing fails, just continue with the template as is
                log("WARN", f"Could not parse template version: {template_version}")

        # Write to environment variables file
        with open(env_vars_json, "w") as f:
            json.dump(template_data, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log("OK", f"Template '{template_name}' loaded to {env_vars_json}")
    except Exception as e:
        log("ERR", f"Failed to load template: {e}")
        import sys

        sys.exit(1)


def list_templates():
    """List available templates."""
    ensure_templates_dir()
    templates = []

    for f in os.listdir(TEMPLATES_DIR):
        if f.endswith(".json"):
            template_name = f.replace(".json", "")
            template_path = os.path.join(TEMPLATES_DIR, f)

            # Try to get version information
            version = "unknown"
            try:
                with open(template_path, "r") as file:
                    data = json.load(file)
                    if "cli_version" in data:
                        version = data["cli_version"]
            except Exception:
                pass

            templates.append((template_name, version))

    if not templates:
        from caylent_devcontainer_cli.utils.ui import COLORS

        print(f"{COLORS['YELLOW']}No templates found. Create one with 'template save <n>'{COLORS['RESET']}")
        return

    from caylent_devcontainer_cli.utils.ui import COLORS

    print(f"{COLORS['CYAN']}Available templates:{COLORS['RESET']}")
    for template_name, version in sorted(templates):
        print(f"  - {COLORS['GREEN']}{template_name}{COLORS['RESET']} (created with CLI version {version})")


def delete_template(template_name):
    """Delete a template."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        return

    if not confirm_action(f"Are you sure you want to delete template '{template_name}'?"):
        log("INFO", f"Template '{template_name}' not deleted")
        return

    try:
        os.remove(template_path)
        log("OK", f"Template '{template_name}' deleted successfully")
    except Exception as e:
        log("ERR", f"Failed to delete template: {e}")


def upgrade_template_with_missing_vars(template_data):
    """Upgrade template with interactive prompts for missing variables."""
    from caylent_devcontainer_cli.commands.setup_interactive import upgrade_template

    # First do the standard upgrade
    upgraded_template = upgrade_template(template_data)

    # Check for missing single-line environment variables
    container_env = upgraded_template.get("containerEnv", {})
    missing_vars = get_missing_single_line_vars(container_env)

    if missing_vars:
        log("INFO", f"Found {len(missing_vars)} missing environment variables")
        new_vars = prompt_for_missing_vars(missing_vars)

        # Add the new variables to the container environment
        container_env.update(new_vars)
        upgraded_template["containerEnv"] = container_env

        log("OK", f"Added {len(new_vars)} new environment variables to template")
    else:
        log("INFO", "No missing environment variables found")

    return upgraded_template


def upgrade_template_file(template_name, force=False):
    """Upgrade a template to the current CLI version."""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.json")

    if not os.path.exists(template_path):
        log("ERR", f"Template '{template_name}' not found at {template_path}")
        import sys

        sys.exit(1)

    try:
        # Read the template file
        with open(template_path, "r") as f:
            template_data = json.load(f)

        # Check if force upgrade is requested
        if force:
            log("INFO", "Force upgrade requested - performing full upgrade with missing variable detection")
            upgraded_template = upgrade_template_with_missing_vars(template_data)
        else:
            # Check if upgrade is needed
            if "cli_version" in template_data:
                template_version = template_data["cli_version"]
                current_version = __version__

                try:
                    # Parse versions using semver
                    template_semver = semver.VersionInfo.parse(template_version)
                    current_semver = semver.VersionInfo.parse(current_version)

                    if template_semver.major == current_semver.major and template_semver.minor == current_semver.minor:
                        # Even if the major and minor versions match, ensure the cli_version is updated
                        template_data["cli_version"] = __version__
                        with open(template_path, "w") as f:
                            json.dump(template_data, f, indent=2)
                            f.write("\n")  # Add newline at end of file
                        log(
                            "INFO",
                            f"Template '{template_name}' version updated from {template_version} to {__version__}",
                        )
                        return
                except ValueError:
                    # If version parsing fails, proceed with upgrade
                    pass

            # Upgrade the template
            upgraded_template = upgrade_template(template_data)

        # Write back to the template file
        with open(template_path, "w") as f:
            json.dump(upgraded_template, f, indent=2)
            f.write("\n")  # Add newline at end of file

        log(
            "OK",
            f"Template '{template_name}' upgraded from version "
            f"{template_data.get('cli_version', 'unknown')} to {__version__}",
        )
    except Exception as e:
        log("ERR", f"Failed to upgrade template: {e}")
        import sys

        sys.exit(1)

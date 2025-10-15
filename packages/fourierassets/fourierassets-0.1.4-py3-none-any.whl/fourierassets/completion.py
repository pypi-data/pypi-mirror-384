import os

from .logger import get_logger


def setup_bash_completion():
    """Setup bash completion for fourierassets command."""
    try:
        # Check if argcomplete is available
        import importlib.util

        if importlib.util.find_spec("argcomplete"):
            bashrc_path = os.path.expanduser("~/.bashrc")
            completion_line = 'alias register-python-argcomplete="register-python-argcomplete3"\neval "$(register-python-argcomplete fourierassets)"'
            # Check if completion is already configured
            if os.path.exists(bashrc_path):
                with open(bashrc_path) as f:
                    content = f.read()

                additions = []
                if completion_line not in content:
                    additions.append(completion_line)

                if additions:
                    print("Adding bash completion for fourierassets to ~/.bashrc")
                    with open(bashrc_path, "a") as f:
                        f.write("\n# Auto-completion for fourierassets\n")
                        for line in additions:
                            f.write(f"{line}\n")

                    print(
                        "Bash completion setup completed. Please restart your shell or run 'source ~/.bashrc'"
                    )
                    print("Then try: fourierassets <TAB><TAB>")
                    return True
                else:
                    print("Bash completion for fourierassets already configured")
                    return True
            else:
                print("~/.bashrc not found, skipping completion setup")
                return False
        else:
            raise ImportError("argcomplete not found")

    except Exception as e:
        print(f"Could not setup bash completion: {e}")
        return False


def main():
    """Main entry point for completion setup."""
    logger = get_logger("completion")
    if setup_bash_completion():
        print("Bash completion setup completed!")
        print("Please restart your shell or run 'source ~/.bashrc'")
        return 0
    else:
        logger.error("Failed to setup bash completion.")
        return 1

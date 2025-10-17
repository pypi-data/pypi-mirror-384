import argparse

command = "shell"
command_help = "Open an interactive IPython shell with Solidipes loaded"


def print_banner() -> None:
    import platform

    import IPython

    import solidipes
    from solidipes.plugins.management import get_installed_plugins_info

    print(f"Python {platform.python_version()}, IPython {IPython.__version__}, Solidipes {solidipes.__version__}")
    print("Plugins:")
    plugins_info = get_installed_plugins_info()
    for plugin_info in plugins_info:
        line = f"  - {plugin_info['name']} {plugin_info['version']}"
        if "loaded" in plugin_info and plugin_info["loaded"] != plugin_info["version"]:
            line += f" (loaded {plugin_info['loaded']})"
        print(line)


def main(args) -> None:
    import inspect

    from IPython import start_ipython

    from . import shell_environment

    namespace = {}

    for name, obj in shell_environment.__dict__.items():
        if name.startswith("_"):
            continue
        namespace[name] = obj

    print_banner()
    print("")
    print(inspect.getsource(shell_environment))
    start_ipython(argv=["--no-banner"], user_ns=namespace)


def populate_parser(parser) -> None:
    parser.description = command_help


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    populate_parser(parser)
    args = parser.parse_args()
    main(args)

from abc import ABC
from functools import cache
from typing import Callable

from .config import cloud_connection_timeout, solidipes_dirname


class bcolors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"  # light gray
    BRIGHT_BLACK = "\033[90m"  # dark gray
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class DataRepositoryException(ValueError):
    pass


class classproperty:
    def __init__(self, func: Callable) -> None:
        self.func = func

    def __get__(self, _, owner):
        return self.func(owner)


def find_config_directory(initial_path="", dir_name=solidipes_dirname):
    """Find a directory in the current path or any of its parents."""
    import os

    current_path = os.path.abspath(initial_path)

    while True:
        # Check if current path contains the directory
        test_path = os.path.join(current_path, dir_name)
        if os.path.isdir(test_path):
            return test_path

        # Check if current path is the root
        if current_path == os.path.dirname(current_path):
            break

        # Move up to the parent directory
        current_path = os.path.dirname(current_path)

    raise FileNotFoundError(f'The directory "{dir_name}" was not found in {initial_path} or any of its parents')


def get_solidipes_directory(initial_path=""):
    """Get the path to the .solidipes directory."""
    import os

    try:
        solidipes_directory = find_config_directory(initial_path, solidipes_dirname)

        # If parent directory is user's home, it is invalid (user_solidipes_directory)
        if os.path.dirname(solidipes_directory) == os.path.expanduser("~"):
            raise FileNotFoundError

        return solidipes_directory

    except FileNotFoundError as e:
        raise FileNotFoundError(f'{e}. Please run "solidipes init" at the root directory of your study.')


def get_user_solidipes_directory():
    import os

    path = os.path.join(os.path.expanduser("~"), solidipes_dirname)

    if not os.path.isdir(path):
        if os.path.exists(path):
            raise FileExistsError(f'"{path}" exists but is not a directory. Please remove it.')
        os.mkdir(path)

    return path


def get_study_root_path(initial_path="", **kwargs):
    import os

    return os.path.dirname(get_solidipes_directory(initial_path))


def get_path_relative_to_root(path):
    """Express path relative to study root."""
    import os

    path = os.path.abspath(path)  # Also strips trailing slash
    path = os.path.relpath(path, get_study_root_path())

    return path


def get_path_relative_to_workdir(path):
    """Convert path expressed relative to study root to path expressed relative to current working directory."""
    import os

    path = os.path.join(get_study_root_path(), path)
    path = os.path.relpath(path, os.getcwd())

    return path


def init_git_repository(initial_path=""):
    from git import Repo

    git_repository = Repo.init(get_study_root_path(initial_path))

    return git_repository


def get_git_repository(initial_path=""):
    import os

    from git import Repo

    current_path = os.path.abspath(initial_path)
    git_repository = Repo(current_path, search_parent_directories=True)
    return git_repository


def get_git_root(initial_path=""):
    repo = get_git_repository(initial_path)
    git_root = repo.git.rev_parse("--show-toplevel")
    return git_root


def get_config_path(filename_var, initial_path="", check_existence=False, user=False):
    import os

    current_working_dir = os.getcwd()
    return _get_config_path(current_working_dir, filename_var, initial_path, check_existence, user)


@cache
def _get_config_path(
    current_working_dir,
    filename_var,
    initial_path="",
    check_existence=False,
    user=False,
):
    import os

    from . import config

    filename = getattr(config, filename_var)

    if user:
        config_directory = get_user_solidipes_directory()
    else:
        config_directory = get_solidipes_directory(initial_path)
    path = os.path.join(config_directory, filename)

    if check_existence and not os.path.isfile(path):
        raise FileNotFoundError(
            f'The file "{path}" does not exist. Please run "solidipes init" at the root directory of your study.'
        )

    return path


def load_yaml(filename):
    import yaml

    with open(filename, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f.read())
    if config is None:
        config = {}
    return config


def save_yaml(filename, config):
    import yaml

    with open(filename, "w", encoding="utf-8") as f:
        f.write(yaml.safe_dump(config))

    return config


def get_study_log_path():
    import os

    config_directory = get_solidipes_directory()
    path = os.path.join(config_directory, "solidipes.logs")
    return path


def get_study_metadata_path(*args, **kwargs):
    return get_config_path("study_metadata_filename", *args, **kwargs)


def get_readme_path(*args, **kwargs):
    import os

    from .config import readme_filename

    return os.path.join(get_study_root_path(*args, **kwargs), readme_filename)


def get_study_description_path(*args, **kwargs):
    import os

    from .config import study_description_filename

    return os.path.join(get_study_root_path(*args, **kwargs), study_description_filename)


def get_mimes_path(*args, **kwargs):
    return get_config_path("mimes_filename", *args, **kwargs)


def get_config(filename_var, *args, **kwargs):
    import os

    path = get_config_path(filename_var, *args, **kwargs)
    if not os.path.exists(path):
        return {}
    return load_yaml(path)


def set_config(filename_var, config, *args, **kwargs) -> None:
    path = get_config_path(filename_var, *args, **kwargs)
    save_yaml(path, config)


def populate_metadata_mandatory_fields(metadata) -> None:
    from .config import study_medatada_mandatory_fields as mandatory_fields

    for field in mandatory_fields.keys():
        if field not in metadata:
            metadata[field] = mandatory_fields[field]


def separate_metadata_description(metadata, html_to_md=False, **kwargs) -> None:
    """Remove description from saved yml and put it in a separate file."""
    from markdownify import markdownify

    from .config import description_warning
    from .utils import get_study_description_path

    description = metadata.pop("description", "")  # can be html or md
    if html_to_md:
        description_md = markdownify(description)
    else:
        description_md = description

    description_path = get_study_description_path(**kwargs)
    with open(description_path, "w", encoding="UTF-8") as f:
        f.write(description_md)

    metadata["description"] = description_warning


def include_metadata_description(metadata, generate_readme=False, use_readme=False, md_to_html=False, **kwargs):
    """Update metadata description field with DESCRIPTION.md file."""
    import os

    from markdown import markdown

    from .config import study_description_filename
    from .utils import get_study_description_path

    description_path = get_study_description_path(**kwargs)

    if use_readme:
        generate_readme(with_title=False, **kwargs)
        description_path = get_readme_path(**kwargs)

    # If DESCRIPTION.md does not exist, create it by parsing current description
    if not os.path.isfile(description_path):
        separate_metadata_description(metadata, html_to_md=True, **kwargs)

    # Update metadata
    with open(description_path, "r", encoding="UTF-8") as f:
        description_md = f.read()

        if md_to_html:
            try:
                description = markdown(description_md, tab_length=2, extensions=["tables"])
            except Exception as e:
                raise ValueError(f"Error parsing {study_description_filename}: {e}")
        else:
            description = description_md

        metadata["description"] = description

    # Re-generate readme
    if generate_readme:
        generate_readme(**kwargs)

    return metadata


def add_completed_stage(stage) -> None:
    completed = set(get_completed_stages())
    completed.add(stage)
    set_config("completed_stages_filename", {"completed_stages": list(completed)})


def remove_completed_stage(stage) -> None:
    completed = set(get_completed_stages())
    if stage in completed:
        completed.remove(stage)
    set_config("completed_stages_filename", {"completed_stages": list(completed)})


def get_completed_stages():
    metadata = get_config("completed_stages_filename")
    if metadata == {}:
        return []
    if "completed_stages" not in metadata:
        return []
    return metadata["completed_stages"]


def is_stage_completed(stage):
    return stage in get_completed_stages()


def get_study_metadata(*args, md_to_html=False, **kwargs):
    metadata = get_config("study_metadata_filename", *args, **kwargs)

    include_metadata_description(metadata, md_to_html=md_to_html, **kwargs)
    populate_metadata_mandatory_fields(metadata)

    return metadata


def generate_readme(*args, with_title=True, **kwargs) -> None:
    from .metadata import lang, licenses
    from .utils import get_readme_path

    readme_path = get_readme_path(**kwargs)
    metadata = get_study_metadata(*args, **kwargs)

    content = ""
    try:
        old_readme_content = open(readme_path, "r", encoding="utf-8").read()
    except Exception:
        old_readme_content = ""

    if with_title:
        content += f"# {metadata['title']}\n\n<br>\n\n"
        content += "## Links\n\n"
        if "DOI" in metadata:
            doi = metadata["DOI"]
            content += f"- Data DOI: [{doi}](https://doi.org/{doi})"
        if "related_identifiers" in metadata:
            rels = metadata["related_identifiers"]
            for r in rels:
                if "resource_type" not in r:
                    continue
                content += f"- {r['relation']} *{r['resource_type']}* [{r['identifier']}]({r['identifier']})\n"
            content += "\n"
        content += "## Authors\n\n"
        if "creators" in metadata:
            authors = metadata["creators"]
            for a in authors:
                content += f"- **{a['name']}**"
                if "affiliation" in a:
                    content += f", {a['affiliation']}"
                if "orcid" in a:
                    content += f", ORCID: [{a['orcid']}](https://orcid.org/{a['orcid']})"
                content += "\n"
            content += "\n"

        content += "## Language\n\n"
        if "language" in metadata:
            _lang = dict(lang)[metadata["language"]]
            content += f"- {_lang}\n\n"

        content += "## License\n\n"
        if "license" in metadata:
            lic = metadata["license"]
            if isinstance(lic, dict):
                lic = lic["id"]
            _lic = dict(licenses)[lic.lower()]
            content += f"- {_lic}\n\n"

        content += metadata["description"]

        if content != old_readme_content:
            with open(readme_path, "w", encoding="UTF-8") as f:
                f.write(content)


def set_study_metadata(config, *args, html_to_md=False, **kwargs) -> None:
    config = config.copy()
    separate_metadata_description(
        config, *args, html_to_md=html_to_md, **kwargs
    )  # keep description field empty when saving
    set_config("study_metadata_filename", config, *args, **kwargs)
    generate_readme(*args, **kwargs)


def get_zenodo_infos(*args, **kwargs):
    return get_config("zenodo_infos_filename", *args, **kwargs)


def set_zenodo_infos(config, *args, **kwargs) -> None:
    set_config("zenodo_infos_filename", config, *args, **kwargs)


def get_mimes(*args, **kwargs):
    try:
        return get_config("mimes_filename", *args, **kwargs)
    except FileNotFoundError:
        return {}


def set_mimes(config, *args, **kwargs) -> None:
    set_config("mimes_filename", config, *args, **kwargs)


def get_ignore(*args, **kwargs) -> set[str]:
    from .config import default_ignore_patterns

    ignore: set[str] = set(get_config("ignore_filename", *args, **kwargs))
    ignore = ignore.union(default_ignore_patterns)
    ignore = [e.strip() for e in ignore if e.strip() != ""]

    return ignore


def set_ignore(config: set[str], *args, **kwargs) -> None:
    config = [e.strip() for e in config if e.strip() != ""]
    set_config("ignore_filename", list(config), *args, **kwargs)


def dict_to_pretty_str(d: dict, indent=0, indent_size=4):
    string = ""
    indent_string = " " * indent_size

    for key, value in d.items():
        string += indent_string * indent + str(key) + ": "
        if isinstance(value, dict):
            string += "{\n" + dict_to_pretty_str(value, indent + 1) + indent_string * indent + "}\n"
        else:
            string += str(value) + "\n"

    return string


def transform_data_containers_to_dict(data):
    from ..loaders.data_container import DataContainer, TemporaryFile

    if isinstance(data, TemporaryFile):
        data = {"DataContainer.TemporaryFile": data.getstate()}
    if isinstance(data, DataContainer):
        data = data._data_collection
    if isinstance(data, dict):
        data_res = {}
        for k, v in data.items():
            data_res[k] = transform_data_containers_to_dict(v)
        data = data_res

    return data


def transform_dict_to_data_containers(data):
    from ..loaders.data_container import DataContainer, TemporaryFile

    if isinstance(data, dict) and len(data.keys()) == 1:
        key = [e for e in data.keys()][0]
        if key == "DataContainer.TemporaryFile":
            tmp = TemporaryFile(init=False)
            tmp.setstate(data["DataContainer.TemporaryFile"])
            return tmp
    if isinstance(data, dict):
        data_res = {}
        for k, v in data.items():
            data_res[k] = transform_dict_to_data_containers(v)
        return DataContainer(data_res)

    return data


def rename_file(old_name, new_name) -> None:
    import subprocess

    from solidipes.utils.git_infos import GitInfos

    git_infos = GitInfos()

    if git_infos.repository and get_path_relative_to_root(old_name) not in git_infos.repository.untracked_files:
        cmd = f"git mv {old_name} {new_name}"

    else:
        cmd = f"mv {old_name} {new_name}"

    subprocess.call(cmd, shell=True)


class parameter(property):
    def __init__(self, func, optional=False, last=False) -> None:
        self.optional = optional
        self.key = func.__name__
        self.name_var = "_" + self.key
        self.func = func
        self.last = last
        super().__init__(self.foo, self.foo_setter)
        self.__doc__ = func.__doc__

    def foo(self, obj, *args, **kwargs):
        if not hasattr(obj, self.name_var):
            value = self.func(*args, **kwargs)
            if value is None:
                raise ValueError(f"{self.key} has no default parameter")
            self.foo_setter(obj, value)

        return getattr(obj, self.name_var)

    def foo_setter(self, obj, value, *args, **kwargs) -> None:
        setattr(obj, self.name_var, value)


class optional_parameter(parameter):
    def __init__(self, func) -> None:
        super().__init__(func, optional=True)


class last_parameter(parameter):
    def __init__(self, func) -> None:
        super().__init__(func, last=True)


class last_parameter_with_default(last_parameter):
    def __init__(self, func) -> None:
        super().__init__(func)


def populate_parser(cls, parser) -> None:
    _parameters = dict()
    _groups = dict()
    import typing

    from ..plugins.discovery import apply_to_object_parent_classes

    last_parameters = dict()

    def _register(key, _cls, v):
        if key not in _parameters:
            _parameters[key] = (_cls, v)
        if _cls not in _groups:
            _groups[_cls] = parser.add_argument_group(_cls.__name__)

    def register_to_data_collection(_cls) -> None:
        for key, v in _cls.__dict__.items():
            if isinstance(v, parameter):
                if v.last:
                    last_parameters[key] = (_cls, v)
                    continue
                _register(key, _cls, v)

    apply_to_object_parent_classes(cls, register_to_data_collection)

    for k, (_cls, v) in last_parameters.items():
        _register(k, _cls, v)

    for key, (_cls, v) in _parameters.items():
        func = getattr(_cls, key)
        type_hints = typing.get_type_hints(func.func)
        arg_name = func.key
        if func.optional:
            arg_name = "--" + arg_name

        try:
            ret_type = type_hints["return"]
        except KeyError:
            raise RuntimeError(f"Parameter {cls.__name__}.{key} was not annotated with a return type")

        _parser = _groups[_cls]
        if ret_type is bool:
            if func.func():
                action = "store_false"
            else:
                action = "store_true"

            _parser.add_argument(arg_name, help=func.__doc__, action=action)
        elif isinstance(v, last_parameter_with_default):
            _parser.add_argument(
                arg_name,
                nargs="?",
                default="TBD",
                help=func.__doc__,
                type=type_hints["return"],
            )
        else:
            _parser.add_argument(arg_name, help=func.__doc__, type=type_hints["return"])


def run_and_check_return(
    command,
    headless=False,
    fail_message="Error",
    timeout=cloud_connection_timeout,
    cwd=None,
) -> None:
    import subprocess

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        cwd=cwd,
        input=b"\n" if headless else None,
    )
    check_process_return(process, fail_message)
    stdout = process.stdout.decode().strip()
    stderr = process.stderr.decode().strip()
    return stdout, stderr


class ExecError(RuntimeError):
    pass


def check_process_return(process, fail_message) -> None:
    import subprocess

    try:
        process.check_returncode()

    except subprocess.CalledProcessError as e:
        if e.stderr:
            raise ExecError(f"{fail_message}: {e.stderr.decode()}")
        else:
            raise ExecError(fail_message)


def compute_checksum(filepath: str) -> str:
    import hashlib

    with open(filepath, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def get_key_to_parsables(name, cls):
    from solidipes.plugins.discovery import (
        get_subclasses_from_plugins,
        plugin_package_names,
    )

    parsable_subclasses = get_subclasses_from_plugins(plugin_package_names, name, cls)
    key_to_parsable = {}
    for e in parsable_subclasses:
        if e.parser_key is None:
            continue
        if not isinstance(e.parser_key, list):
            e.parser_key = [e.parser_key]
        for k in e.parser_key:
            key_to_parsable[k] = e

    return key_to_parsable


################################################################


class Parsable(ABC):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if v == "TBD":
                continue
            if v is not None:
                setattr(self, k, v)

    @classmethod
    def populate_parser(cls, parser) -> None:
        populate_parser(cls, parser)

    @classmethod
    def run_and_check_return(cls, command, **kwargs) -> None:
        return run_and_check_return(command, **kwargs)

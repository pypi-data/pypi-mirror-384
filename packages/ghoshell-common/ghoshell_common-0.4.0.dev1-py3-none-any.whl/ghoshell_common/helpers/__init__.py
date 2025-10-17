from typing import TYPE_CHECKING
from ghoshell_common.helpers.dictionary import (dict_without_none, dict_without_zero)
from ghoshell_common.helpers.string import camel_to_snake
from ghoshell_common.helpers.yaml import yaml_pretty_dump, yaml_multiline_string_pipe
from ghoshell_common.helpers.modules import (
    import_from_path,
    import_class_from_path,
    import_instance_from_path,
    parse_import_path_module_and_attr_name,
    join_import_module_and_spec,
    get_module_attr,
    generate_module_and_attr_name,
    generate_import_path,
    get_module_fullname_from_path,
    Importer,
    is_method_belongs_to_class,
    get_calling_modulename,
    rewrite_module,
    rewrite_module_by_path,
    create_module,
    create_and_bind_module,
)
from ghoshell_common.helpers.io import BufferPrint
from ghoshell_common.helpers.timeutils import Timeleft, timestamp_datetime, timestamp, timestamp_ms
from ghoshell_common.helpers.hashes import md5, sha1, sha256
from ghoshell_common.helpers.trans import gettext, ngettext

from ghoshell_common.helpers.coding import reflect_module_code, unwrap
from ghoshell_common.helpers.openai import get_openai_key
from ghoshell_common.helpers.tree_sitter import tree_sitter_parse, code_syntax_check
from ghoshell_common.helpers.code_analyser import (
    get_code_interface, get_code_interface_str,
    get_attr_source_from_code, get_attr_interface_from_code,
)
from ghoshell_common.helpers.files import generate_directory_tree, list_dir, is_pathname_ignored

if TYPE_CHECKING:
    from typing import Callable


# --- private methods --- #
def __uuid() -> str:
    from uuid import uuid4
    # keep uuid in 32 chars
    return str(uuid4())


# --- facade --- #

uuid: "Callable[[], str]" = __uuid
""" patch this method to change global uuid generator"""


def uuid_md5() -> str:
    return md5(uuid())

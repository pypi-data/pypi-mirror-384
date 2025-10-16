"""UUID transform plugin module"""

import re
import uuid
from collections.abc import Sequence

import uuid6
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.plugins import TransformPlugin
from cmem_plugin_base.dataintegration.types import BoolParameterType

from cmem_plugin_uuid.utils import (
    clock_seq_to_int,
    get_namespace_uuid,
    namespace_hex,
    node_to_int,
    uuid3_uuid5_namespace_param,
    uuid_convert_param_in,
    uuid_convert_param_out,
)


@Plugin(
    label="UUID1",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv1 from a host ID, sequence number, and the current time",
    documentation="""
UUIDv1 is generated from a host ID, sequence number, and the current
time.

""",
    parameters=[
        PluginParameter(
            name="node",
            label="Node (default: hardware address)",
            description=(
                'Node value in the form "01:23:45:67:89:AB", 01-23-45-67-89-AB", or '
                '"0123456789AB". If not given, it is attempted to obtain the hardware '
                "address. If this is unsuccessful, a random 48-bit number is chosen."
            ),
            default_value=None,
        ),
        PluginParameter(
            name="clock_seq",
            label="Clock sequence (default: random)",
            description=(
                "If clock sequence is given, it is used as the sequence number. "
                "Otherwise a random 14-bit sequence number is chosen."
            ),
            default_value=None,
        ),
    ],
)
class UUID1(TransformPlugin):
    """UUID1 Transform Plugin"""

    def __init__(
        self,
        node: str,
        clock_seq: str,
    ):
        self.node = node_to_int(node) if node else None
        self.clock_seq = clock_seq_to_int(clock_seq) if clock_seq else None

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [
                    str(uuid.uuid1(node=self.node, clock_seq=self.clock_seq)) for _ in collection
                ]
        else:
            result = [str(uuid.uuid1(node=self.node, clock_seq=self.clock_seq))]
        return result


@Plugin(
    label="UUID3",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv3",
    documentation="""UUID3 is based on the MD5 hash of a namespace identifier (which
    is a UUID) and a name (which is a string).""",
    parameters=[
        PluginParameter(
            param_type=uuid3_uuid5_namespace_param,
            name="namespace",
            label="Namespace",
            description="The namespace.",
            default_value="",
        ),
        PluginParameter(
            param_type=BoolParameterType(),
            name="namespace_as_uuid",
            label="Namespace as UUID",
            description=(
                "Applies only if none of the pre-defined namespaces is selected. If "
                "enabled, the namespace string needs to be a valid UUID. "
                "Otherwise, the namespace UUID is a UUIDv1 derived from the MD5 hash "
                "of the namespace string."
            ),
            default_value=False,
        ),
    ],
)
class UUID3(TransformPlugin):
    """UUID3 Transform Plugin"""

    def __init__(
        self,
        namespace: str,
        namespace_as_uuid: bool | None,
    ):
        self.namespace = namespace
        self.namespace_as_uuid = namespace_as_uuid

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        namespace_uuid = get_namespace_uuid(
            namespace_as_uuid=self.namespace_as_uuid,
            namespace=self.namespace,
            uuid_version=3,
        )

        if len(inputs) != 0:
            for collection in inputs:
                for _ in collection:
                    if not self.namespace.strip():
                        result += [str(uuid.UUID(hex=namespace_hex(_, 3), version=3))]
                    else:
                        result += [str(uuid.uuid3(namespace_uuid, _))]  # type: ignore[arg-type]
        return result


@Plugin(
    label="UUID4",
    categories=["Value", "Identifier"],
    description="Generate a random UUIDv4.",
    documentation="""UUIDv4 specifies a random UUID.""",
)
class UUID4(TransformPlugin):
    """UUID4 Transform Plugin"""

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [str(uuid.uuid4()) for _ in collection]
        else:
            result = [str(uuid.uuid4())]
        return result


@Plugin(
    label="UUID5",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv5",
    documentation="""UUID5 is based on the SHA1 hash of a namespace identifier (which
    is a UUID) and a name (which is a string).""",
    parameters=[
        PluginParameter(
            param_type=uuid3_uuid5_namespace_param,
            name="namespace",
            label="Namespace",
            description="If 'namespace' is not given, the input string is used.",
            default_value="",
        ),
        PluginParameter(
            param_type=BoolParameterType(),
            name="namespace_as_uuid",
            label="Namespace as UUID",
            description=(
                "Applies only if none of the pre-defined namespaces is selected. If "
                "enabled, the namespace string needs to be a valid UUID. "
                "Otherwise, the namespace UUID is a UUIDv1 derived from the SHA1 hash "
                "of the namespace string."
            ),
            default_value=False,
        ),
    ],
)
class UUID5(TransformPlugin):
    """UUID5 Transform Plugin"""

    def __init__(
        self,
        namespace: str,
        namespace_as_uuid: bool | None,
    ):
        self.namespace = namespace
        self.namespace_as_uuid = namespace_as_uuid

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        namespace_uuid = get_namespace_uuid(
            namespace_as_uuid=self.namespace_as_uuid,
            namespace=self.namespace,
            uuid_version=5,
        )

        if len(inputs) != 0:
            for collection in inputs:
                for _ in collection:
                    if not self.namespace.strip():
                        result += [str(uuid.UUID(hex=namespace_hex(_, 5), version=5))]
                    else:
                        result += [str(uuid.uuid5(namespace_uuid, _))]  # type: ignore[arg-type]
        return result


@Plugin(
    label="UUID6",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv6 from a host ID, sequence number, and the current time",
    documentation="""
UUIDv6 is generated from a host ID, sequence number, and the current
time.

UUIDv6 is a field-compatible version of UUIDv1, reordered for
improved DB locality. It is expected that UUIDv6 will primarily be
used in contexts where there are existing v1 UUIDs. Systems that do
not involve legacy UUIDv1 SHOULD consider using UUIDv7 instead.
""",
    parameters=[
        PluginParameter(
            name="node",
            label="Node (default: hardware address)",
            description=(
                'Node value in the form "01:23:45:67:89:AB", 01-23-45-67-89-AB", or '
                '"0123456789AB". If not given, a random 48-bit number is chosen.'
            ),
            default_value="",
        ),
        PluginParameter(
            name="clock_seq",
            label="Clock sequence (default: random)",
            description=(
                "If clock sequence is given, it is used as the sequence number. "
                "Otherwise a random 14-bit number is chosen."
            ),
            default_value="",
        ),
    ],
)
class UUID6(TransformPlugin):
    """UUID6 Transform Plugin"""

    def __init__(
        self,
        node: str,
        clock_seq: str,
    ):
        self.node = node_to_int(node) if node else None
        self.clock_seq = clock_seq_to_int(clock_seq) if clock_seq else None

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [
                    str(uuid6.uuid6(node=self.node, clock_seq=self.clock_seq)) for _ in collection
                ]
        else:
            result = [str(uuid6.uuid6(node=self.node, clock_seq=self.clock_seq))]
        return result


@Plugin(
    label="UUID1 to UUID6",
    categories=["Value", "Identifier"],
    description="Generate UUIDv6 from a UUIDv1.",
    documentation="""
UUIDv6 is a field-compatible version of UUIDv1, reordered for
improved DB locality. It is expected that UUIDv6 will primarily be
used in contexts where there are existing v1 UUIDs. Systems that do
not involve legacy UUIDv1 SHOULD consider using UUIDv7 instead.
""",
)
class UUID1ToUUID6(TransformPlugin):
    """UUID1 to UUID6 Transform Plugin"""

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                for _ in collection:
                    try:
                        result += [str(uuid6.uuid1_to_uuid6(uuid.UUID(_)))]
                    except ValueError as exc:
                        raise ValueError(f"{_} is not a valid UUIDv1 string") from exc
        return result


@Plugin(
    label="UUID7",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv7 from a random number, and the current time.",
    documentation="""UUIDv7 features a time-ordered value field derived from the
widely implemented and well known Unix Epoch timestamp source, the
number of milliseconds since midnight 1 Jan 1970 UTC, leap seconds
excluded. As well as improved entropy characteristics over versions
1 or 6.
Implementations SHOULD utilize UUIDv7 over UUIDv1 and
6 if possible.
""",
)
class UUID7(TransformPlugin):
    """UUID7 Transform Plugin"""

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [str(uuid6.uuid7()) for _ in collection]
        else:
            result = [str(uuid6.uuid7())]
        return result


@Plugin(
    label="UUID8",
    categories=["Value", "Identifier"],
    description="Generate a UUIDv8 from a random number, and the current time.",
    documentation="""UUIDv8 features a time-ordered value field derived from the
widely implemented and well known Unix Epoch timestamp source, the
number of nanoseconds since midnight 1 Jan 1970 UTC, leap seconds
excluded.
""",
)
class UUID8(TransformPlugin):
    """UUID8 Transform Plugin"""

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [str(uuid6.uuid8()) for _ in collection]
        else:
            result = [str(uuid6.uuid8())]
        return result


@Plugin(
    label="UUID Convert",
    categories=["Value", "Identifier"],
    description="Convert a UUID string representation",
    documentation="""Convert a UUID string with 32 hexadecimal digits to a 16-byte
    string containing the six integer fields in big-endian byte order, a 16-byte string
    the six integer fields in little-endian byte order, a 32-character lowercase
    hexadecimal string, a 128-bit integer, or a URN. Strings in the correct format,
    however, the log will show a warning if the input does not comply with the standard
    specified in RFC 4122 and the proposed updates""",
    parameters=[
        PluginParameter(
            param_type=uuid_convert_param_in,
            name="from_format",
            label="From",
            description="Input string format",
            default_value="uuid_hex",
        ),
        PluginParameter(
            param_type=uuid_convert_param_out,
            name="to_format",
            label="To",
            description="Output string format",
            default_value="hex",
        ),
    ],
)
class UUIDConvert(TransformPlugin):
    """Converts UUID representation"""

    def __init__(self, from_format: str = "uuid_hex", to_format: str = "hex") -> None:
        self.from_ = from_format
        self.to = to_format

        self.uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        self.urn_pattern = (
            r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )

    def convert_uuid(self, uuid_string: str) -> str:  # noqa: C901
        """Convert UUID string"""
        match self.from_:
            case "uuid_hex":
                try:
                    in_uuid = uuid.UUID(uuid_string)
                except ValueError as exc:
                    raise ValueError(f"{uuid_string} is not a valid 32-bit UUID string") from exc
            case "int":
                try:
                    in_uuid = uuid.UUID(int=int(uuid_string))
                except ValueError as exc:
                    raise ValueError(
                        f"{uuid_string} is not a valid 128-bit integer UUID value"
                    ) from exc
            case "urn":
                uuid_string = uuid_string.lower()
                if not re.match(self.urn_pattern, uuid_string):
                    raise ValueError(f"{uuid_string} is not a valid UUID URN")
                in_uuid = uuid.UUID(uuid_string)

        if not re.match(self.uuid_pattern, str(in_uuid)):
            self.log.warning(
                f"{uuid_string} is not a valid UUID as specified in RFC 4122 and "
                f"the proposed updates"
            )

        match self.to:
            case "uuid":
                result = str(in_uuid)
            case "hex":
                result = str(in_uuid.hex)
            case "int":
                result = str(in_uuid.int)
            case "urn":
                result = str(in_uuid.urn)

        return result

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Trasnform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [self.convert_uuid(_) for _ in collection]
        return result


@Plugin(
    label="UUID Version",
    categories=["Value", "Identifier"],
    description="Outputs UUID version number of input",
    documentation="""Input: UUID string, output: UUID version number of input.""",
)
class UUIDVersion(TransformPlugin):
    """Outputs UUID version number"""

    def transform(self, inputs: Sequence[Sequence[str]]) -> Sequence[str]:
        """Transform"""
        result = []
        if len(inputs) != 0:
            for collection in inputs:
                result += [str(uuid.UUID(_).version) for _ in collection]
        return result

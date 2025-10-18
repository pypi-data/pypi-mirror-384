from collections.abc import Mapping, Sequence
import enum
import os
from typing import overload

from . import enums as enums, messages as messages


from typing import Iterator

class ENCODE_FORMAT(enum.IntEnum):
    """Formats which a novatel message can be encoded to."""

    def __str__(self) -> object: ...

    FLATTENED_BINARY = 0
    """
    NovAtel EDIE "Flattened" binary format.  All strings/arrays are padded to maximum length to allow programmatic access.
    """

    ASCII = 1
    """
    NovAtel ASCII. If the log was decoded from a SHORT/compressed format, it will be encoded to the respective SHORT/compressed format.
    """

    ABBREV_ASCII = 2
    """NovAtel Abbreviated ASCII."""

    BINARY = 3
    """
    NovAtel Binary. If the log was decoded from a SHORT/compressed format, it will be encoded to the respective SHORT/compressed format.
    """

    JSON = 4
    """A JSON object.  See HTML documentation for information on fields."""

    UNSPECIFIED = 5
    """No encode format was specified."""

class TIME_STATUS(enum.IntEnum):
    """Indications of how well a GPS reference time is known."""

    def __str__(self) -> object: ...

    UNKNOWN = 20
    """Time validity is unknown."""

    APPROXIMATE = 60
    """Time is set approximately."""

    COARSEADJUSTING = 80
    """Time is approaching coarse precision."""

    COARSE = 100
    """This time is valid to coarse precision."""

    COARSESTEERING = 120
    """Time is coarse set and is being steered."""

    FREEWHEELING = 130
    """Position is lost and the range bias cannot be calculated."""

    FINEADJUSTING = 140
    """Time is adjusting to fine precision."""

    FINE = 160
    """Time has fine precision."""

    FINEBACKUPSTEERING = 170
    """Time is fine set and is being steered by the backup system."""

    FINESTEERING = 180
    """Time is fine set and is being steered."""

    SATTIME = 200
    """
    Time from satellite. Only used in logs containing satellite data such as ephemeris and almanac.
    """

    EXTERN = 220
    """Time source is external to the Receiver."""

    EXACT = 240
    """Time is exact."""

class MESSAGE_FORMAT(enum.IntEnum):
    """Message formats supported natively by a novatel reciever."""

    def __str__(self) -> object: ...

    BINARY = 0
    """Binary format."""

    ASCII = 1
    """ASCII format."""

    ABBREV = 2
    """Abbreviated ASCII format."""

    RSRVD = 3
    """Format reserved for future use."""

class MESSAGE_TYPE_MASK(enum.IntEnum):
    """
    Bitmasks for extracting data from binary `message type` fields which appear within novatel headers and certain logs.
    """

    def __str__(self) -> object: ...

    MEASSRC = 31
    """Bitmask for extracting the source of message."""

    MSGFORMAT = 96
    """Bitmask for extracting the format of a message."""

    RESPONSE = 128
    """Bitmask for extracting the response status of a message."""

class MESSAGE_ID_MASK(enum.IntEnum):
    """
    Bitmasks for extracting data from `message id` and `message type` fields which appear within novatel headers and certain logs.
    """

    def __str__(self) -> object: ...

    LOGID = 65535
    """Bitmask for extracting the id of message/log."""

    MEASSRC = 2031616
    """Bitmask for extracting the source of message."""

    MSGFORMAT = 6291456
    """Bitmask for extracting the format of a message."""

    RESPONSE = 8388608
    """Bitmask for extracting the response status of a message."""

class MEASUREMENT_SOURCE(enum.IntEnum):
    """Origins for a message."""

    def __str__(self) -> object: ...

    PRIMARY = 0
    """Originates from primary antenna."""

    SECONDARY = 1
    """Originates from secondary antenna."""

    MAX = 2

class SatelliteId:
    def __init__(self) -> None: ...

    def to_dict(self) -> dict: ...

    @property
    def prn(self) -> int:
        """The satellite PRN for GPS or the slot for GLONASS."""

    @prn.setter
    def prn(self, arg: int, /) -> None: ...

    @property
    def prn_or_slot(self) -> int:
        """DEPRECATED: Use 'prn' field instead."""

    @prn_or_slot.setter
    def prn_or_slot(self, arg: int, /) -> None: ...

    @property
    def frequency_channel(self) -> int:
        """
        The frequency channel if it is a GLONASS satilite, otherwise left as zero.
        """

    @frequency_channel.setter
    def frequency_channel(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

MAX_MESSAGE_LENGTH: int = 32768

MAX_ASCII_MESSAGE_LENGTH: int = 32768

MAX_BINARY_MESSAGE_LENGTH: int = 32768

MAX_SHORT_ASCII_MESSAGE_LENGTH: int = 32768

MAX_SHORT_BINARY_MESSAGE_LENGTH: int = 271

MAX_ABB_ASCII_RESPONSE_LENGTH: int = 32768

MAX_NMEA_MESSAGE_LENGTH: int = 256

CPP_VERSION: str = '3.9.9'

GIT_SHA: str = '0000000000000000'

GIT_BRANCH: str = ''

GIT_IS_DIRTY: bool = False

BUILD_TIMESTAMP: str = '0000-00-00T00:00:00'

CPP_PRETTY_VERSION: str = 'Version: 3.9.9\nBranch: \nSHA: 0000000000000000'

def calculate_crc(arg: bytes, /) -> int: ...

def disable_internal_logging() -> None:
    """Disable logging which originates from novatel_edie's native C++ code."""

def enable_internal_logging() -> None:
    """Enable logging which originates from novatel_edie's native C++ code."""

class DATA_TYPE(enum.IntEnum):
    """The concrete data types of base-level message fields."""

    def __str__(self) -> object: ...

    BOOL = 0

    CHAR = 1

    UCHAR = 2

    SHORT = 3

    USHORT = 4

    INT = 5

    UINT = 6

    LONG = 7

    ULONG = 8

    LONGLONG = 9

    ULONGLONG = 10

    FLOAT = 11

    DOUBLE = 12

    HEXBYTE = 13

    SATELLITEID = 14

    UNKNOWN = 15

class FIELD_TYPE(enum.IntEnum):
    """The abstracted types of a message field."""

    def __str__(self) -> object: ...

    SIMPLE = 0
    """A value with a simple data type such as a integer or float."""

    ENUM = 1
    """An enum value."""

    BITFIELD = 2
    """A bitfield value."""

    FIXED_LENGTH_ARRAY = 3
    """An array with a pre-determined length."""

    VARIABLE_LENGTH_ARRAY = 4
    """An array whose length length may differ across different messages."""

    STRING = 5
    """A string value."""

    FIELD_ARRAY = 6
    """An array of complex fields with their own sub-fields."""

    RESPONSE_ID = 7
    """A fabricated response ID."""

    RESPONSE_STR = 8
    """A fabricated response string."""

    RXCONFIG_HEADER = 9
    """A fabricated RXCONFIG header."""

    RXCONFIG_BODY = 10
    """A fabricated RXCONFIG body."""

    UNKNOWN = 11
    """A value with an unknown type."""

str_to_FIELD_TYPE: dict = ...

class EnumDataType:
    """Enum Data Type representing contents of UI DB"""

    def __init__(self) -> None: ...

    @property
    def value(self) -> int: ...

    @value.setter
    def value(self, arg: int, /) -> None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def description(self) -> str: ...

    @description.setter
    def description(self, arg: str, /) -> None: ...

    def __repr__(self) -> str: ...

class EnummeratorDefinition:
    """Enum Definition representing contents of UI DB"""

    def __init__(self) -> None: ...

    @property
    def id(self) -> str: ...

    @id.setter
    def id(self, arg: str, /) -> None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def enumerators(self) -> list[EnumDataType]: ...

    @enumerators.setter
    def enumerators(self, arg: Sequence[EnumDataType], /) -> None: ...

    def __repr__(self) -> str: ...

class BaseDataType:
    """Struct containing basic elements of data type fields in the UI DB"""

    def __init__(self) -> None: ...

    @property
    def name(self) -> DATA_TYPE: ...

    @name.setter
    def name(self, arg: DATA_TYPE, /) -> None: ...

    @property
    def length(self) -> int: ...

    @length.setter
    def length(self, arg: int, /) -> None: ...

    @property
    def description(self) -> str: ...

    @description.setter
    def description(self, arg: str, /) -> None: ...

class SimpleDataType(BaseDataType):
    """Struct containing elements of simple data type fields in the UI DB"""

    def __init__(self) -> None: ...

    @property
    def enums(self) -> dict[int, EnumDataType]: ...

    @enums.setter
    def enums(self, arg: Mapping[int, EnumDataType], /) -> None: ...

class FieldDefinition:
    """Struct containing elements of basic fields in the UI DB"""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, name: str, type: FIELD_TYPE, conversion: str, length: int, data_type: DATA_TYPE) -> None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def type(self) -> FIELD_TYPE: ...

    @type.setter
    def type(self, arg: FIELD_TYPE, /) -> None: ...

    @property
    def description(self) -> str: ...

    @description.setter
    def description(self, arg: str, /) -> None: ...

    @property
    def conversion(self) -> str: ...

    @conversion.setter
    def conversion(self, arg: str, /) -> None: ...

    @property
    def width(self) -> "std::optional<int>": ...

    @width.setter
    def width(self, arg: "std::optional<int>", /) -> None: ...

    @property
    def precision(self) -> "std::optional<int>": ...

    @precision.setter
    def precision(self, arg: "std::optional<int>", /) -> None: ...

    @property
    def data_type(self) -> SimpleDataType: ...

    @data_type.setter
    def data_type(self, arg: SimpleDataType, /) -> None: ...

    def set_conversion(self, conversion: str) -> None: ...

    def __repr__(self) -> str: ...

class EnumFieldDefinition(FieldDefinition):
    """Struct containing elements of enum fields in the UI DB"""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, name: str, enumerators: Sequence[EnumDataType]) -> None: ...

    @property
    def enum_id(self) -> str: ...

    @enum_id.setter
    def enum_id(self, arg: str, /) -> None: ...

    @property
    def enum_def(self) -> EnummeratorDefinition: ...

    @enum_def.setter
    def enum_def(self, arg: EnummeratorDefinition, /) -> None: ...

    @property
    def length(self) -> int: ...

    @length.setter
    def length(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class ArrayFieldDefinition(FieldDefinition):
    """Struct containing elements of array fields in the UI DB"""

    def __init__(self) -> None: ...

    @property
    def array_length(self) -> int: ...

    @array_length.setter
    def array_length(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class FieldArrayFieldDefinition(FieldDefinition):
    """Struct containing elements of field array fields in the UI DB"""

    def __init__(self) -> None: ...

    @property
    def array_length(self) -> int: ...

    @array_length.setter
    def array_length(self, arg: int, /) -> None: ...

    @property
    def field_size(self) -> int: ...

    @field_size.setter
    def field_size(self, arg: int, /) -> None: ...

    @property
    def fields(self) -> list[FieldDefinition]: ...

    @fields.setter
    def fields(self, arg: Sequence[FieldDefinition], /) -> None: ...

    def __repr__(self) -> str: ...

class MessageDefinition:
    """Struct containing elements of message definitions in the UI DB"""

    def __init__(self) -> None: ...

    @property
    def id(self) -> str: ...

    @id.setter
    def id(self, arg: str, /) -> None: ...

    @property
    def log_id(self) -> int: ...

    @log_id.setter
    def log_id(self, arg: int, /) -> None: ...

    @property
    def name(self) -> str: ...

    @name.setter
    def name(self, arg: str, /) -> None: ...

    @property
    def description(self) -> str: ...

    @description.setter
    def description(self, arg: str, /) -> None: ...

    @property
    def fields(self) -> dict: ...

    @property
    def latest_message_crc(self) -> int: ...

    @latest_message_crc.setter
    def latest_message_crc(self, arg: int, /) -> None: ...

    def __repr__(self) -> str: ...

class MessageDatabase:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, file_path: str | os.PathLike) -> None: ...

    @staticmethod
    def from_string(json_data: str) -> MessageDatabase: ...

    def merge(self, other_db: "novatel::edie::MessageDatabase") -> None: ...

    def append_messages(self, messages: Sequence[MessageDefinition]) -> None: ...

    def append_enumerations(self, enums: Sequence[EnummeratorDefinition]) -> None: ...

    def remove_message(self, msg_id: int) -> None: ...

    def remove_enumeration(self, enumeration: str) -> None: ...

    @overload
    def get_msg_def(self, msg_name: str) -> MessageDefinition: ...

    @overload
    def get_msg_def(self, msg_id: int) -> MessageDefinition: ...

    @overload
    def get_enum_def(self, enum_id: str) -> EnummeratorDefinition: ...

    @overload
    def get_enum_def(self, enum_name: str) -> EnummeratorDefinition: ...

    def get_msg_type(self, name: str) -> object: ...

    def get_enum_type_by_name(self, name: str) -> object: ...

    def get_enum_type_by_id(self, id: str) -> object: ...

def get_builtin_database() -> MessageDatabase:
    """Get the JSON database built-in to the package."""

class RecieverStatus:
    """Boolean values indicating information about the state of the reciever."""

    @property
    def raw_value(self) -> int: ...

    @property
    def reciever_error(self) -> bool: ...

    @property
    def temperature_warning(self) -> bool: ...

    @property
    def voltage_warning(self) -> bool: ...

    @property
    def antenna_powered(self) -> bool: ...

    @property
    def lna_failure(self) -> bool: ...

    @property
    def antenna_open_circuit(self) -> bool: ...

    @property
    def antenna_short_circuit(self) -> bool: ...

    @property
    def cpu_overload(self) -> bool: ...

    @property
    def com_buffer_overrun(self) -> bool: ...

    @property
    def spoofing_detected(self) -> bool: ...

    @property
    def link_overrun(self) -> bool: ...

    @property
    def input_overrun(self) -> bool: ...

    @property
    def aux_transmit_overrun(self) -> bool: ...

    @property
    def antenna_gain_out_of_range(self) -> bool: ...

    @property
    def jammer_detected(self) -> bool: ...

    @property
    def ins_reset(self) -> bool: ...

    @property
    def imu_communication_failure(self) -> bool: ...

    @property
    def gps_almanac_invalid(self) -> bool: ...

    @property
    def position_solution_invalid(self) -> bool: ...

    @property
    def position_fixed(self) -> bool: ...

    @property
    def clock_steering_disabled(self) -> bool: ...

    @property
    def clock_model_invalid(self) -> bool: ...

    @property
    def external_oscillator_locked(self) -> bool: ...

    @property
    def software_resource_warning(self) -> bool: ...

    @property
    def tracking_mode_hdr(self) -> bool: ...

    @property
    def digital_filtering_enabled(self) -> bool: ...

    @property
    def auxiliary_3_event(self) -> bool: ...

    @property
    def auxiliary_2_event(self) -> bool: ...

    @property
    def auxiliary_1_event(self) -> bool: ...

    @property
    def version_bits(self) -> int: ...

    def __repr__(self) -> object: ...

class MessageType:
    """
    A message field which provides information about its source, format, and whether it is a response.
    """

    def __repr__(self) -> str: ...

    @property
    def is_response(self) -> bool:
        """Whether the message is a response."""

    @property
    def format(self) -> MESSAGE_FORMAT:
        """The original format of the message."""

    @property
    def sibling_id(self) -> int:
        """Where the message originates from."""

    @property
    def source(self) -> MEASUREMENT_SOURCE:
        """Where the message originates from."""

class Header:
    @property
    def message_id(self) -> int:
        """The Message ID number."""

    @property
    def message_type(self) -> MessageType:
        """Information regarding the type of the message."""

    @property
    def port_address(self) -> int:
        """The port the message was sent from."""

    @property
    def length(self) -> int:
        """The length of the message. Will be 0 if unknown."""

    @property
    def sequence(self) -> int:
        """
        Number of remaning related messages following this one. Will be 0 for most messages.
        """

    @property
    def idle_time(self) -> int:
        """Time that the processor is idle. Divide by two to get the percentage."""

    @property
    def time_status(self) -> TIME_STATUS:
        """The quality of the GPS reference time."""

    @property
    def week(self) -> int:
        """GPS reference wekk number."""

    @property
    def milliseconds(self) -> float:
        """Milliseconds from the beginning of the GPS reference week."""

    @property
    def receiver_status(self) -> RecieverStatus:
        """
        32-bits representing the status of various hardware and software components of the receiver.
        """

    @property
    def message_definition_crc(self) -> int:
        """A value for validating the message definition used for decoding."""

    @property
    def receiver_sw_version(self) -> int:
        """A value (0 - 65535) representing the receiver software build number."""

    def to_dict(self) -> dict:
        """
        Converts the header to a dictionary.

        Returns:
            A dictionary representation of the header.
        """

    def __repr__(self) -> str: ...

class GpsTime:
    """A GPS reference time."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, week: int, milliseconds: float = TIME_STATUS.UNKNOWN) -> None: ...

    @overload
    def __init__(self, week: int, milliseconds: float, time_status: TIME_STATUS = TIME_STATUS.UNKNOWN) -> None: ...

    def __repr__(self) -> str: ...

    @property
    def week(self) -> int:
        """GPS reference week number."""

    @week.setter
    def week(self, arg: int, /) -> None: ...

    @property
    def milliseconds(self) -> float:
        """Milliseconds from the beginning of the GPS reference week."""

    @milliseconds.setter
    def milliseconds(self, arg: float, /) -> None: ...

    @property
    def status(self) -> TIME_STATUS:
        """The quality of the GPS reference time."""

    @status.setter
    def status(self, arg: TIME_STATUS, /) -> None: ...

class UnknownBytes:
    """A set of bytes which was determined to be undecodable by EDIE."""

    def __repr__(self) -> str: ...

    @property
    def data(self) -> bytes:
        """The raw bytes determined to be undecodable."""

class Field:
    def __getattr__(self, field_name: str) -> object: ...

    def __repr__(self) -> str: ...

    def __dir__(self) -> list: ...

    def get_field_names(self) -> list:
        """
        Retrieves the name of every top-level field within the payload of this message.

        Returns:
            The name of every top-level field within the message payload.
        """

    def get_field_values(self) -> list:
        """
        Retrieves the values of every top-level field within the payload of this message.

        Returns:
            The value of every top-level field within the message payload.
        """

    def to_dict(self) -> dict:
        """
        Converts the field to a dictionary.

        Returns:
            A dictionary representation of the field.
        """

    def to_list(self) -> list:
        """
        Converts the field to a list.

        Returns:
            A list representation of the field.
        """

class UnknownMessage:
    def __repr__(self) -> str: ...

    @property
    def header(self) -> Header:
        """The header of the message."""

    @property
    def payload(self) -> bytes:
        """The undecoded bytes that make up the message's payload."""

    def to_dict(self) -> dict:
        """
        Converts the message to a dictionary.

        Returns:
            A dictionary representation of the message.
        """

class Message(Field):
    def encode(self, arg: ENCODE_FORMAT, /) -> MessageData: ...

    def to_ascii(self) -> MessageData: ...

    def to_abbrev_ascii(self) -> MessageData: ...

    def to_binary(self) -> MessageData: ...

    def to_flattened_binary(self) -> MessageData: ...

    def to_json(self) -> MessageData: ...

    def to_dict(self, include_header: bool = True) -> dict:
        """
        Converts the message to a dictionary.

        Args:
            include_header: Whether to include the header of the message in the 
                new representation.

        Returns:
            A dictionary representation of the message.
        """

    @property
    def header(self) -> Header:
        """The header of the message."""

    @property
    def name(self) -> str:
        """The type of message it is."""

class Response:
    def encode(self, arg: ENCODE_FORMAT, /) -> MessageData: ...

    def to_ascii(self) -> MessageData: ...

    def to_abbrev_ascii(self) -> MessageData: ...

    def to_binary(self) -> MessageData: ...

    def to_flattended_binary(self) -> MessageData: ...

    def to_json(self) -> MessageData: ...

    def to_dict(self, include_header: bool = True) -> dict:
        """
        Converts the response to a dictionary.

        Args:
            include_header: Whether to include the header of the response in the 
                new representation.

        Returns:
            A dictionary representation of the response.
        """

    def __repr__(self) -> str: ...

    @property
    def header(self) -> object: ...

    @property
    def name(self) -> str:
        """The type of message it is."""

    @property
    def response_id(self) -> int: ...

    @property
    def response_string(self) -> str: ...

    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from novatel_edie.enums import Responses
    @property
    def response_enum(self) -> Responses

NMEA_SYNC: str = '$'

NMEA_SYNC_LENGTH: int = 1

NMEA_CRC_LENGTH: int = 2

OEM4_ASCII_SYNC: str = '#'

OEM4_ASCII_FIELD_SEPARATOR: str = ','

OEM4_ASCII_HEADER_TERMINATOR: str = ';'

OEM4_ASCII_SYNC_LENGTH: int = 1

OEM4_ASCII_CRC_DELIMITER: str = '*'

OEM4_ASCII_CRC_LENGTH: int = 8

OEM4_SHORT_ASCII_SYNC: str = '%'

OEM4_ASCII_MESSAGE_NAME_MAX: int = 40

OEM4_SHORT_ASCII_SYNC_LENGTH: int = 1

OEM4_ABBREV_ASCII_SYNC: str = '<'

OEM4_ABBREV_ASCII_SEPARATOR: str = ' '

OEM4_ABBREV_ASCII_INDENTATION_LENGTH: int = 5

OEM4_ERROR_PREFIX_LENGTH: int = 6

OEM4_BINARY_SYNC1: int = 170

OEM4_BINARY_SYNC2: int = 68

OEM4_BINARY_SYNC3: int = 18

OEM4_BINARY_SYNC_LENGTH: int = 3

OEM4_BINARY_HEADER_LENGTH: int = 28

OEM4_BINARY_CRC_LENGTH: int = 4

OEM4_SHORT_BINARY_SYNC3: int = 19

OEM4_SHORT_BINARY_SYNC_LENGTH: int = 3

OEM4_SHORT_BINARY_HEADER_LENGTH: int = 12

OEM4_PROPRIETARY_BINARY_SYNC2: int = 69

class ASCII_HEADER(enum.IntEnum):
    """ASCII Message header format sequence"""

    def __str__(self) -> object: ...

    MESSAGE_NAME = 0
    """ASCII log Name."""

    PORT = 1
    """Receiver logging port."""

    SEQUENCE = 2
    """Embedded log sequence number."""

    IDLE_TIME = 3
    """Receiver Idle time."""

    TIME_STATUS = 4
    """GPS reference time status."""

    WEEK = 5
    """GPS Week number."""

    SECONDS = 6
    """GPS week seconds."""

    RECEIVER_STATUS = 7
    """Receiver status."""

    MSG_DEF_CRC = 8
    """Reserved Field."""

    RECEIVER_SW_VERSION = 9
    """Receiver software version."""

class HEADER_FORMAT(enum.IntEnum):
    """Formats for novatel headers."""

    def __str__(self) -> object: ...

    UNKNOWN = 1

    BINARY = 2

    SHORT_BINARY = 3

    PROPRIETARY_BINARY = 4

    ASCII = 5

    SHORT_ASCII = 6

    ABB_ASCII = 7

    NMEA = 8

    JSON = 9

    SHORT_ABB_ASCII = 10

    ALL = 11

class MetaData:
    """
    Metadata for a specific message.

    Used as a storehouse for information during piece-wise decoding.
    """

    def __init__(self) -> None: ...

    @property
    def format(self) -> HEADER_FORMAT: ...

    @format.setter
    def format(self, arg: HEADER_FORMAT, /) -> None: ...

    @property
    def sibling_id(self) -> int: ...

    @sibling_id.setter
    def sibling_id(self, arg: int, /) -> None: ...

    @property
    def measurement_source(self) -> MEASUREMENT_SOURCE: ...

    @measurement_source.setter
    def measurement_source(self, arg: MEASUREMENT_SOURCE, /) -> None: ...

    @property
    def time_status(self) -> TIME_STATUS: ...

    @time_status.setter
    def time_status(self, arg: TIME_STATUS, /) -> None: ...

    @property
    def response(self) -> bool: ...

    @response.setter
    def response(self, arg: bool, /) -> None: ...

    @property
    def week(self) -> int: ...

    @week.setter
    def week(self, arg: int, /) -> None: ...

    @property
    def milliseconds(self) -> float: ...

    @milliseconds.setter
    def milliseconds(self, arg: float, /) -> None: ...

    @property
    def binary_msg_length(self) -> int:
        """
        Message length according to the binary header. If ASCII, this field is not used.
        """

    @binary_msg_length.setter
    def binary_msg_length(self, arg: int, /) -> None: ...

    @property
    def length(self) -> int:
        """Length of the entire log, including the header and CRC."""

    @length.setter
    def length(self, arg: int, /) -> None: ...

    @property
    def header_length(self) -> int:
        """The length of the message header. Used for NovAtel logs."""

    @header_length.setter
    def header_length(self, arg: int, /) -> None: ...

    @property
    def message_id(self) -> int: ...

    @message_id.setter
    def message_id(self, arg: int, /) -> None: ...

    @property
    def message_crc(self) -> int: ...

    @message_crc.setter
    def message_crc(self, arg: int, /) -> None: ...

    @property
    def message_name(self) -> str: ...

    @message_name.setter
    def message_name(self, arg: str, /) -> None: ...

    @property
    def message_description(self) -> object: ...

    @property
    def message_fields(self) -> object: ...

    def __repr__(self) -> str: ...

class Oem4BinaryHeader:
    """Not currently part of public API."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: bytes, /) -> None: ...

    @property
    def sync1(self) -> int:
        """First sync byte of Header."""

    @sync1.setter
    def sync1(self, arg: int, /) -> None: ...

    @property
    def sync2(self) -> int:
        """Second sync byte of Header."""

    @sync2.setter
    def sync2(self, arg: int, /) -> None: ...

    @property
    def sync3(self) -> int:
        """Third sync byte of Header."""

    @sync3.setter
    def sync3(self, arg: int, /) -> None: ...

    @property
    def header_length(self) -> int:
        """Total Binary header length."""

    @header_length.setter
    def header_length(self, arg: int, /) -> None: ...

    @property
    def msg_number(self) -> int:
        """Binary log Message Number/ID."""

    @msg_number.setter
    def msg_number(self, arg: int, /) -> None: ...

    @property
    def msg_type(self) -> int:
        """Binary log Message type response or data?."""

    @msg_type.setter
    def msg_type(self, arg: int, /) -> None: ...

    @property
    def port(self) -> int:
        """Receiver Port of logging."""

    @port.setter
    def port(self, arg: int, /) -> None: ...

    @property
    def length(self) -> int:
        """Total length of binary log."""

    @length.setter
    def length(self, arg: int, /) -> None: ...

    @property
    def sequence_number(self) -> int:
        """Sequence number of Embedded message inside."""

    @sequence_number.setter
    def sequence_number(self, arg: int, /) -> None: ...

    @property
    def idle_time(self) -> int:
        """Receiver Idle time."""

    @idle_time.setter
    def idle_time(self, arg: int, /) -> None: ...

    @property
    def time_status(self) -> int:
        """GPS reference time status."""

    @time_status.setter
    def time_status(self, arg: int, /) -> None: ...

    @property
    def week_no(self) -> int:
        """GPS Week number."""

    @week_no.setter
    def week_no(self, arg: int, /) -> None: ...

    @property
    def week_msec(self) -> int:
        """GPS week seconds."""

    @week_msec.setter
    def week_msec(self, arg: int, /) -> None: ...

    @property
    def status(self) -> int:
        """Status of the log."""

    @status.setter
    def status(self, arg: int, /) -> None: ...

    @property
    def msg_def_crc(self) -> int:
        """Message def CRC of binary log."""

    @msg_def_crc.setter
    def msg_def_crc(self, arg: int, /) -> None: ...

    @property
    def receiver_sw_version(self) -> int:
        """Receiver Software version."""

    @receiver_sw_version.setter
    def receiver_sw_version(self, arg: int, /) -> None: ...

    def __bytes__(self) -> bytes: ...

    def __repr__(self) -> str: ...

class Oem4BinaryShortHeader:
    """Not currently part of public API."""

    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: bytes, /) -> None: ...

    @property
    def sync1(self) -> int:
        """First sync byte of Header."""

    @sync1.setter
    def sync1(self, arg: int, /) -> None: ...

    @property
    def sync2(self) -> int:
        """Second sync byte of Header."""

    @sync2.setter
    def sync2(self, arg: int, /) -> None: ...

    @property
    def sync3(self) -> int:
        """Third sync byte of Header."""

    @sync3.setter
    def sync3(self, arg: int, /) -> None: ...

    @property
    def length(self) -> int:
        """Message body length."""

    @length.setter
    def length(self, arg: int, /) -> None: ...

    @property
    def message_id(self) -> int:
        """Message ID of the log."""

    @message_id.setter
    def message_id(self, arg: int, /) -> None: ...

    @property
    def week_no(self) -> int:
        """GPS Week number."""

    @week_no.setter
    def week_no(self, arg: int, /) -> None: ...

    @property
    def week_msec(self) -> int:
        """GPS Week seconds."""

    @week_msec.setter
    def week_msec(self, arg: int, /) -> None: ...

    def __bytes__(self) -> bytes: ...

    def __repr__(self) -> str: ...

class NovatelEdieException(Exception):
    pass

class FailureException(NovatelEdieException):
    pass

class UnknownException(NovatelEdieException):
    pass

class IncompleteException(NovatelEdieException):
    pass

class IncompleteMoreDataException(NovatelEdieException):
    pass

class NullProvidedException(NovatelEdieException):
    pass

class NoDatabaseException(NovatelEdieException):
    pass

class NoDefinitionException(NovatelEdieException):
    pass

class NoDefinitionEmbeddedException(NovatelEdieException):
    pass

class BufferFullException(NovatelEdieException):
    pass

class BufferEmptyException(NovatelEdieException):
    pass

class StreamEmptyException(NovatelEdieException):
    pass

class UnsupportedException(NovatelEdieException):
    pass

class MalformedInputException(NovatelEdieException):
    pass

class DecompressionFailureException(NovatelEdieException):
    pass

class JsonDbReaderException(NovatelEdieException):
    pass

class STATUS(enum.IntEnum):
    def __str__(self) -> object: ...

    SUCCESS = 0
    """Successfully found a frame in the framer buffer."""

    FAILURE = 1
    """An unexpected failure occurred."""

    UNKNOWN = 2
    """Could not identify bytes as a protocol."""

    INCOMPLETE = 3
    """
    It is possible that a valid frame exists in the frame buffer, but more information is needed.
    """

    INCOMPLETE_MORE_DATA = 4
    """The current frame buffer is incomplete but more data is expected."""

    NULL_PROVIDED = 5
    """A null pointer was provided."""

    NO_DATABASE = 6
    """No database has been provided to the component."""

    NO_DEFINITION = 7
    """No definition could be found in the database for the provided message."""

    NO_DEFINITION_EMBEDDED = 8
    """
    No definition could be found in the database for the embedded message in the RXCONFIG log.
    """

    BUFFER_FULL = 9
    """The destination buffer is not big enough to contain the provided data."""

    BUFFER_EMPTY = 10
    """The internal circular buffer does not contain any unread bytes"""

    STREAM_EMPTY = 11
    """The input stream is empty."""

    UNSUPPORTED = 12
    """An attempted operation is unsupported by this component."""

    MALFORMED_INPUT = 13
    """The input is recognizable, but has unexpected formatting."""

    DECOMPRESSION_FAILURE = 14
    """The RANGECMPx log could not be decompressed."""

def throw_exception_from_status(status: STATUS) -> None: ...

class Parser:
    def __init__(self, message_db: MessageDatabase | None = None) -> None:
        """
        Initializes a Parser.

        Args:
            message_db: The message database to parse messages with.
               If None, use the default database.
        """

    @property
    def ignore_abbreviated_ascii_responses(self) -> bool:
        """
        Whether to skip over abbreviated ascii message responses e.g. `<OK`/`<ERROR`.
        """

    @ignore_abbreviated_ascii_responses.setter
    def ignore_abbreviated_ascii_responses(self, arg: bool, /) -> None: ...

    @property
    def decompress_range_cmp(self) -> bool:
        """Whether to decompress compressed RANGE messages."""

    @decompress_range_cmp.setter
    def decompress_range_cmp(self, arg: bool, /) -> None: ...

    @property
    def return_unknown_bytes(self) -> bool:
        """Whether to return unidentifiable data."""

    @return_unknown_bytes.setter
    def return_unknown_bytes(self, arg: bool, /) -> None: ...

    @property
    def filter(self) -> Filter:
        """The filter which controls which data is skipped over."""

    @filter.setter
    def filter(self, arg: Filter, /) -> None: ...

    @property
    def available_space(self) -> int:
        """
        The number of bytes in the Parser's internal buffer available for writing new data.
        """

    def write(self, arg: bytes, /) -> int:
        """
        Writes data to the Parser's internal buffer allowing it to later be parsed.

        Use 'available_space' attribute to check how many bytes can be safely written.

        Args:
            data: A set of bytes to append to the Parser's internal buffer.

        Returns:
               The number of bytes written to the Parser's internal buffer. 
               Can be less than the length of `data` if the buffer is full.
        """

    def read(self, decode_incomplete_abbreviated: bool = False) -> Message | Response | UnknownMessage | UnknownBytes:
        """
        Attempts to read a message from data in the Parser's buffer.

        Args:
            decode_incomplete_abbreviated: If True, the Parser will try to
            interpret a possibly incomplete abbreviated ASCII message as if
            it were complete. This is necessary when there is no data
            following the message to indicate that its end.

        Returns:
            A decoded `Message`,
            an `UnknownMessage` whose header was identified but whose payload
            could not be decoded due to no available message definition,
            or a series of `UnknownBytes` determined to be undecodable.

        Raises:
            BufferEmptyException: There is insufficient data in the Parser's
            buffer to decode a message.
        """

    def __iter__(self) -> Iterator[Message|Response|UnknownMessage|UnknownBytes]:
        """
        Marks Parser as Iterable.

        Returns:
            The Parser itself as an Iterator.
        """

    def __next__(self) -> Message | Response | UnknownMessage | UnknownBytes:
        """
        Attempts to read the next message from data in the Parser's buffer.

        Returns:
            A decoded `Message`,
            an `UnknownMessage` whose header was identified but whose payload
            could not be decoded due to no available message definition,
            or a series of `UnknownBytes` determined to be undecodable.

        Raises:
            StopIteration: There is insufficient data in the Parser's
            buffer to decode a message.
        """

    def convert(fmt: ENCODE_FORMAT, decode_incomplete_abbreviated: bool = False) -> MessageData:
        """
        Converts the next message in the buffer to the specified format.

        Args:
            fmt: The format to convert the message to.
            decode_incomplete_abbreviated: If True, the Parser will try to
                interpret a possibly incomplete abbreviated ASCII message as if
                it were complete. This is necessary when there is no data
                following the message to indicate its end.

        Returns:
            The converted message.

        Raises:
            BufferEmptyException: There is insufficient data in the Parser's
            buffer to decode a message.
        """

    def iter_convert(self, fmt: ENCODE_FORMAT) -> ConversionIterator:
        """
        Creates an interator which parses and converts messages to a specified format.

        Args:
            fmt: The format to convert messages to.

        Returns:
            An iterator that directly converts messages.
        """

    def flush(self, return_flushed_bytes: bool = False) -> object:
        """
        Flushes all bytes from the internal Parser.

        Args:
            return_flushed_bytes: If True, the flushed bytes will be returned.

        Returns:
            The number of bytes flushed if return_flushed_bytes is False,
            otherwise the flushed bytes.
        """

class ConversionIterator:
    def __iter__(self) -> Iterator[MessageData]:
        """
        Marks ConversionIterator as Iterable.

        Returns:
            The ConversionIterator itself as an Iterator.
        """

    def __next__() -> MessageData:
        """
        Converts the next message in the buffer to the specified format.

        Returns:
            The converted message.

        Raises:
            StopIteration: There is insufficient data in the Parser's
            buffer to decode a message.
        """

class FileParser:
    def __init__(self, file_path: str | os.PathLike, message_db: MessageDatabase | None = None) -> None:
        """
        Initializes a FileParser.

        Args:
            file_path: The path to the file to be parsed.
            message_db: The message database to parse message with.
               If None, use the default database.
        """

    @property
    def ignore_abbreviated_ascii_responses(self) -> bool:
        """
        Whether to skip over abbreviated ASCII message responses e.g. `<OK`/`<ERROR`.
        """

    @ignore_abbreviated_ascii_responses.setter
    def ignore_abbreviated_ascii_responses(self, arg: bool, /) -> None: ...

    @property
    def decompress_range_cmp(self) -> bool:
        """Whether to decompress compressed RANGE messages."""

    @decompress_range_cmp.setter
    def decompress_range_cmp(self, arg: bool, /) -> None: ...

    @property
    def return_unknown_bytes(self) -> bool:
        """Whether to return unidentifiable data."""

    @return_unknown_bytes.setter
    def return_unknown_bytes(self, arg: bool, /) -> None: ...

    @property
    def filter(self) -> Filter:
        """The filter which controls which data is skipped over."""

    @filter.setter
    def filter(self, arg: Filter, /) -> None: ...

    def read(self) ->  Message | Response | UnknownMessage | UnknownBytes:
        """
        Attempts to read a message from remaining data in the file.

        Returns:
            A decoded `Message`,
            an `UnknownMessage` whose header was identified but whose payload
            could not be decoded due to no available message definition,
            or a series of `UnknownBytes` determined to be undecodable.

        Raises:
            StreamEmptyException: There is insufficient data in the remaining 
                in the file to decode a message.
        """

    def __iter__(self) -> Iterator[Message|Response|UnknownMessage|UnknownBytes]:
        """
        Marks FileParser as Iterable.

        Returns:
            The FileParser itself as an Iterator.
        """

    def __next__(self) -> Message | Response | UnknownMessage | UnknownBytes:
        """
        Attempts to read the next message from remaining data in the file.

        Returns:
            A decoded `Message`,
            an `UnknownMessage` whose header was identified but whose payload
            could not be decoded due to no available message definition,
            or a series of `UnknownBytes` determined to be undecodable.

        Raises:
            StopIteration: There is insufficient data in the remaining
                file to decode a message.
        """

    def convert(self, fmt: ENCODE_FORMAT) -> object:
        """
        Converts the next message in the file to the specified format.

        Args:
            fmt: The format to convert the message to.

        Returns:
            The converted message.

        Raises:
            StreamEmptyException: There is insufficient data in the remaining 
                in the file to decode a message.
        """

    def iter_convert(self, fmt: ENCODE_FORMAT) -> FileConversionIterator:
        """
        Creates an iterator which parses and converts messages to a specified format.

        Args:
            fmt: The format to convert messages to.

        Returns:
            An iterator that directly converts messages.
        """

    def reset(self) -> bool:
        """Resets the FileParser, clearing its internal state."""

    def flush(self, return_flushed_bytes: bool = False) -> object:
        """
        Flushes all bytes from the FileParser.

        Args:
            return_flushed_bytes: If True, the flushed bytes will be returned.

        Returns:
            The number of bytes flushed if return_flushed_bytes is False,
            otherwise the flushed bytes.
        """

class FileConversionIterator:
    def __iter__(self) -> Iterator[MessageData]:
        """
        Marks FileConversionIterator as Iterable.

        Returns:
            The FileConversionIterator itself as an Iterator.
        """

    def __next__() -> MessageData:
        """
        Converts the next message in the file to the specified format.

        Returns:
            The converted message.

        Raises:
            StopIteration: There is insufficient data in the remaining
                file to decode a message.
        """

class Framer:
    def __init__(self) -> None:
        """Initializes a Framer."""

    @property
    def frame_json(self) -> bool:
        """Whether to detect, frame, and return messages in JSON format."""

    @frame_json.setter
    def frame_json(self, arg: bool, /) -> None: ...

    @property
    def payload_only(self) -> bool:
        """Whether to frame and return only the payload of detected messages."""

    @payload_only.setter
    def payload_only(self, arg: bool, /) -> None: ...

    @property
    def report_unknown_bytes(self) -> bool:
        """Whether to frame and return undecodable data."""

    @report_unknown_bytes.setter
    def report_unknown_bytes(self, arg: bool, /) -> None: ...

    @property
    def available_space(self) -> int:
        """
        The number of bytes in the Framer's internal buffer available for writing new data.
        """

    def get_frame(buffer_size = MAX_MESSAGE_LENGTH) -> tuple[bytes, MetaData]:
        """
        Attempts to get a frame from the Framer's buffer.

        Args:
            buffer_size: The maximum number of bytes to use for a framed message.

        Returns:
            The framed data and metadata.

        Raises:
            BufferEmptyException: There are no more bytes in the internal buffer.
            BufferFullException: The framed message does not fit in the provided
                buffer size.
            IncompleteException: The framer found the start of a message, but 
                there are no more bytes in the internal buffer.
        """

    def __iter__(self) -> Iterator[tuple[bytes, MetaData]]:
        """
        Marks Framer as Iterable.

        Returns:
            The Framer itself as an Iterator.
        """

    def __next__(self) -> tuple[bytes, MetaData]:
        """
        Attempts to get the next frame from the Framer's buffer.

        Returns:
            The framed data and its metadata.

        Raises:
            StopIteration: There is insufficient data in the Framer's
                buffer to get a complete frame.
        """

    def write(self, arg: bytes, /) -> int:
        """
        Writes data to the Framer's buffer.

        Use 'available_space' attribute to check how many bytes can be safely written.  

        Args:
            data: The data to write to the buffer.

        Returns:
            The number of bytes written to the Framer's buffer. 
            Can be less than the length of `data` if the buffer is full.
        """

    def flush(self) -> bytes:
        """
        Flushes all bytes from the internal Framer.

        Returns:
            The flushed bytes.
        """

class MessageData:
    def __repr__(self) -> str: ...

    @property
    def message(self) -> bytes: ...

    @property
    def header(self) -> object: ...

    @property
    def payload(self) -> object: ...

class Decoder:
    def __init__(self, message_db: MessageDatabase | None = None) -> None:
        """
        Initializes a Decoder.

        Args:
            message_db: The message database to decode messages with.
               If None, use the default database.
        """

    def decode_header(self, raw_header: bytes, metadata: MetaData | None = None) -> Header:
        """
        Decode the header from a piece of framed data.

        Args:
            raw_header: A frame of raw bytes containing the header information to decode.
            metadata: A storehouse for additional information determined as part of the decoding process.
                Supplying metadata is optional, but without it there will be no way of later accessing
                information such as the number of bytes that make up the original header representation.

        Returns:
            A decoded `Header`.
        """

    def decode_payload(self, raw_payload: bytes, header: Header, metadata: MetaData | None = None) -> Message:
        """
        Decode the payload of a message given the associated header.

        Args:
            raw_header: A frame of raw bytes containing the payload information to decode.
            metadata: An optional way of supplying data to aid in decoding. If not provided
                decoding will attempt to use only information from the header.

        Returns:
            A decoded `Message`.
        """

    def decode(self, raw_message: bytes) -> Message:
        """
        Decode the message from its raw byte representation.

        Args:
            raw_message: A frame of raw bytes containing the message information to decode.

        Returns:
            A decoded `Message` or an `UnknownMessage` whose header was identified but whose payload
            could not be decoded due to no available message definition.
        """

class Filter:
    def __init__(self) -> None:
        """
        Initializes a filter with the default configuration which all messages.
        """

    @property
    def include_responses(self) -> bool:
        """Whether to include response messages."""

    @include_responses.setter
    def include_responses(self, include: bool): ...

    @property
    def include_non_responses(self) -> bool:
        """Whether to include non-response (regular) messages."""

    @include_non_responses.setter
    def include_non_responses(self, include: bool): ...

    @property
    def lower_time_bound(self) -> GpsTime | None:
        """The earliest time that messages can have without being filtered-out."""

    @lower_time_bound.setter
    def lower_time_bound(self, value: GpsTime | None): ...

    @property
    def upper_time_bound(self) -> GpsTime | None:
        """The latest time that messages can have without being filtered-out."""

    @lower_time_bound.setter
    def upper_time_bound(self, value: GpsTime | None): ...

    @property
    def time_bounds_inverted(self) -> bool:
        """
        Whether the upper and lower time bounds should be inverted. 

        If both are set, only messages outside of the range will be included.
        """

    @time_bounds_inverted.setter
    def time_bounds_inverted(self, value: bool) -> None: ...

    @property
    def decimation_period(self) -> int | None:
        """
        Only messages whose time in milliseconds is cleanly divisible by this number will be included.
        """

    @decimation_period.setter
    def decimation_period(self, value: int | None): ...

    @property
    def decimation_period_inverted(self) -> bool:
        """
        Whether to invert which messages are filtered by the decimation period.
        """

    @decimation_period_inverted.setter
    def decimation_period_inverted(self, arg: bool, /) -> None: ...

    @property
    def time_statuses(self) -> list[TIME_STATUS]:
        """
        The set of time statues to filter on. 

        If None, messages with any time status will be included.
        """

    @property
    def time_statuses_excluded(self) -> bool:
        """
        Whether to exclude messages from the set of filtered time_statues. 

        Otherwise only they will be included.
        """

    @time_statuses_excluded.setter
    def time_statuses_excluded(self, value: bool) -> None: ...

    def add_time_status(self, time_status: TIME_STATUS) -> None:
        """
        Adds a new time status to the set to filter on.

        Args:
            time_status: The additional time status to filter on.
        """

    def extend_time_statuses(self, time_statuses: Sequence[TIME_STATUS]) -> None:
        """
        Extends the set of time statuses to filter on.

        Args:
            time_statuses: The additional times status to filter on.
        """

    def remove_time_status(self, time_status: TIME_STATUS) -> None:
        """
        Removes a time status from the set to filter on.

        Args:
            time_statuses: The time status to remove.
        """

    def clear_time_statuses(self) -> None:
        """Clears all time status filters."""

    @property
    def message_ids(self) -> list[tuple[int, HEADER_FORMAT, int]]:
        """The set of message IDs to filter on."""

    @property
    def message_ids_excluded(self) -> bool:
        """
        Whether to exclude messages from the set of filtered ids. 

        Otherwise only they will be included.
        """

    @message_ids_excluded.setter
    def message_ids_excluded(self, value: bool) -> None: ...

    def add_message_id(self, id: int, format: HEADER_FORMAT = HEADER_FORMAT.ALL, source: int = 0) -> None:
        """
        Adds a new message ID to the set to filter on.

        Args:
            id: The message ID to filter on.
            format: The message format it applies to. Defaults to all.
            source: The antenna source it applies to. Defaults to primary.
        """

    def extend_message_ids(self, ids: Sequence[tuple[int, HEADER_FORMAT, int]]) -> None:
        """
        Extends the set of message ids to filter on.

        Args:
            time_statuses: A sequence of ids, formats, and sources.
        """

    def remove_message_id(self, id: int, format: HEADER_FORMAT, source: int) -> None:
        """
        Removes a message ID from the set to filter on.

        Args:
            id: The message ID to remove.
            format: Which format to remove it for.
            source: Which source to remove if for.
        """

    def clear_message_ids(self) -> None:
        """Clears all message ID filters."""

    @property
    def message_names(self) -> list[tuple[str, HEADER_FORMAT, int]]:
        """The set of message names to filter on."""

    @property
    def message_names_excluded(self) -> bool:
        """
        Whether to exclude messages from the set of filtered names. 

        Otherwise only they will be included.
        """

    @message_names_excluded.setter
    def message_names_excluded(self, value: bool) -> None: ...

    def add_message_name(self, name: str, format: HEADER_FORMAT = HEADER_FORMAT.ALL, source: int = 0) -> None:
        """
        Adds a new message name to the set to filter on.

        Args:
            id: The message name to filter on.
            format: The message format it applies to. Defaults to all.
            source: The antenna source it applies to. Defaults to primary.
        """

    def extend_message_names(self, names: Sequence[tuple[str, HEADER_FORMAT, int]]) -> None:
        """
        Extends the set of message name to filter on.

        Args:
            time_statuses: A sequence of names, formats, and sources.
        """

    def remove_message_name(self, name: str, format: HEADER_FORMAT, source: int) -> None:
        """
        Removes a message name from the set to filter on.

        Args:
            id: The message name to remove.
            format: Which format to remove it for.
            source: Which source to remove if for.
        """

    def clear_message_names(self) -> None:
        """Clears all message name filters."""

    def reset(self) -> None:
        """
        Reset the filter to the default configuration of allowing all messages.
        """

    def do_filtering(self, metadata: MetaData) -> bool:
        """
        Determines whether a message should be filtered.

        Args:
            metadata: The metadata associated with a particular message.

        Returns:
            True if the message can be included, False if it should be filtered-out.
        """

    def __repr__(self) -> str:
        """
        Creates a string representation based on active filters.

        Returns: The string representation of the filter.
        """

class Commander:
    def __init__(self, message_db: MessageDatabase | None = None) -> None: ...

    def encode(self, abbrev_ascii_command: bytes, encode_format: ENCODE_FORMAT) -> bytes: ...

class RangeDecompressor:
    def __init__(self, message_db: MessageDatabase | None = None) -> None: ...

    def reset(self) -> None: ...

    def decompress(self, data: bytes, metadata: MetaData, encode_format: ENCODE_FORMAT = ENCODE_FORMAT.UNSPECIFIED) -> object: ...

class RxConfigHandler:
    def __init__(self, message_db: MessageDatabase | None = None) -> None: ...

    def write(self, arg: bytes, /) -> int: ...

    def convert(self, encode_format: ENCODE_FORMAT) -> tuple: ...

    def flush(self, return_flushed_bytes: bool = False) -> object: ...

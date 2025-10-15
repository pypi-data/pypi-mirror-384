from azuresphere_imagemetadata.guid_utils import Guid
import pytest


def test_guid_raises():
    with pytest.raises(ValueError):
        Guid.from_hex_string("00000000-0000-0000")


def test_guid_from_raw_bytes():
    INPUT_HEX = "00000000000000000000000000000000"
    guid = Guid(bytearray.fromhex(INPUT_HEX))
    assert guid.hex == INPUT_HEX


def test_guid_from_hex_string():
    """
    Confirms the input string matches the output string

    This is because the hex string bytes are remapped when stored as raw bytes.
    """
    INPUT_HEX = "01234567-1234-5678-1234-123456789012"
    guid = Guid.from_hex_string(INPUT_HEX)
    assert str(guid) == "01234567-1234-5678-1234-123456789012"


def test_guid_to_hex_string():
    """
    Confirms that the raw bytes do not match the hex string (expected behaviour).

    This is because the raw bytes are stored in a different order to the hex string.
    """
    INPUT_HEX = "01234567123456781234123456789012"
    guid = Guid(bytearray.fromhex(INPUT_HEX))
    assert guid.hex != INPUT_HEX

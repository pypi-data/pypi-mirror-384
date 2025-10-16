from unittest.mock import patch

from sf_devtools.core.common import check_prerequisites


@patch("sf_devtools.core.common.which")
def test_check_prerequisites_missing(mock_which):
    def fake_which(cmd):
        return None if cmd == "sf" else "/usr/bin/" + cmd

    mock_which.side_effect = fake_which
    assert check_prerequisites() is False


@patch("sf_devtools.core.common.which", return_value="/usr/bin/mock")
def test_check_prerequisites_ok(mock_which):
    assert check_prerequisites() is True

import json
from unittest.mock import Mock, patch

from sf_devtools.core.salesforce import SalesforceCli


@patch("sf_devtools.core.salesforce.subprocess.run")
def test_get_package_versions(mock_run):
    mock_result = Mock()
    mock_result.stdout = json.dumps(
        {
            "result": [
                {
                    "SubscriberPackageVersionId": "04t000000000001",
                    "Version": "1.0.0",
                    "CreatedDate": "2024-01-01",
                }
            ]
        }
    )
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    sf_cli = SalesforceCli()
    versions = sf_cli.get_package_versions("mypkg")
    assert versions == ["04t000000000001 - 1.0.0 (2024-01-01)"]

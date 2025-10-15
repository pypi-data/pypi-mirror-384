"""
Test for Salesforce CLI wrapper
"""

import json
from unittest.mock import Mock, patch

import pytest

from sf_devtools.core.salesforce import SalesforceCli, SalesforceCliError


def test_salesforce_cli_initialization():
    """SalesforceCliクラスの初期化テスト"""
    sf_cli = SalesforceCli()
    assert sf_cli is not None
    assert sf_cli.console is not None


@patch("subprocess.run")
def test_run_command_success(mock_run):
    """正常なコマンド実行のテスト"""
    # モックの設定
    mock_result = Mock()
    mock_result.stdout = '{"result": {"status": "success"}}'
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    sf_cli = SalesforceCli()
    result = sf_cli.run_command(["sf", "org", "list"])

    assert result == {"result": {"status": "success"}}
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_run_command_json_error(mock_run):
    """JSON解析エラーのテスト"""
    # モックの設定
    mock_result = Mock()
    mock_result.stdout = "invalid json"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    sf_cli = SalesforceCli()

    with pytest.raises(SalesforceCliError):
        sf_cli.run_command(["sf", "org", "list"])


@patch("subprocess.run")
def test_list_orgs(mock_run):
    """組織一覧取得のテスト"""
    # モックの設定
    mock_result = Mock()
    mock_result.stdout = json.dumps(
        {
            "result": {
                "nonScratchOrgs": [
                    {
                        "alias": "prod",
                        "username": "user@example.com",
                        "orgId": "00D000000000000EAA",
                        "connected": True,
                    }
                ],
                "scratchOrgs": [],
            }
        }
    )
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    sf_cli = SalesforceCli()
    result = sf_cli.list_orgs()

    assert "result" in result
    assert "nonScratchOrgs" in result["result"]
    assert len(result["result"]["nonScratchOrgs"]) == 1

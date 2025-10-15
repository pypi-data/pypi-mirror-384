"""
Salesforce CLI wrapper utilities
"""

import json
import subprocess
from typing import Any, Dict, List

from rich.table import Table

from .common import console


class SalesforceCliError(Exception):
    """Salesforce CLI コマンド実行エラー"""

    pass


class SalesforceCli:
    """Salesforce CLI のラッパークラス"""

    def __init__(self) -> None:
        self.console = console

    def run_command(
        self, command: List[str], capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Salesforce CLI コマンドを実行する

        Args:
            command: 実行するコマンドのリスト
            capture_output: 出力をキャプチャするかどうか

        Returns:
            コマンドの実行結果（JSON形式）

        Raises:
            SalesforceCliError: コマンドの実行に失敗した場合
        """
        try:
            # --json フラグを追加して JSON 出力を強制
            if "--json" not in command:
                command.append("--json")

            self.console.print(f"[dim]実行中: {' '.join(command)}[/dim]")

            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                check=False,  # エラーコードでの例外発生を無効化
            )

            if result.stdout:
                try:
                    parsed_result = json.loads(result.stdout)
                    # Type guard to ensure we return the expected type
                    if isinstance(parsed_result, dict):
                        return parsed_result
                    else:
                        return {"result": parsed_result}
                except json.JSONDecodeError as e:
                    raise SalesforceCliError(
                        f"JSON解析エラー: {e}\n出力: {result.stdout}"
                    )

            # stdout が空の場合、stderr をチェック
            if result.stderr:
                raise SalesforceCliError(f"コマンド実行エラー: {result.stderr}")

            return {"result": None, "status": 0}

        except FileNotFoundError:
            raise SalesforceCliError(
                "Salesforce CLI (sf) が見つかりません。インストールしてください。"
            )
        except Exception as e:
            raise SalesforceCliError(f"予期しないエラー: {e}")

    def list_orgs(self, include_scratch: bool = True) -> Dict[str, Any]:
        """
        組織一覧を取得する

        Args:
            include_scratch: スクラッチ組織を含めるかどうか

        Returns:
            組織一覧の情報
        """
        command = ["sf", "org", "list"]
        if include_scratch:
            command.append("--all")

        return self.run_command(command)

    def get_package_versions(self, package_name: str) -> List[str]:
        """指定したパッケージのバージョン一覧を取得する"""
        command = ["sf", "package", "version", "list", "--packages", package_name]
        result = self.run_command(command)
        versions = []
        for item in result.get("result", []):
            spv_id = item.get("SubscriberPackageVersionId", "")
            ver = item.get("Version", "")
            created = item.get("CreatedDate", "")
            versions.append(f"{spv_id} - {ver} ({created})")
        return versions

    def display_orgs_table(self, orgs_data: Dict[str, Any]) -> None:
        """
        組織一覧を美しいテーブル形式で表示する

        Args:
            orgs_data: sf org list の結果データ
        """
        # データ構造の確認（新旧両対応）
        result = orgs_data.get("result", orgs_data)

        # Non-Scratch組織
        non_scratch = result.get("nonScratchOrgs", [])
        if non_scratch:
            table = Table(
                title="🏢 認証済み組織", show_header=True, header_style="bold blue"
            )
            table.add_column("エイリアス", style="cyan", no_wrap=True)
            table.add_column("ユーザー名", style="green")
            table.add_column("組織ID", style="yellow")
            table.add_column("接続状態", style="magenta")

            for org in non_scratch:
                alias = org.get("alias", "")
                username = org.get("username", "")
                org_id = org.get("orgId", "")
                connected = (
                    "✅ 接続済み" if org.get("connected", False) else "❌ 未接続"
                )

                table.add_row(alias, username, org_id, connected)

            self.console.print(table)
            self.console.print()

        # Scratch組織
        scratch_orgs = result.get("scratchOrgs", [])
        if scratch_orgs:
            table = Table(
                title="🧪 スクラッチ組織", show_header=True, header_style="bold green"
            )
            table.add_column("エイリアス", style="cyan", no_wrap=True)
            table.add_column("ユーザー名", style="green")
            table.add_column("組織ID", style="yellow")
            table.add_column("有効期限", style="red")
            table.add_column("接続状態", style="magenta")

            for org in scratch_orgs:
                alias = org.get("alias", "")
                username = org.get("username", "")
                org_id = org.get("orgId", "")
                expiration_date = org.get("expirationDate", "未設定")
                connected = (
                    "✅ 接続済み" if org.get("connected", False) else "❌ 未接続"
                )

                table.add_row(alias, username, org_id, expiration_date, connected)

            self.console.print(table)

        # 組織が見つからない場合
        if not non_scratch and not scratch_orgs:
            self.console.print("[yellow]認証済みの組織が見つかりません。[/yellow]")
            self.console.print(
                "[dim]sf org login web を使用して組織に認証してください。[/dim]"
            )

"""
Scratch organization management functionality.
Port of scripts/mes-dev-cli/modules/scratch_org.sh
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..core.common import (
    Config,
    Logger,
    SalesforceCli,
    SalesforceCliError,
    UserInterface,
    config,
    logger,
    sf_cli,
    ui,
)


class ScratchOrgManager:
    """Scratch organization management functionality."""

    def show_menu(self) -> None:
        """Show scratch org management menu."""
        while True:
            logger.info("スクラッチ組織管理")

            options = [
                "新規作成",
                "一覧表示",
                "削除",
                "組織を開く",
                "組織情報表示",
                "一括削除",
                "組織シェイプ管理",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("操作を選択してください:", options)

                if choice == 0:  # 新規作成
                    self.create_scratch_org()
                elif choice == 1:  # 一覧表示
                    self.list_scratch_orgs()
                elif choice == 2:  # 削除
                    self.delete_scratch_org()
                elif choice == 3:  # 組織を開く
                    self.open_scratch_org()
                elif choice == 4:  # 組織情報表示
                    self.show_scratch_org_info()
                elif choice == 5:  # 一括削除
                    self.bulk_delete_scratch_orgs()
                elif choice == 6:  # 組織シェイプ管理
                    self.org_shape_menu()
                elif choice == 7:  # 戻る
                    return

                # 操作完了後、続行確認
                if not ui.confirm("スクラッチ組織管理を続けますか？", default=True):
                    return

            except Exception as e:
                logger.error(f"操作中にエラーが発生しました: {e}")
                if not ui.confirm("スクラッチ組織管理を続けますか？", default=True):
                    return

    def create_scratch_org(self) -> None:
        """Create a new scratch organization."""
        logger.step("新規スクラッチ組織の作成")

        # 作成タイプの選択
        creation_types = [
            "標準 (sanwa-scratch-def.json)",
            "クイック作成 (最小設定)",
            "シェイプベース作成",
        ]

        choice = ui.select_from_menu("作成するスクラッチ組織のタイプ:", creation_types)

        if choice == 0:
            self._create_standard_scratch_org()
        elif choice == 1:
            self._create_quick_scratch_org()
        elif choice == 2:
            self._create_shape_based_scratch_org()

    def list_scratch_orgs(self) -> None:
        """List scratch organizations."""
        logger.step("スクラッチ組織一覧を表示中...")

        try:
            result = sf_cli.run_command(
                ["sf", "org", "list", "--json"], cwd=config.project_root
            )

            # Parse JSON output
            try:
                org_data = json.loads(result.stdout)
                scratch_orgs = org_data.get("result", {}).get(
                    "scratchOrgs", org_data.get("scratchOrgs", [])
                )

                if not scratch_orgs:
                    logger.info("スクラッチ組織が見つかりません")
                    return

                print()
                print("=== スクラッチ組織一覧 ===")
                print(f"{'Alias':<20} {'Username':<40} {'Expiration':<12} {'Status'}")
                print("-" * 80)

                for org in scratch_orgs:
                    alias = org.get("alias", "")
                    username = org.get("username", "")
                    expiration = org.get("expirationDate", "")
                    status = "Active" if org.get("isExpired") is False else "Expired"

                    print(f"{alias:<20} {username:<40} {expiration:<12} {status}")

            except json.JSONDecodeError:
                logger.error("組織リストの解析に失敗しました")

        except SalesforceCliError:
            logger.error("スクラッチ組織の一覧取得に失敗しました")

    def delete_scratch_org(self) -> None:
        """Delete a scratch organization."""
        logger.step("スクラッチ組織の削除")

        scratch_org = ui.select_org(
            "削除するスクラッチ組織", include_scratch=True, return_type="alias"
        )
        if not scratch_org:
            logger.error("組織が選択されませんでした")
            return

        # 確認
        logger.warn(f"スクラッチ組織 '{scratch_org}' を削除します")
        if not ui.confirm("この操作は取り消せません。続行しますか？"):
            logger.info("削除をキャンセルしました")
            return

        try:
            logger.step(f"スクラッチ組織 '{scratch_org}' を削除中...")

            command = [
                "sf",
                "org",
                "delete",
                "scratch",
                "--target-org",
                scratch_org,
                "--no-prompt",
            ]
            sf_cli.run_command(command, cwd=config.project_root)

            logger.success(f"スクラッチ組織 '{scratch_org}' を削除しました")

        except SalesforceCliError:
            logger.error(f"スクラッチ組織 '{scratch_org}' の削除に失敗しました")

    def open_scratch_org(self) -> None:
        """Open a scratch organization in browser."""
        logger.step("スクラッチ組織を開く")

        scratch_org = ui.select_org(
            "開くスクラッチ組織", include_scratch=True, return_type="alias"
        )
        if not scratch_org:
            logger.error("組織が選択されませんでした")
            return

        try:
            logger.step(f"スクラッチ組織 '{scratch_org}' を開いています...")

            command = ["sf", "org", "open", "--target-org", scratch_org]
            sf_cli.run_command(command, cwd=config.project_root)

            logger.success(f"スクラッチ組織 '{scratch_org}' をブラウザで開きました")

        except SalesforceCliError:
            logger.error(f"スクラッチ組織 '{scratch_org}' のオープンに失敗しました")

    def show_scratch_org_info(self) -> None:
        """Show detailed scratch organization information."""
        logger.step("スクラッチ組織情報の表示")

        scratch_org = ui.select_org(
            "情報を表示するスクラッチ組織", include_scratch=True, return_type="alias"
        )
        if not scratch_org:
            logger.error("組織が選択されませんでした")
            return

        try:
            logger.step(f"スクラッチ組織 '{scratch_org}' の情報を取得中...")

            # Get detailed org info
            command = ["sf", "org", "display", "--target-org", scratch_org, "--json"]
            result = sf_cli.run_command(command, cwd=config.project_root)

            try:
                org_info = json.loads(result.stdout)
                result_data = org_info.get("result", {})

                print()
                print(f"=== スクラッチ組織情報: {scratch_org} ===")
                print(f"Username: {result_data.get('username', 'N/A')}")
                print(f"Org ID: {result_data.get('id', 'N/A')}")
                print(f"Instance URL: {result_data.get('instanceUrl', 'N/A')}")
                print(
                    f"Access Token: {'***' if result_data.get('accessToken') else 'N/A'}"
                )
                print(f"Client ID: {result_data.get('clientId', 'N/A')}")
                print(f"Created Date: {result_data.get('createdDate', 'N/A')}")
                print(f"Expiration Date: {result_data.get('expirationDate', 'N/A')}")
                print(f"Edition: {result_data.get('edition', 'N/A')}")
                print(f"Status: {result_data.get('status', 'N/A')}")

            except json.JSONDecodeError:
                logger.error("組織情報の解析に失敗しました")
                print(result.stdout)

        except SalesforceCliError:
            logger.error(f"スクラッチ組織 '{scratch_org}' の情報取得に失敗しました")

    def bulk_delete_scratch_orgs(self) -> None:
        """Delete multiple scratch organizations."""
        logger.step("スクラッチ組織の一括削除")

        try:
            # Get scratch orgs list
            result = sf_cli.run_command(
                ["sf", "org", "list", "--json"], cwd=config.project_root
            )
            org_data = json.loads(result.stdout)
            scratch_orgs = org_data.get("result", {}).get(
                "scratchOrgs", org_data.get("scratchOrgs", [])
            )

            if not scratch_orgs:
                logger.info("削除可能なスクラッチ組織がありません")
                return

            # Show deletion options
            deletion_options = [
                "有効期限切れの組織のみ削除",
                "すべてのスクラッチ組織を削除",
                "手動選択",
            ]

            choice = ui.select_from_menu(
                "削除タイプを選択してください:", deletion_options
            )

            orgs_to_delete = []

            if choice == 0:  # 有効期限切れのみ
                for org in scratch_orgs:
                    if org.get("isExpired", False):
                        orgs_to_delete.append(org.get("alias") or org.get("username"))
            elif choice == 1:  # すべて
                for org in scratch_orgs:
                    orgs_to_delete.append(org.get("alias") or org.get("username"))
            elif choice == 2:  # 手動選択
                # TODO: Implement multi-select functionality
                logger.info("手動選択機能は今後実装予定です")
                return

            if not orgs_to_delete:
                logger.info("削除対象のスクラッチ組織がありません")
                return

            # 確認
            logger.warn(f"{len(orgs_to_delete)} 個のスクラッチ組織を削除します:")
            for org in orgs_to_delete:
                print(f"  - {org}")

            if not ui.confirm("この操作は取り消せません。続行しますか？"):
                logger.info("一括削除をキャンセルしました")
                return

            # Delete organizations
            success_count = 0
            for org in orgs_to_delete:
                try:
                    logger.step(f"スクラッチ組織 '{org}' を削除中...")
                    command = [
                        "sf",
                        "org",
                        "delete",
                        "scratch",
                        "--target-org",
                        org,
                        "--no-prompt",
                    ]
                    sf_cli.run_command(command, cwd=config.project_root)
                    success_count += 1
                except SalesforceCliError:
                    logger.error(f"スクラッチ組織 '{org}' の削除に失敗しました")

            logger.success(
                f"{success_count}/{len(orgs_to_delete)} 個のスクラッチ組織を削除しました"
            )

        except Exception as e:
            logger.error(f"一括削除中にエラーが発生しました: {e}")

    def org_shape_menu(self) -> None:
        """Organization shape management menu."""
        logger.info("組織シェイプ管理")
        logger.info("組織シェイプ機能は今後実装予定です")

    def _create_standard_scratch_org(self) -> None:
        """Create standard scratch org using sanwa-scratch-def.json."""
        logger.step("標準スクラッチ組織の作成")

        # DevHub認証確認
        devhub = self._get_devhub_org()
        if not devhub:
            return

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        alias = ui.get_user_input("エイリアス", f"scratch-{timestamp}")
        duration = ui.get_user_input(
            "有効期間 (日)", str(config.default_scratch_duration)
        )

        # 設定ファイルの確認
        config_file = config.config_dir / "sanwa-scratch-def.json"
        if not config_file.exists():
            logger.error(f"設定ファイルが見つかりません: {config_file}")
            return

        # 作成前の確認
        logger.info("作成設定:")
        print(f"  エイリアス: {alias}")
        print(f"  有効期間: {duration} 日")
        print(f"  設定ファイル: {config_file}")
        print(f"  DevHub: {devhub}")

        if not ui.confirm("この設定でスクラッチ組織を作成しますか？"):
            logger.info("作成をキャンセルしました")
            return

        try:
            logger.step("スクラッチ組織を作成中... (最大40分)")

            command = [
                "sf",
                "org",
                "create",
                "scratch",
                "--definition-file",
                str(config_file),
                "--alias",
                alias,
                "--duration-days",
                duration,
                "--target-dev-hub",
                devhub,
                "--wait",
                "40",
            ]

            sf_cli.run_command(command, cwd=config.project_root)
            logger.success(f"スクラッチ組織 '{alias}' が作成されました")

            # Show details
            self._show_scratch_org_details(alias)

        except SalesforceCliError:
            logger.error("スクラッチ組織の作成に失敗しました")

    def _create_quick_scratch_org(self) -> None:
        """Create quick scratch org with minimal configuration."""
        logger.step("クイックスクラッチ組織の作成")

        # DevHub認証確認
        devhub = self._get_devhub_org()
        if not devhub:
            return

        timestamp = datetime.now().strftime("%H%M%S")
        alias = ui.get_user_input("エイリアス", f"quick-{timestamp}")

        # 作成前の確認
        logger.info("作成設定:")
        print(f"  エイリアス: {alias}")
        print("  設定: 最小設定 (Developer Edition)")
        print("  有効期間: 7 日")
        print(f"  DevHub: {devhub}")

        if not ui.confirm("この設定でスクラッチ組織を作成しますか？"):
            logger.info("作成をキャンセルしました")
            return

        try:
            logger.step("クイックスクラッチ組織を作成中...")

            # Create minimal scratch org definition
            quick_config = {
                "orgName": "Quick Scratch Org",
                "edition": "Developer",
                "features": [],
                "settings": {},
            }

            # Write temporary config file
            temp_config = config.temp_dir / "quick-scratch-def.json"
            config.temp_dir.mkdir(exist_ok=True)

            with open(temp_config, "w", encoding="utf-8") as f:
                json.dump(quick_config, f, indent=2)

            command = [
                "sf",
                "org",
                "create",
                "scratch",
                "--definition-file",
                str(temp_config),
                "--alias",
                alias,
                "--duration-days",
                "7",
                "--target-dev-hub",
                devhub,
            ]

            sf_cli.run_command(command, cwd=config.project_root)
            logger.success(f"クイックスクラッチ組織 '{alias}' が作成されました")

            # Cleanup temp file
            temp_config.unlink(missing_ok=True)

            # Show details
            self._show_scratch_org_details(alias)

        except SalesforceCliError:
            logger.error("クイックスクラッチ組織の作成に失敗しました")

    def _create_shape_based_scratch_org(self) -> None:
        """Create shape-based scratch org."""
        logger.step("シェイプベーススクラッチ組織の作成")
        logger.info("シェイプベース作成機能は今後実装予定です")

    def _get_devhub_org(self) -> Optional[str]:
        """Get DevHub organization."""
        try:
            sf_cli.load_org_cache()
            devhub_orgs = []

            # Get DevHub orgs from cache (型安全)
            cache = sf_cli._org_cache or {}
            result_part = cache.get("result", {}) if isinstance(cache, dict) else {}
            if not isinstance(result_part, dict):
                result_part = {}
            devhubs_raw = result_part.get("devHubs", cache.get("devHubs", []))
            devhubs = devhubs_raw if isinstance(devhubs_raw, list) else []

            for org in devhubs:
                if not isinstance(org, dict):
                    continue
                alias = org.get("alias")
                username = org.get("username")
                value = (alias or username) or None
                if isinstance(value, str):
                    devhub_orgs.append(value)

            if not devhub_orgs:
                logger.error("認証済みのDevHub組織が見つかりません")
                logger.info(
                    "DevHub組織に認証してください: sf org login web --set-default-dev-hub"
                )
                return None

            if len(devhub_orgs) == 1:
                logger.info(f"DevHub組織: {devhub_orgs[0]}")
                return devhub_orgs[0]

            # Multiple DevHubs, let user choose
            choice_index = ui.select_from_menu(
                "DevHub組織を選択してください:", devhub_orgs
            )
            # 型安全に選択結果を返却
            if isinstance(choice_index, int) and 0 <= choice_index < len(devhub_orgs):
                value = devhub_orgs[choice_index]
                return value if isinstance(value, str) else None
            return None

        except Exception as e:
            logger.error(f"DevHub組織の取得に失敗しました: {e}")
            return None

    def _show_scratch_org_details(self, alias: str) -> None:
        """Show scratch org details after creation."""
        try:
            logger.step(f"スクラッチ組織 '{alias}' の詳細情報:")

            command = ["sf", "org", "display", "--target-org", alias, "--json"]
            result = sf_cli.run_command(command, cwd=config.project_root)

            org_info = json.loads(result.stdout)
            result_data = org_info.get("result", {})

            print(f"  Username: {result_data.get('username', 'N/A')}")
            print(f"  Instance URL: {result_data.get('instanceUrl', 'N/A')}")
            print(f"  Expiration: {result_data.get('expirationDate', 'N/A')}")

        except Exception:
            logger.warn("詳細情報の取得に失敗しました")


# Module instance for convenient access
scratch_org_manager = ScratchOrgManager()

"""
Package test and deploy functionality.
Port of scripts/mes-dev-cli/modules/package_deploy.sh
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from rich.box import DOUBLE, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ..core.common import Logger, SalesforceCliError, config, logger, sf_cli, ui
from .package_service import PackageService


class PackageDeployManager:
    """Manage package testing and deployment operations."""

    def __init__(self) -> None:
        self.project_root: Path = config.project_root
        self.dev_package = "SanwaMesPackage-Dev"
        self.prod_package = "SanwaMesPackage-Prod"
        self.console = Console()
        self.svc = PackageService()

    # =========================
    # Menu
    # =========================
    def show_menu(self) -> None:
        """Entry menu with Rich UI: choose Dry Run or Deploy, then environment/org/upgrade."""
        while True:
            self._show_header()

            # Two main actions
            table = Table(
                title="[bold bright_cyan]🚀 パッケージテスト・デプロイ[/bold bright_cyan]",
                header_style="bold bright_blue",
                box=ROUNDED,
                width=90,
            )
            table.add_column("#", justify="center", style="bold yellow", width=3)
            table.add_column("操作", style="white")
            table.add_column("説明", style="dim")
            table.add_row(
                "0",
                "Dry Run",
                "インストールは実行せず、コマンドと前提チェックを行います",
            )
            table.add_row("1", "Deploy", "実際にパッケージをインストールします")
            table.add_row("2", "戻る", "メニューを抜けます")
            self.console.print(table)
            self.console.print()

            try:
                action = ui.select_from_menu(
                    "実行する操作を選択してください:", ["Dry Run", "Deploy", "戻る"]
                )
            except Exception:
                return

            if action == 2:
                return

            # Pick environment (scratch/sandbox/production)
            env = self._pick_environment()
            if not env:
                return

            # Pick upgrade type (with explanation)
            upgrade = self._pick_upgrade_type()

            # Resolve package by environment (Dev or Prod)
            package_id = self._select_package_for_environment(
                "scratch" if env == "scratch" else "deploy"
            )
            if not package_id:
                logger.error("有効なパッケージが選択されませんでした")
                if not ui.confirm("メニューに戻りますか？", default=True):
                    return
                continue

            # Select target org (by env)
            include_scratch = env == "scratch"
            target_org = ui.select_org(
                f"対象組織を選択 ({env})",
                include_scratch=include_scratch,
                return_type="alias",
            )
            if not target_org:
                logger.error("組織が選択されませんでした")
                if not ui.confirm("メニューに戻りますか？", default=True):
                    return
                continue

            if action == 0:
                # Dry Run (simulation)
                self._simulate_install(env, target_org, package_id, upgrade)
            else:
                # Deploy
                self._execute_install(env, target_org, package_id, upgrade)

            if not ui.confirm("パッケージテスト・デプロイを続けますか？", default=True):
                return

    # -------------------------
    # Rich helpers
    # -------------------------
    def _show_header(self) -> None:
        panel = Panel(
            Text.assemble(
                ("📦 ", "bold green"),
                ("Package Install", "bold cyan"),
                ("  |  ", "dim"),
                ("Upgrade Type 対応 (Unlocked)", "magenta"),
            ),
            title="[bold bright_blue]パッケージテスト・デプロイ[/bold bright_blue]",
            border_style="bright_blue",
            box=DOUBLE,
            width=90,
        )
        self.console.print(panel)
        self.console.print(Rule(style="bright_blue"))

    def _pick_environment(self) -> Optional[str]:
        table = Table(
            title="[bold]対象環境を選択[/bold]",
            header_style="bold white",
            box=ROUNDED,
            width=90,
        )
        table.add_column("#", justify="center", width=3, style="bold yellow")
        table.add_column("環境", style="white")
        table.add_column("説明", style="dim")
        table.add_row("0", "scratch", "スクラッチ組織に対して実行 (Devパッケージ)")
        table.add_row("1", "sandbox", "Sandboxに対して実行 (Prodパッケージ)")
        table.add_row("2", "production", "本番組織に対して実行 (Prodパッケージ)")
        self.console.print(table)
        try:
            idx = ui.select_from_menu(
                "対象環境を選択してください:", ["scratch", "sandbox", "production"]
            )
            return ["scratch", "sandbox", "production"][idx]
        except Exception:
            return None

    def _pick_upgrade_type(self) -> str:
        desc = {
            "DeprecateOnly": "削除対象をすべて非推奨にマーク (削除はしない)",
            "Mixed": "安全に削除できるものは削除し、その他は非推奨 (既定)",
            "Delete": "依存のない削除対象を削除 (一部データ喪失の可能性)",
        }
        table = Table(
            title="[bold]Upgrade Type を選択 (Unlockedのみ)[/bold]",
            header_style="bold white",
            box=ROUNDED,
            width=90,
        )
        table.add_column("#", justify="center", width=3, style="bold yellow")
        table.add_column("タイプ", style="white")
        table.add_column("説明", style="dim")
        for i, key in enumerate(["DeprecateOnly", "Mixed", "Delete"]):
            table.add_row(str(i), key, desc[key])
        self.console.print(table)
        try:
            idx = ui.select_from_menu(
                "Upgrade Type を選択してください (既定: Mixed):",
                ["DeprecateOnly", "Mixed", "Delete"],
            )
            return ["DeprecateOnly", "Mixed", "Delete"][idx]
        except Exception:
            return "Mixed"

    # -------------------------
    # Execution paths
    # -------------------------
    def _simulate_install(
        self, environment: str, target_org: str, package_id: str, upgrade_type: str
    ) -> None:
        """Show command and perform basic checks. No side effects."""
        wait_time = {"scratch": 20, "sandbox": 30, "production": 45}[environment]
        cmd = [
            "sf",
            "package",
            "install",
            "--package",
            package_id,
            "--target-org",
            target_org,
            "--wait",
            str(wait_time),
            "--no-prompt",
            "--upgrade-type",
            upgrade_type,
        ]
        info_text = Text.assemble(
            ("これはドライランです。インストールは実行されません。\n\n", "bold yellow"),
            ("実行予定コマンド:\n", "bold white"),
            (" "),
            (" ".join(cmd), "cyan"),
            ("\n\nUpgrade Type:", "bold white"),
            (f" {upgrade_type}", "green"),
        )
        info = Panel(
            info_text,
            title="[bold bright_yellow]Dry Run[/bold bright_yellow]",
            border_style="yellow",
            box=ROUNDED,
            width=100,
        )
        self.console.print(info)
        # Preflight checks: validate package id format
        if not self._validate_package_version_id(package_id):
            logger.warn(
                "パッケージIDの形式が正しくありません (04t...)。Dry Run のため続行しません。"
            )

    def _execute_install(
        self, environment: str, target_org: str, package_id: str, upgrade_type: str
    ) -> None:
        wait_time = {"scratch": 20, "sandbox": 30, "production": 45}[environment]
        logger.step(
            {
                "scratch": "パッケージテスト実行中...",
                "sandbox": "Sandboxデプロイ実行中...",
                "production": "本番デプロイ実行中...",
            }[environment]
        )
        logger.info(f"対象組織: {target_org}")
        logger.info(f"パッケージ: {package_id}")
        cmd = [
            "sf",
            "package",
            "install",
            "--package",
            package_id,
            "--target-org",
            target_org,
            "--wait",
            str(wait_time),
            "--installation-key",
            "",
            "--no-prompt",
            "--upgrade-type",
            upgrade_type,
        ]
        try:
            # 長時間実行になりやすいためストリーミング表示
            self.svc._run_with_streaming(
                cmd, title="パッケージインストール中", log_basename="package_install"
            )
        except SalesforceCliError:
            if environment == "scratch":
                logger.error("パッケージテストに失敗しました")
            elif environment == "sandbox":
                logger.error("Sandboxデプロイに失敗しました")
                self._record_deployment_history(
                    package_id, target_org, "Sandbox", "Failed"
                )
            else:
                logger.error("本番デプロイに失敗しました")
                self._record_deployment_history(
                    package_id, target_org, "Production", "Failed"
                )
                logger.warn("緊急対応が必要な場合があります")
                logger.info("ロールバック手順を確認してください")
            return
        # Success
        if environment == "scratch":
            logger.success("パッケージテスト完了")
            logger.step("テスト結果の確認")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass
            if ui.confirm("テスト結果を確認しましたか？", default=False):
                logger.success("テスト完了")
        elif environment == "sandbox":
            logger.success("Sandboxデプロイ完了")
            self._record_deployment_history(
                package_id, target_org, "Sandbox", "Success"
            )
            logger.step("デプロイ後の確認")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass
        else:
            logger.success("🎉 本番デプロイ完了")
            self._record_deployment_history(
                package_id, target_org, "Production", "Success"
            )
            logger.step("デプロイ後の確認")
            logger.info("本番環境での動作確認を実施してください")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass

    # =========================
    # Core actions
    # =========================
    def _deploy_package(self, environment: str) -> None:
        """Deploy or test package based on environment."""
        env_name = ""
        package_env = "deploy"  # scratch or deploy
        wait_time = 30
        org_prompt = "組織エイリアス"
        org_default = ""

        if environment == "scratch":
            env_name = "スクラッチ組織でのパッケージテスト"
            package_env = "scratch"
            wait_time = 20
            org_prompt = "スクラッチ組織エイリアス"
            org_default = f"test-scratch-{datetime.now():%Y%m%d}"
        elif environment == "sandbox":
            env_name = "Sandboxへのパッケージデプロイ"
            package_env = "deploy"
            wait_time = 30
            org_prompt = "Sandbox組織エイリアス"
            org_default = "mesdev"
        elif environment == "production":
            env_name = "本番環境へのパッケージデプロイ"
            package_env = "deploy"
            wait_time = 45
            org_prompt = "本番組織エイリアス"
            org_default = "prod"

        logger.step(env_name)

        package_id = self._select_package_for_environment(package_env)
        if not package_id:
            logger.error("有効なパッケージが選択されませんでした")
            return

        target_org = ui.get_user_input(org_prompt, org_default)
        if not target_org:
            logger.error("組織エイリアスが入力されませんでした")
            return

        # Confirmations
        if environment == "production":
            logger.warn("🚨 本番環境デプロイメント - 厳重確認 🚨")
            print(f"対象組織: {target_org}")
            print(f"パッケージ: {package_id}")
            print()
            logger.warn("⚠️  この操作は本番環境に影響を与えます")
            print()
            logger.warn("本番デプロイ前のチェックリスト:")
            print("□ Sandboxでのテストが完了している")
            print("□ 関係者への事前通知が完了している")
            print("□ ロールバック手順が準備されている")
            print("□ メンテナンス時間内での実行である")
            print()
            if not ui.confirm("すべてのチェック項目を確認しましたか？", default=False):
                logger.info("本番デプロイをキャンセルしました")
                return
            # Require literal 'yes'
            text = ui.get_user_input(
                "最終確認: 実行する場合は 'yes' と入力してください"
            )
            if text.strip().lower() != "yes":
                logger.info("本番デプロイをキャンセルしました")
                return
        elif environment == "sandbox":
            logger.warn("⚠️  Sandboxデプロイメント確認")
            print(f"対象組織: {target_org}")
            print(f"パッケージ: {package_id}")
            if not ui.confirm("デプロイメントを実行しますか？", default=False):
                logger.info("デプロイメントをキャンセルしました")
                return
        else:
            logger.info("スクラッチ組織テスト確認")
            print(f"対象組織: {target_org}")
            print(f"パッケージ: {package_id}")
            if not ui.confirm("テストを実行しますか？", default=False):
                logger.info("テストをキャンセルしました")
                return

        # Execute install
        step_name = {
            "scratch": "パッケージテスト実行中...",
            "sandbox": "Sandboxデプロイ実行中...",
            "production": "本番デプロイ実行中...",
        }[environment]
        logger.step(step_name)
        logger.info(f"対象組織: {target_org}")
        logger.info(f"パッケージ: {package_id}")

        cmd = [
            "sf",
            "package",
            "install",
            "--package",
            package_id,
            "--target-org",
            target_org,
            "--wait",
            str(wait_time),
            "--installation-key",
            "",
            "--no-prompt",
        ]

        try:
            self.svc._run_with_streaming(
                cmd, title="パッケージインストール中", log_basename="package_install"
            )
        except SalesforceCliError:
            # Failure handling
            if environment == "scratch":
                logger.error("パッケージテストに失敗しました")
            elif environment == "sandbox":
                logger.error("Sandboxデプロイに失敗しました")
                self._record_deployment_history(
                    package_id, target_org, "Sandbox", "Failed"
                )
            else:
                logger.error("本番デプロイに失敗しました")
                self._record_deployment_history(
                    package_id, target_org, "Production", "Failed"
                )
                logger.warn("緊急対応が必要な場合があります")
                logger.info("ロールバック手順を確認してください")
            return

        # Success handling
        if environment == "scratch":
            logger.success("パッケージテスト完了")
            logger.step("テスト結果の確認")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass
            if ui.confirm("テスト結果を確認しましたか？", default=False):
                logger.success("テスト完了")
        elif environment == "sandbox":
            logger.success("Sandboxデプロイ完了")
            self._record_deployment_history(
                package_id, target_org, "Sandbox", "Success"
            )
            logger.step("デプロイ後の確認")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass
        else:
            logger.success("🎉 本番デプロイ完了")
            self._record_deployment_history(
                package_id, target_org, "Production", "Success"
            )
            logger.step("デプロイ後の確認")
            logger.info("本番環境での動作確認を実施してください")
            try:
                self.svc._run_with_streaming(
                    ["sf", "org", "open", "--target-org", target_org],
                    title="Org をブラウザで開く",
                    log_basename="org_open",
                )
            except SalesforceCliError:
                pass

    # =========================
    # Utilities
    # =========================
    def _select_package_for_environment(self, package_env: str) -> Optional[str]:
        """Return selected SubscriberPackageVersionId for environment.
        package_env: 'scratch' -> Dev package, otherwise Prod package
        """
        if package_env == "scratch":
            package_name = self.dev_package
            Logger.info("テスト対象のパッケージバージョン（Dev版）を選択してください")
        else:
            package_name = self.prod_package
            Logger.info(
                "デプロイ対象のパッケージバージョン（Prod版）を選択してください"
            )

        versions = self._get_package_versions(package_name)
        if not versions:
            logger.warn(f"{package_name} のパッケージバージョンが見つかりません")
            logger.info("まずパッケージバージョンを作成してください")
            return None

        # Present as a menu for convenience
        choice_idx = ui.select_from_menu(
            "利用可能なバージョンから選択してください:", versions
        )
        # Extract ID from selected line (format: '04t... - Version (CreatedDate)')
        selected_line = versions[choice_idx]
        pkg_id = selected_line.split()[0]
        if self._validate_package_version_id(pkg_id):
            return pkg_id
        # Fallback: ask manual input
        typed = ui.get_user_input("パッケージバージョンID (04t...)")
        return typed if self._validate_package_version_id(typed) else None

    def _record_deployment_history(
        self, package_id: str, target_org: str, environment: str, status: str
    ) -> None:
        history_file = self.project_root / "logs" / "deploy-history.log"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(
                f"{timestamp} | {environment} | {target_org} | {package_id} | {status}\n"
            )
        logger.info(f"デプロイ履歴を記録しました: {history_file}")

    def _check_package_dependencies(self) -> None:
        logger.step("パッケージ依存関係の確認")
        package_version_id = ui.get_user_input("パッケージバージョンID (04t...)")
        if not self._validate_package_version_id(package_version_id):
            return

        target_org = ui.get_user_input("調査対象組織エイリアス")
        if not target_org:
            logger.error("組織エイリアスが入力されませんでした")
            return

        logger.step("依存関係を調査中...")
        try:
            res = sf_cli.run_command(
                [
                    "sf",
                    "data",
                    "query",
                    "--target-org",
                    target_org,
                    "--query",
                    f"SELECT Name, Dependencies FROM SubscriberPackageVersion WHERE Id='{package_version_id}'",
                    "--result-format",
                    "json",
                ],
                cwd=self.project_root,
                capture_output=True,
                check=False,
            )
            data = json.loads(res.stdout or "{}")
            recs = (data.get("result", {}) or {}).get("records", [])
            if recs:
                name = recs[0].get("Name") or "不明"
                print(f"パッケージ名: {name}")
                print()
                Logger.info("依存関係:")
                deps = recs[0].get("Dependencies", {})
                ids = ((deps or {}).get("ids", [])) if isinstance(deps, dict) else []
                if ids:
                    for item in ids:
                        print(item.get("subscriberPackageVersionId", ""))
                else:
                    print("依存関係なし")
            else:
                logger.error("パッケージ情報を取得できませんでした")
        except Exception as e:
            logger.error(f"依存関係取得中にエラー: {e}")

    def _check_deploy_history(self) -> None:
        logger.step("デプロイ履歴の確認")
        target_org = ui.get_user_input("履歴確認対象組織エイリアス")
        if not target_org:
            logger.error("組織エイリアスが入力されませんでした")
            return
        logger.step("インストール済みパッケージを確認中...")
        try:
            sf_cli.run_command(
                ["sf", "package", "installed", "list", "--target-org", target_org],
                cwd=self.project_root,
                check=False,
            )
        except Exception:
            pass

    # =========================
    # Low level helpers
    # =========================
    def _get_package_versions(self, package_name: str) -> List[str]:
        try:
            res = subprocess.run(
                [
                    "sf",
                    "package",
                    "version",
                    "list",
                    "--packages",
                    package_name,
                    "--json",
                ],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            data = json.loads(res.stdout or "{}")
            result = data.get("result", []) or data.get("records", [])
            out: List[str] = []
            for rec in result or []:
                spv = rec.get("SubscriberPackageVersionId") or rec.get("Id") or ""
                ver = rec.get("Version") or rec.get("versionNumber") or ""
                created = rec.get("CreatedDate") or rec.get("createdDate") or ""
                if spv:
                    out.append(f"{spv} - {ver} ({created})")
            return out
        except Exception:
            return []

    def _validate_package_version_id(self, package_version_id: Optional[str]) -> bool:
        if not package_version_id:
            logger.error("パッケージバージョンIDが入力されていません")
            return False
        if not re.fullmatch(r"04t[a-zA-Z0-9]{15}", package_version_id):
            logger.error(f"無効なパッケージバージョンIDです: {package_version_id}")
            return False
        return True


# Module instance for convenient access
package_deploy_manager = PackageDeployManager()

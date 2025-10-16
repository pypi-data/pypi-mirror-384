"""
MES package management functionality.
Port of scripts/mes-dev-cli/modules/mes_package.sh
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

from ..core.common import Logger, SalesforceCliError, config, logger, sf_cli, ui
from .package_service import PackageService


class MesPackageManager:
    """MES package management functionality."""

    def __init__(self) -> None:
        self.mes_package_name_dev = "SanwaMesPackage-Dev"
        self.mes_package_name_prod = "SanwaMesPackage-Prod"
        self.mes_package_path = "sanwa-mes"
        self.project_root = config.project_root
        self.svc = PackageService()
        self.console = Console()

    def show_menu(self) -> None:
        """Show MES package management menu."""
        while True:
            logger.info("MES パッケージ管理")

            options = [
                "新規パッケージ作成 (Dev)",
                "新規パッケージ作成 (Prod)",
                "パッケージバージョン作成 (Dev)",
                "パッケージバージョン作成 (Prod)",
                "パッケージ一覧表示",
                "メタデータ取得・更新",
                "デプロイ確認 (Dry Run)",
                "依存関係設定確認",
                "パッケージ削除",
                "パッケージバージョン削除",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("操作を選択してください:", options)

                if choice == 0:  # 新規パッケージ作成 (Dev)
                    self._create_mes_package("dev")
                elif choice == 1:  # 新規パッケージ作成 (Prod)
                    self._create_mes_package("prod")
                elif choice == 2:  # パッケージバージョン作成 (Dev)
                    self._create_mes_package_version("dev")
                elif choice == 3:  # パッケージバージョン作成 (Prod)
                    self._create_mes_package_version("prod")
                elif choice == 4:  # パッケージ一覧表示
                    self._list_mes_packages()
                elif choice == 5:  # メタデータ取得・更新
                    self._update_mes_metadata()
                elif choice == 6:  # デプロイ確認 (Dry Run)
                    self._deploy_dry_run()
                elif choice == 7:  # 依存関係設定確認
                    self._check_mes_dependencies()
                elif choice == 8:  # パッケージ削除
                    self._delete_package()
                elif choice == 9:  # パッケージバージョン削除
                    self._delete_package_version()
                elif choice == 10:  # 戻る
                    return

                # 操作完了後、続行確認
                if not ui.confirm("MES パッケージ管理を続けますか？", default=True):
                    return

            except Exception as e:
                logger.error(f"操作中にエラーが発生しました: {e}")
                if not ui.confirm("MES パッケージ管理を続けますか？", default=True):
                    return

    def _create_mes_package(self, package_type: str) -> None:
        """Create MES package (dev or prod)."""
        logger.step(f"MES パッケージの新規作成 ({package_type})")
        devhub = self.svc.ensure_devhub()
        if not devhub:
            logger.error("DevHub組織の確認/認証に失敗しました")
            return

        package_name = (
            self.mes_package_name_prod
            if package_type == "prod"
            else self.mes_package_name_dev
        )

        cmd: List[str] = [
            "sf",
            "package",
            "create",
            "--name",
            package_name,
            "--path",
            self.mes_package_path,
            "--package-type",
            "Unlocked",
            "--target-dev-hub",
            devhub,
        ]

        if package_type == "prod":
            cmd.append("--org-dependent")
            logger.info("Prod版のため、組織依存パッケージとして作成されます")

        logger.step("パッケージを作成中...")
        try:
            # 短時間の可能性もあるが、標準化のためストリーミング表示
            self.svc._run_with_streaming(
                cmd, title="MES パッケージ作成", log_basename="mes_pkg_create"
            )
            logger.success(f"MES パッケージ ({package_type}) が作成されました")

            # Show created package lines
            try:
                res = subprocess.run(
                    ["sf", "package", "list"],
                    cwd=self.project_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                lines = [
                    ln
                    for ln in res.stdout.splitlines()
                    if package_name in ln or "Package Id" in ln
                ]
                if lines:
                    for ln in lines:
                        Logger.info(ln)
            except Exception:
                pass
        except SalesforceCliError:
            logger.error(f"MES パッケージ ({package_type}) の作成に失敗しました")
            return

    def _create_mes_package_version(self, package_type: str) -> None:
        """Create MES package version (dev or prod)."""
        logger.step(f"MES パッケージバージョンの作成 ({package_type})")
        devhub = self.svc.ensure_devhub()
        if not devhub:
            logger.error("DevHub組織の確認/認証に失敗しました")
            return

        package_name = (
            self.mes_package_name_prod
            if package_type == "prod"
            else self.mes_package_name_dev
        )

        if package_type == "dev":
            if ui.confirm("依存関係設定を確認しますか？"):
                self._show_dependency_config()

        wait_default = str(config.default_wait_time)
        wait_time = ui.get_user_input("待機時間 (分)", wait_default) or wait_default

        cmd: List[str] = [
            "sf",
            "package",
            "version",
            "create",
            "--package",
            package_name,
            "--installation-key-bypass",
            "--wait",
            wait_time,
            "--target-dev-hub",
            devhub,
            "--verbose",
        ]

        logger.step(f"パッケージバージョンを作成中... (最大 {wait_time} 分)")
        try:
            # 長時間実行のためストリーミング表示
            self.svc._run_with_streaming(
                cmd,
                title="MES パッケージバージョン作成",
                log_basename="mes_pkg_version_create",
            )
            logger.success(
                f"MES パッケージバージョン ({package_type}) が作成されました"
            )
            # Show latest version (ascending list → take last)
            versions = self._get_package_versions(package_name)
            latest = versions[-1] if versions else None
            if latest:
                Logger.info("最新のパッケージバージョン:")
                Logger.info(latest)
        except SalesforceCliError:
            logger.error(
                f"MES パッケージバージョン ({package_type}) の作成に失敗しました"
            )
            return

    def _list_mes_packages(self) -> None:
        """List MES packages and versions."""
        logger.step("MES パッケージ一覧を表示中...")

        # 1) MES パッケージ（Dev/Prod）行を JSON から抽出して表示
        pkgs = self.svc.list_packages()
        ptable = Table(
            title="MES パッケージ一覧", header_style="bold white", box=ROUNDED
        )
        ptable.add_column("Package Name", style="cyan", overflow="fold")
        ptable.add_column("Package Id", style="white", overflow="ellipsis")
        ptable.add_column("Type", style="white")
        ptable.add_column("Alias", style="white")

        shown = False
        for p in pkgs or []:
            nm = p.get("Name") or p.get("name") or ""
            if nm not in (self.mes_package_name_dev, self.mes_package_name_prod):
                continue
            pid = p.get("Id") or p.get("id") or ""
            ptype = p.get("ContainerOptions") or p.get("packageType") or ""
            alias = p.get("Alias") or p.get("alias") or ""
            ptable.add_row(nm, pid, ptype, alias)
            shown = True

        if shown:
            self.console.print(ptable)
        else:
            logger.warn("MES パッケージが見つかりません")

        # 2) Dev バージョン
        vtable_dev = Table(
            title="MES Dev パッケージバージョン", header_style="bold white", box=ROUNDED
        )
        vtable_dev.add_column("Version", style="cyan", overflow="fold")
        vtable_dev.add_column("SPV Id", style="white", overflow="ellipsis")
        vtable_dev.add_column("Released", style="white")
        vtable_dev.add_column("Created", style="white", overflow="fold")

        dev_json = self.svc.list_package_versions(self.mes_package_name_dev)
        if dev_json:
            for rec in dev_json:
                ver = rec.get("Version") or rec.get("versionNumber") or ""
                spv = rec.get("SubscriberPackageVersionId") or rec.get("Id") or ""
                rel = rec.get("IsReleased")
                if rel is None:
                    rel = rec.get("isReleased")
                created = rec.get("CreatedDate") or rec.get("createdDate") or ""
                vtable_dev.add_row(
                    str(ver), spv, ("Yes" if rel else "No"), str(created)
                )
            self.console.print()
            self.console.print(vtable_dev)
        else:
            logger.warn("MES Dev パッケージバージョンが見つかりません")

        # 3) Prod バージョン
        vtable_prod = Table(
            title="MES Prod パッケージバージョン",
            header_style="bold white",
            box=ROUNDED,
        )
        vtable_prod.add_column("Version", style="cyan", overflow="fold")
        vtable_prod.add_column("SPV Id", style="white", overflow="ellipsis")
        vtable_prod.add_column("Released", style="white")
        vtable_prod.add_column("Created", style="white", overflow="fold")

        prod_json = self.svc.list_package_versions(self.mes_package_name_prod)
        if prod_json:
            for rec in prod_json:
                ver = rec.get("Version") or rec.get("versionNumber") or ""
                spv = rec.get("SubscriberPackageVersionId") or rec.get("Id") or ""
                rel = rec.get("IsReleased")
                if rel is None:
                    rel = rec.get("isReleased")
                created = rec.get("CreatedDate") or rec.get("createdDate") or ""
                vtable_prod.add_row(
                    str(ver), spv, ("Yes" if rel else "No"), str(created)
                )
            self.console.print()
            self.console.print(vtable_prod)
        else:
            logger.warn("MES Prod パッケージバージョンが見つかりません")

    def _update_mes_metadata(self) -> None:
        """Update MES metadata: retrieve, convert, sync, format."""
        logger.step("MES メタデータの更新")

        source_org = ui.select_org(
            "メタデータ取得元", include_scratch=False, return_type="alias"
        )
        if not source_org:
            logger.error("組織が選択されませんでした")
            return

        manifest_file = ui.get_user_input("マニフェストファイル", "manifest/mes.xml")
        manifest_path = (self.project_root / manifest_file).resolve()
        if not manifest_path.exists():
            logger.error(f"マニフェストファイルが見つかりません: {manifest_file}")
            return

        Logger.info("メタデータ取得設定:")
        print(f"  取得元組織: {source_org}")
        print(f"  マニフェスト: {manifest_file}")
        print(f"  取得先: {self.mes_package_path} ディレクトリ")

        if not ui.confirm("この設定でメタデータを取得しますか？"):
            logger.info("取得をキャンセルしました")
            return

        self.svc.retrieve_convert_sync(manifest_file, source_org, self.mes_package_path)

    def _deploy_dry_run(self) -> None:
        """Run dry-run deployment for selected manifest/org/test level."""
        logger.step("MES パッケージ デプロイ確認 (Dry Run)")

        # Manifest selection
        options = [
            "mes.xml (MESパッケージメタデータ)",
            "core.xml (基盤メタデータ)",
            "package.xml (Package.xml Generator作業用)",
            "カスタム指定",
        ]
        choice = ui.select_from_menu("使用するマニフェストファイルを選択:", options)

        manifest_file = ""
        if choice == 0:
            manifest_file = "manifest/mes.xml"
        elif choice == 1:
            manifest_file = "manifest/core.xml"
        elif choice == 2:
            manifest_file = "manifest/package.xml"
        elif choice == 3:
            manifest_file = ui.get_user_input("マニフェストファイルパス", "manifest/")

        if not (self.project_root / manifest_file).exists():
            logger.error(f"マニフェストファイルが見つかりません: {manifest_file}")
            return

        # Target org selection
        target_org = ui.select_org(
            "デプロイ確認先組織", include_scratch=False, return_type="alias"
        )
        if not target_org:
            logger.error("組織が選択されませんでした")
            return

        # Test level selection
        test_options = [
            "NoTestRun (テスト実行なし)",
            "RunLocalTests (ローカルテストのみ)",
            "RunAllTestsInOrg (全テスト実行)",
            "RunSpecifiedTests (指定テストのみ)",
        ]
        t_choice = ui.select_from_menu(
            "テストレベルを選択(推奨 -> 2:RunLocalTests):", test_options
        )
        test_level = "NoTestRun"
        specified_tests = ""
        if t_choice == 0:
            test_level = "NoTestRun"
        elif t_choice == 1:
            test_level = "RunLocalTests"
        elif t_choice == 2:
            test_level = "RunAllTestsInOrg"
        elif t_choice == 3:
            test_level = "RunSpecifiedTests"
            specified_tests = ui.get_user_input("実行するテストクラス名 (カンマ区切り)")

        Logger.info("デプロイ確認設定:")
        print(f"  マニフェスト: {manifest_file}")
        print(f"  対象組織: {target_org}")
        print(f"  テストレベル: {test_level}")
        if specified_tests:
            print(f"  指定テスト: {specified_tests}")
        print("  実行モード: Dry Run (実際のデプロイは行われません)")

        if not ui.confirm("この設定でデプロイ確認を実行しますか？"):
            logger.info("デプロイ確認をキャンセルしました")
            return

        try:
            self.svc.deploy_dry_run_by_manifest(
                manifest_file, target_org, test_level, specified_tests
            )
            logger.success("✅ デプロイ確認が完了しました")
        except SalesforceCliError:
            logger.error("❌ デプロイ確認でエラーが発生しました")

    def _check_mes_dependencies(self) -> None:
        """Show dependency configuration and recommended dependencies."""
        logger.step("MES パッケージの依存関係設定確認")

        sfdx_project = self.project_root / "sfdx-project.json"
        if sfdx_project.exists():
            try:
                data = json.loads(sfdx_project.read_text(encoding="utf-8"))
                Logger.info("sfdx-project.json の依存関係設定:")
                deps_shown = False
                for d in data.get("packageDirectories", []):
                    if d.get("package") in ("SanwaMesPackage", "sanwa-mes"):
                        deps = d.get("dependencies", [])
                        if deps:
                            for item in deps:
                                pkg = item.get("package", "")
                                ver = item.get("versionNumber", "LATEST")
                                print(f"- {pkg}: {ver}")
                                deps_shown = True
                if not deps_shown:
                    logger.warn("依存関係が設定されていません")
            except Exception as e:
                logger.warn(f"依存関係の読み取りに失敗しました: {e}")
        else:
            logger.error("sfdx-project.json が見つかりません")

        print()
        Logger.info("推奨される依存パッケージ:")
        self._show_recommended_dependencies()

    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_devhub_org(self) -> Optional[str]:
        """Ensure DevHub org (alias 'prod') is authenticated and reachable."""
        alias = "prod"
        # Try display
        res = subprocess.run(
            ["sf", "org", "display", "--target-org", alias],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            return alias

        Logger.error(f"DevHub組織 '{alias}' への認証が必要です")
        if not ui.confirm("DevHub組織 'prod' への認証を実行しますか？"):
            return None

        # Login
        try:
            sf_cli.run_command(
                [
                    "sf",
                    "org",
                    "login",
                    "web",
                    "--alias",
                    alias,
                    "--set-default-dev-hub",
                ],
                cwd=self.project_root,
                check=True,
            )
        except SalesforceCliError:
            Logger.error("DevHub組織の認証に失敗しました")
            return None

        # Verify
        res2 = subprocess.run(
            ["sf", "org", "display", "--target-org", alias],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        if res2.returncode == 0:
            Logger.success("DevHub接続テスト: OK")
            return alias
        Logger.error("DevHub接続テスト: NG")
        return None

    def _get_package_versions(self, package_name: str) -> List[str]:
        """Return list of formatted version strings for a package."""
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
                if spv or ver or created:
                    out.append(f"{spv} - {ver} ({created})")
            return out
        except Exception:
            return []

    def _retrieve_mes_metadata_with_temp_dir(
        self, manifest_file: str, source_org: str, target_dir: str
    ) -> None:
        """Retrieve metadata (mdapi), convert to source, rsync to target, format, cleanup."""
        work_dir = (
            self.project_root
            / f"temp-mes-retrieve-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        md_dir = work_dir / "mdapi"
        src_dir = work_dir / "src"

        logger.step("1) 作業ディレクトリの準備")
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir)
            md_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"作業ディレクトリの準備に失敗しました: {e}")
            return

        logger.step("2) メタデータを Metadata API 形式で取得中")
        try:
            self.svc._run_with_streaming(
                [
                    "sf",
                    "project",
                    "retrieve",
                    "start",
                    "--manifest",
                    manifest_file,
                    "--target-org",
                    source_org,
                    "--target-metadata-dir",
                    str(md_dir),
                    "--unzip",
                ],
                title="メタデータ取得中",
                log_basename="mes_retrieve",
            )
        except SalesforceCliError:
            logger.error("メタデータの取得に失敗しました")
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        md_root = md_dir / "unpackaged"
        if not md_root.exists():
            logger.error(f"取得されたメタデータが見つかりません: {md_root}")
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        logger.step("3) Metadata API → Source 形式に変換中")
        try:
            self.svc._run_with_streaming(
                [
                    "sf",
                    "project",
                    "convert",
                    "mdapi",
                    "--root-dir",
                    str(md_root),
                    "--output-dir",
                    str(src_dir),
                ],
                title="形式変換中 (mdapi→source)",
                log_basename="mes_convert_mdapi",
            )
        except SalesforceCliError:
            logger.error("メタデータ形式の変換に失敗しました")
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        logger.step(f"4) rsync で {target_dir} に同期中")
        try:
            target_path = self.project_root / target_dir
            target_path.mkdir(parents=True, exist_ok=True)
            rsync_cmd = [
                "rsync",
                "-av",
                "--delete",
                f"{src_dir}/",
                f"{target_path}/",
            ]
            # rsync は出力が多いためストリーミング表示
            self.svc._run_with_streaming(
                rsync_cmd,
                title=f"rsync 同期中 → {target_dir}",
                log_basename="mes_rsync",
            )
            logger.success(f"MES メタデータの更新が完了しました: {target_dir}")

            # 結果の表示
            try:
                file_count = sum(1 for _ in target_path.rglob("*") if _.is_file())
                logger.info(f"更新されたファイル数: {file_count}")
                main_default = target_path / "main" / "default"
                if main_default.exists():
                    metadata_dirs = sum(1 for p in main_default.iterdir() if p.is_dir())
                    logger.info(f"メタデータディレクトリ数: {metadata_dirs}")
            except Exception:
                pass

            logger.step("5) 取得したメタデータのフォーマット統一中")
            self._apply_metadata_formatting(str(target_path))
        except subprocess.CalledProcessError:
            logger.error("rsync による同期に失敗しました")
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        finally:
            logger.step("6) 作業ディレクトリのクリーンアップ")
            shutil.rmtree(work_dir, ignore_errors=True)
            logger.success(f"✔ 完了: {target_dir} を最新化しました")

    def _apply_metadata_formatting(self, target_dir: str) -> None:
        """Apply formatting using Prettier when available."""
        logger.info("  Prettierでフォーマット適用中...")
        self._format_with_prettier(target_dir)
        logger.success("  フォーマット統一完了")

    def _format_with_prettier(self, target_dir: str) -> None:
        if shutil.which("npx") is None:
            logger.warn("    npx/Prettierが利用できません（スキップします）")
            return
        # Apply to XML
        try:
            subprocess.run(
                ["npx", "prettier", "--write", f"{target_dir}/**/*.xml"],
                cwd=self.project_root,
                check=False,
                text=True,
            )
            logger.info("    Prettierフォーマット適用完了")
        except Exception:
            logger.warn("    Prettierフォーマットでエラーが発生しました（続行します）")
        # JS
        try:
            subprocess.run(
                [
                    "bash",
                    "-lc",
                    f"shopt -s nullglob; ls {target_dir}/**/*.js >/dev/null 2>&1 || exit 0; npx prettier --write '{target_dir}/**/*.js'",
                ],
                cwd=self.project_root,
                check=False,
                text=True,
            )
        except Exception:
            pass
        # CSS
        try:
            subprocess.run(
                [
                    "bash",
                    "-lc",
                    f"shopt -s nullglob; ls {target_dir}/**/*.css >/dev/null 2>&1 || exit 0; npx prettier --write '{target_dir}/**/*.css'",
                ],
                cwd=self.project_root,
                check=False,
                text=True,
            )
        except Exception:
            pass

    def _execute_deploy_dry_run(
        self,
        manifest_file: str,
        target_org: str,
        test_level: str,
        specified_tests: str = "",
    ) -> None:
        logger.step("デプロイ確認を実行中...")

        cmd: List[str] = [
            "sf",
            "project",
            "deploy",
            "start",
            "--manifest",
            manifest_file,
            "--target-org",
            target_org,
            "--test-level",
            test_level,
            "--dry-run",
            "--verbose",
        ]

        if specified_tests and test_level == "RunSpecifiedTests":
            cmd.extend(["--tests", specified_tests])

        Logger.info("実行コマンド:")
        print(" ".join(cmd))
        print()

        start = datetime.now()
        try:
            sf_cli.run_command(cmd, cwd=self.project_root, check=True)
            duration = (datetime.now() - start).total_seconds()
            logger.success(
                f"✅ デプロイ確認が完了しました (所要時間: {int(duration)}秒)"
            )
            logger.info("結果: デプロイ可能です")

            print()
            Logger.info("次のステップ:")
            print("  1. パッケージバージョン作成の準備ができています")
            print("  2. 必要に応じて実際のデプロイを実行してください")
            print("  3. 問題がある場合はメタデータを修正してください")
        except SalesforceCliError:
            duration = (datetime.now() - start).total_seconds()
            logger.error(
                f"❌ デプロイ確認でエラーが発生しました (所要時間: {int(duration)}秒)"
            )
            logger.warn("結果: デプロイできません")

            print()
            Logger.info("推奨アクション:")
            print("  1. エラーメッセージを確認してメタデータを修正")
            print("  2. 依存関係や必要なコンポーネントを確認")
            print("  3. 修正後に再度デプロイ確認を実行")
            print("  4. 問題解決後にパッケージバージョン作成を実行")
            return

    def _show_dependency_config(self) -> None:
        logger.info("現在の依存関係設定:")
        sfdx_project = self.project_root / "sfdx-project.json"
        if sfdx_project.exists():
            try:
                data = json.loads(sfdx_project.read_text(encoding="utf-8"))
                for d in data.get("packageDirectories", []):
                    if d.get("package") in ("SanwaMesPackage", "sanwa-mes"):
                        print(
                            json.dumps(
                                d.get("dependencies", []), indent=2, ensure_ascii=False
                            )
                        )
                        return
                logger.warn("依存関係が設定されていません")
            except Exception as e:
                logger.warn(f"依存関係の読み取りに失敗しました: {e}")

    def _show_recommended_dependencies(self) -> None:
        print("  FlowActionsBasePack: 04t8b000001ZxNVAA0")
        print("  FlowScreenComponentsBasePack: 04t5G000004fz9OQAQ")
        print("  ListEditor: 04t5h000000FElNAAW")
        print("  datatable: 04t5G000004fz9EQAQ")
        print("  BarQR: 04t1U0000058cC1QAI")
        print("  SanwaMesCorePackage: 0.1.0.LATEST")

    # -----------------------------
    # Delete helpers
    # -----------------------------
    def _delete_package(self) -> None:
        """Delete a package selected from sf package list."""
        logger.step("パッケージ削除")

        devhub = self.svc.ensure_devhub()
        if not devhub:
            logger.error("DevHub組織の確認/認証に失敗しました")
            return

        # Fetch packages in JSON
        packages = self.svc.list_packages() or []
        if not packages:
            logger.warn("削除可能なパッケージが見つかりません")
            return

        display: List[str] = []
        for p in packages:
            pid = p.get("Id") or ""
            nm = p.get("Name") or p.get("name") or ""
            als = p.get("Alias") or p.get("alias") or ""
            label = f"{pid} - {nm}"
            if als:
                label += f" (alias: {als})"
            display.append(label)

        idx = ui.select_from_menu("削除するパッケージを選択してください:", display)
        if idx is None:
            return
        selected = packages[idx]
        package_id = selected.get("Id") or selected.get("id")
        package_name = selected.get("Name") or selected.get("name") or package_id

        # Check versions exist
        # 型を保証（None の可能性を排除）
        if not isinstance(package_id, str):
            package_id = str(package_id) if package_id is not None else ""
        versions = self.svc.list_package_versions(package_id)
        if versions:
            logger.warn(
                "このパッケージにはパッケージバージョンが存在します。先にバージョンを削除してください。"
            )
            return

        Logger.info("削除対象:")
        print(f"  パッケージ: {package_name} ({package_id})")
        if not ui.confirm("このパッケージを削除しますか？", default=False):
            logger.info("削除をキャンセルしました")
            return

        try:
            # None を渡さないように変換・検証
            pid = package_id if isinstance(package_id, str) else str(package_id)
            self.svc.delete_package(pid, devhub=devhub, no_prompt=True)
            logger.success("パッケージを削除しました")
        except SalesforceCliError:
            logger.error("パッケージの削除に失敗しました")

    def _delete_package_version(self) -> None:
        """Delete a package version selected from sf package version list."""
        logger.step("パッケージバージョン削除")

        devhub = self.svc.ensure_devhub()
        if not devhub:
            logger.error("DevHub組織の確認/認証に失敗しました")
            return

        # Choose package (to narrow down versions)
        scope_options = [
            f"{self.mes_package_name_dev} (Dev)",
            f"{self.mes_package_name_prod} (Prod)",
            "sf package list から選択",
        ]
        scope = ui.select_from_menu(
            "バージョン一覧の対象パッケージを選択してください:", scope_options
        )
        package_selector = None
        if scope == 0:
            package_selector = self.mes_package_name_dev
        elif scope == 1:
            package_selector = self.mes_package_name_prod
        else:
            # Fetch all packages and let the user choose
            packages = self.svc.list_packages()
            if not packages:
                logger.warn("パッケージが見つかりません")
                return
            disp: List[str] = []
            for p in packages:
                pid = p.get("Id") or ""
                nm = p.get("Name") or p.get("name") or ""
                disp.append(f"{pid} - {nm}")
            pidx = ui.select_from_menu("対象パッケージを選択:", disp)
            package_selector = packages[pidx].get("Id") or packages[pidx].get("Name")

        # List versions for selected package
        versions = self._get_package_versions(str(package_selector))
        if not versions:
            logger.warn("削除可能なパッケージバージョンが見つかりません")
            return
        vidx = ui.select_from_menu("削除するバージョンを選択してください:", versions)
        selected_line = versions[vidx]
        version_id = selected_line.split()[0]

        Logger.info("削除対象:")
        print(f"  パッケージ: {package_selector}")
        print(f"  バージョン: {selected_line}")
        if not ui.confirm(
            "このパッケージバージョンを削除しますか？ (ベータのみ削除可能)",
            default=False,
        ):
            logger.info("削除をキャンセルしました")
            return

        # Execute delete
        try:
            self.svc.delete_package_version(version_id, devhub=devhub, no_prompt=True)
            logger.success("パッケージバージョンを削除しました")
        except SalesforceCliError:
            logger.error(
                "パッケージバージョンの削除に失敗しました（ベータ版のみ削除可能です）"
            )


# Module instance for convenient access
mes_package_manager = MesPackageManager()

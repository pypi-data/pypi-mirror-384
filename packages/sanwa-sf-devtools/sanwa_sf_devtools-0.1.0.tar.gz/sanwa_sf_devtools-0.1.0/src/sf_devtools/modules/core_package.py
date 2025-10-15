"""
Core package management functionality.
Port of scripts/mes-dev-cli/modules/core_package.sh
"""

from pathlib import Path
from typing import List, Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

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
from .package_service import PackageService


class CorePackageManager:
    """Core package management functionality."""

    def __init__(self) -> None:
        self.core_package_name = "SanwaMesCorePackage"
        self.core_package_path = "sanwa-mes-core"
        self.project_root = config.project_root
        self.svc = PackageService()
        self.console = Console()

    def show_menu(self) -> None:
        """Show core package management menu."""
        while True:
            logger.info("Core パッケージ管理")

            options = [
                "新規パッケージ作成",
                "パッケージバージョン作成",
                "パッケージ一覧表示",
                "メタデータ取得・更新",
                "デプロイ確認 (Dry Run)",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("操作を選択してください:", options)

                if choice == 0:  # 新規パッケージ作成
                    self.create_core_package()
                elif choice == 1:  # パッケージバージョン作成
                    self.create_core_package_version()
                elif choice == 2:  # パッケージ一覧表示
                    self.list_core_packages()
                elif choice == 3:  # メタデータ取得・更新
                    self.update_core_metadata()
                elif choice == 4:  # デプロイ確認 (Dry Run)
                    self.deploy_core_dry_run()
                elif choice == 5:  # 戻る
                    return

                # 操作完了後、続行確認
                if not ui.confirm("Core パッケージ管理を続けますか？", default=True):
                    return

            except Exception as e:
                logger.error(f"操作中にエラーが発生しました: {e}")
                if not ui.confirm("Core パッケージ管理を続けますか？", default=True):
                    return

    def create_core_package(self) -> None:
        """Create a new core package."""
        logger.step("Coreパッケージの作成")

        # DevHub認証確認
        devhub = self.svc.ensure_devhub()
        if not devhub:
            return

        # 作成前の確認
        logger.info("パッケージ作成設定:")
        print(f"  パッケージ名: {self.core_package_name}")
        print(f"  パス: {self.core_package_path}")
        print(f"  DevHub: {devhub}")

        if not ui.confirm("この設定でCoreパッケージを作成しますか？"):
            logger.info("作成をキャンセルしました")
            return

        try:
            logger.step("Coreパッケージを作成中...")
            self.svc.create_package(
                name=self.core_package_name,
                path=self.core_package_path,
                unlocked=True,
                org_dependent=False,
                devhub=devhub,
            )
            logger.success("Coreパッケージが作成されました")

            # パッケージIDを表示
            logger.info("作成されたパッケージを確認してください:")
            self._show_package_info()

        except SalesforceCliError:
            logger.error("Coreパッケージの作成に失敗しました")

    def create_core_package_version(self) -> None:
        """Create a new core package version."""
        logger.step("Coreパッケージバージョンの作成")

        # DevHub認証確認
        devhub = self.svc.ensure_devhub()
        if not devhub:
            return

        wait_time = ui.get_user_input("待機時間 (分)", str(config.default_wait_time))

        # 作成前の確認
        logger.info("パッケージバージョン作成設定:")
        print(f"  パッケージ名: {self.core_package_name}")
        print(f"  待機時間: {wait_time} 分")
        print(f"  DevHub: {devhub}")

        if not ui.confirm("この設定でパッケージバージョンを作成しますか？"):
            logger.info("作成をキャンセルしました")
            return

        try:
            logger.step(f"パッケージバージョンを作成中... (最大 {wait_time} 分)")
            self.svc.create_package_version(
                package=self.core_package_name,
                wait_min=int(wait_time or config.default_wait_time),
                devhub=devhub,
                bypass_install_key=True,
                verbose=True,
            )
            logger.success("Coreパッケージバージョンが作成されました")

            # 作成されたバージョン情報を表示（昇順リスト想定 → 末尾を最新として表示）
            logger.info("最新のパッケージバージョン:")
            recs = self.svc.list_package_versions(self.core_package_name)
            if recs:
                last = recs[-1]
                spv = last.get("SubscriberPackageVersionId") or last.get("Id") or ""
                ver = last.get("Version") or last.get("versionNumber") or ""
                created = last.get("CreatedDate") or last.get("createdDate") or ""
                print(f"{spv} - {ver} ({created})")

        except SalesforceCliError:
            logger.error("Coreパッケージバージョンの作成に失敗しました")

    def list_core_packages(self) -> None:
        """List core packages and versions."""
        logger.step("Core パッケージ一覧を表示中...")

        # 1) パッケージ一覧（JSON→必要項目のみ表示）
        packages = self.svc.list_packages()
        table = Table(title="パッケージ一覧", header_style="bold white", box=ROUNDED)
        table.add_column("Package Name", style="cyan", overflow="fold")
        table.add_column("Package Id", style="white", overflow="ellipsis")
        table.add_column("Type", style="white", overflow="fold")
        table.add_column("Alias", style="white", overflow="fold")

        shown_any = False
        for p in packages or []:
            nm = p.get("Name") or p.get("name") or ""
            if nm != self.core_package_name:
                continue
            pid = p.get("Id") or p.get("id") or ""
            ptype = p.get("ContainerOptions") or p.get("packageType") or ""
            alias = p.get("Alias") or p.get("alias") or ""
            table.add_row(nm, pid, ptype, alias)
            shown_any = True

        if shown_any:
            self.console.print(table)
        else:
            logger.warn("Core パッケージが見つかりません")

        # 2) バージョン一覧（JSON→コンパクト表示）
        versions = self.svc.list_package_versions(self.core_package_name)
        vtable = Table(
            title="Core パッケージバージョン", header_style="bold white", box=ROUNDED
        )
        vtable.add_column("Version", style="cyan", overflow="fold")
        vtable.add_column("SPV Id", style="white", overflow="ellipsis")
        vtable.add_column("Released", style="white", overflow="fold")
        vtable.add_column("Created", style="white", overflow="fold")

        if versions:
            for rec in versions:
                ver = rec.get("Version") or rec.get("versionNumber") or ""
                spv = rec.get("SubscriberPackageVersionId") or rec.get("Id") or ""
                released = rec.get("IsReleased")
                if released is None:
                    released = rec.get("isReleased")
                created = rec.get("CreatedDate") or rec.get("createdDate") or ""
                vtable.add_row(
                    str(ver), spv, ("Yes" if released else "No"), str(created)
                )
            self.console.print()
            self.console.print(vtable)
        else:
            logger.warn("Core パッケージバージョンが見つかりません")

    def update_core_metadata(self) -> None:
        """Update core metadata from source org."""
        logger.step("Core メタデータの更新")

        source_org = ui.select_org(
            "メタデータ取得元", include_scratch=False, return_type="alias"
        )
        if not source_org:
            logger.error("組織が選択されませんでした")
            return

        manifest_file = ui.get_user_input("マニフェストファイル", "manifest/core.xml")
        manifest_path = config.project_root / manifest_file

        if not manifest_path.exists():
            logger.error(f"マニフェストファイルが見つかりません: {manifest_file}")
            return

        # 取得前の確認
        logger.info("メタデータ取得設定:")
        print(f"  取得元組織: {source_org}")
        print(f"  マニフェスト: {manifest_file}")
        print(f"  取得先: {self.core_package_path} ディレクトリ")

        if not ui.confirm("この設定でメタデータを取得しますか？"):
            logger.info("取得をキャンセルしました")
            return

        # Retrieve metadata via shared service
        self.svc.retrieve_convert_sync(
            manifest_file, source_org, self.core_package_path
        )

    def deploy_core_dry_run(self) -> None:
        """Perform dry run deployment of core package."""
        logger.step("Core パッケージのデプロイ確認")

        target_org = ui.select_org(
            "デプロイ先", include_scratch=True, return_type="alias"
        )
        if not target_org:
            logger.error("組織が選択されませんでした")
            return

        # 確認
        logger.info("デプロイ確認設定:")
        print(f"  デプロイ先組織: {target_org}")
        print(f"  パッケージパス: {self.core_package_path}")
        print("  モード: Dry Run (実際のデプロイは行われません)")

        if not ui.confirm("この設定でデプロイ確認を実行しますか？"):
            logger.info("デプロイ確認をキャンセルしました")
            return

        try:
            logger.step("デプロイ確認を実行中...")
            self.svc.deploy_dry_run_by_source_dir(self.core_package_path, target_org)
            logger.success("デプロイ確認が完了しました")

        except SalesforceCliError:
            logger.error("デプロイ確認に失敗しました")

    def _get_devhub_org(self) -> Optional[str]:
        """Get DevHub organization."""
        try:
            sf_cli.load_org_cache()
            devhub_orgs = []

            # Get DevHub orgs from cache
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
            return devhub_orgs[choice_index]

        except Exception as e:
            logger.error(f"DevHub組織の取得に失敗しました: {e}")
            return None

    def _show_package_info(self) -> None:
        """Show package information."""
        try:
            result = sf_cli.run_command(
                ["sf", "package", "list"], cwd=config.project_root
            )
            lines = result.stdout.split("\n")

            for line in lines:
                if self.core_package_name in line:
                    print(line)
                    break
        except SalesforceCliError:
            logger.warn("パッケージ情報の表示に失敗しました")

    def _get_package_versions(self) -> List[str]:
        """Get package versions."""
        try:
            command = [
                "sf",
                "package",
                "version",
                "list",
                "--packages",
                self.core_package_name,
                "--verbose",
            ]

            result = sf_cli.run_command(command, cwd=config.project_root)
            lines = result.stdout.strip().split("\n")

            # Skip header line and return version info
            if len(lines) <= 1:
                return []
            return [l for l in lines[1:] if isinstance(l, str)]

        except SalesforceCliError:
            return []

    def _retrieve_core_metadata_with_temp_dir(
        self, manifest_file: str, source_org: str, target_dir: str
    ) -> None:
        """Retrieve metadata using temporary directory approach."""
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        work_dir = config.project_root / f"temp-core-retrieve-{timestamp}"
        md_dir = work_dir / "mdapi"
        src_dir = work_dir / "src"

        try:
            logger.step("1) 作業ディレクトリの準備")
            if work_dir.exists():
                shutil.rmtree(work_dir)
            md_dir.mkdir(parents=True)

            logger.step("2) メタデータを Metadata API 形式で取得中")

            command = [
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
            ]

            sf_cli.run_command(command, cwd=config.project_root)

            # retrieve の結果は md_dir/unpackaged に展開される
            md_root = md_dir / "unpackaged"
            if not md_root.exists():
                logger.error(f"取得されたメタデータが見つかりません: {md_root}")
                return

            logger.step("3) Metadata API → Source 形式に変換中")

            command = [
                "sf",
                "project",
                "convert",
                "mdapi",
                "--root-dir",
                str(md_root),
                "--output-dir",
                str(src_dir),
            ]

            sf_cli.run_command(command, cwd=config.project_root)

            logger.step("4) 変換されたメタデータをコピー中")

            # Copy converted metadata to target directory
            target_path = config.project_root / target_dir
            if target_path.exists():
                # Backup existing directory
                backup_path = config.project_root / f"{target_dir}.backup.{timestamp}"
                logger.info(f"既存ディレクトリをバックアップ: {backup_path}")
                shutil.move(str(target_path), str(backup_path))

            # Copy new metadata
            if src_dir.exists():
                # Find the main source directory in src_dir
                source_dirs = [d for d in src_dir.iterdir() if d.is_dir()]
                if source_dirs:
                    shutil.copytree(str(source_dirs[0]), str(target_path))
                    logger.success(f"メタデータを {target_dir} にコピーしました")
                else:
                    logger.error("変換されたソースディレクトリが見つかりません")
            else:
                logger.error("変換されたメタデータが見つかりません")

        except SalesforceCliError:
            logger.error("メタデータの取得に失敗しました")
        except Exception as e:
            logger.error(f"メタデータ取得中にエラーが発生しました: {e}")
        finally:
            # クリーンアップ
            if work_dir.exists():
                logger.step("作業ディレクトリをクリーンアップ中")
                try:
                    shutil.rmtree(work_dir)
                except Exception as e:
                    logger.warn(f"作業ディレクトリの削除に失敗しました: {e}")


# Module instance for convenient access
core_package_manager = CorePackageManager()

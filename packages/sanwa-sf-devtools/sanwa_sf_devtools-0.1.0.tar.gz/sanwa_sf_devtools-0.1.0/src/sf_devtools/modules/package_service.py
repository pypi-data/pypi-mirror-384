"""
Shared service for Salesforce package operations used by MES/Core managers.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.text import Text

from ..core.common import Logger, SalesforceCliError, config, logger, sf_cli, ui


class PackageService:
    """A shared service that wraps common sf CLI operations for packages."""

    def __init__(self) -> None:
        self.project_root: Path = config.project_root
        self.console = Console()

    # -----------------------------
    # Streaming runner
    # -----------------------------
    def _run_with_streaming(
        self, cmd: List[str], *, title: str, log_basename: str
    ) -> None:
        """Run a command with streaming output and a spinner indicator.

        Raises SalesforceCliError when command exits with non-zero code.
        """
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"{log_basename}_{datetime.now():%Y%m%d_%H%M%S}.log"

        Logger.step("実行コマンド:")
        print(" " + " ".join(cmd))

        import subprocess

        start = datetime.now()
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"=== {title} 開始: {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")
            lf.write(f"CMD: {' '.join(cmd)}\n\n")
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=self.project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                with Progress(
                    SpinnerColumn(style="bright_cyan"),
                    TextColumn(f"[bold cyan]{title}[/bold cyan]"),
                    TextColumn("[dim]| 出力: {task.fields[last_line]}"),
                    TimeElapsedColumn(),
                    transient=True,
                    console=self.console,
                ) as progress:
                    task = progress.add_task("run", total=None, last_line="起動中")
                    if proc.stdout is not None:
                        for raw in proc.stdout:
                            line = raw.rstrip("\n")
                            lf.write(raw)
                            try:
                                self.console.print(Text.from_ansi(line))
                            except Exception:
                                self.console.print(line)
                            progress.update(
                                task, last_line=(line[-80:] if line else "...")
                            )
                    rc = proc.wait()
            except KeyboardInterrupt:
                try:
                    proc.terminate()  # type: ignore[name-defined]
                except Exception:
                    pass
                try:
                    proc.wait(timeout=3)  # type: ignore[name-defined]
                except Exception:
                    try:
                        proc.kill()  # type: ignore[name-defined]
                    except Exception:
                        pass
                lf.write("\n[ユーザー中断]\n")
                rc = 130
            except Exception as e:
                lf.write(f"\n[例外] {e}\n")
                rc = 1
            finally:
                dur = int((datetime.now() - start).total_seconds())
                lf.write(("\n=== 完了 ===\n"))
                lf.write(f"終了コード: {rc}\n所要時間: {dur}秒\n")

        if rc != 0:
            raise SalesforceCliError(
                f"Command failed with code {rc}: {' '.join(cmd)} (log: {log_file})"
            )

    # -----------------------------
    # DevHub
    # -----------------------------
    def ensure_devhub(self) -> Optional[str]:
        """DevHub を確認し、必要ならログインを促して認証済みの識別子を返します。

        概要:
            1) `sf org list` のキャッシュから DevHub 候補を取得。単一なら返却、複数ならユーザーに選択させます。
            2) 候補がなければ 'prod' エイリアスを試し、未認証なら Web ログインを促します。

        Returns:
            Optional[str]: DevHub のエイリアスまたはユーザー名。失敗時は None。
        """
        try:
            sf_cli.load_org_cache()
            cache = getattr(sf_cli, "_org_cache", {}) or {}
            devhubs = (cache.get("result", {}) or {}).get(
                "devHubs", cache.get("devHubs", [])
            ) or []
            candidates: List[str] = []
            for org in devhubs:
                alias = org.get("alias")
                username = org.get("username")
                if alias or username:
                    candidates.append(alias or username)
            if candidates:
                if len(candidates) == 1:
                    logger.info(f"DevHub組織: {candidates[0]}")
                    return candidates[0]
                idx = ui.select_from_menu("DevHub組織を選択してください:", candidates)
                return candidates[idx]
        except Exception:
            pass

        # Fallback to 'prod'
        alias = "prod"
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

    # -----------------------------
    # List helpers
    # -----------------------------
    def list_packages(self) -> List[Dict]:
        """`sf package list --json` を実行し、パッケージ一覧を返します。

        Returns:
            List[Dict]: パッケージレコードの配列（失敗時は空配列）。
        """
        try:
            res = subprocess.run(
                ["sf", "package", "list", "--json"],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            data = json.loads(res.stdout or "{}")
            return data.get("result", []) or data.get("records", []) or []
        except Exception:
            return []

    def list_package_versions(self, package_selector: str) -> List[Dict]:
        """対象パッケージのバージョン一覧を JSON で返します。

        Args:
            package_selector: パッケージ名または ID。

        Returns:
            List[Dict]: バージョンレコードの配列（失敗時は空配列）。
        """
        try:
            res = subprocess.run(
                [
                    "sf",
                    "package",
                    "version",
                    "list",
                    "--packages",
                    package_selector,
                    "--json",
                ],
                cwd=self.project_root,
                text=True,
                capture_output=True,
                check=False,
            )
            data = json.loads(res.stdout or "{}")
            return data.get("result", []) or data.get("records", []) or []
        except Exception:
            return []

    # -----------------------------
    # CRUD
    # -----------------------------
    def create_package(
        self,
        name: str,
        path: str,
        *,
        unlocked: bool = True,
        org_dependent: bool = False,
        devhub: str,
    ) -> None:
        """`sf package create` でパッケージを作成します。

        Args:
            name: パッケージ名。
            path: プロジェクト内のパス。
            unlocked: Unlocked か Managed か。
            org_dependent: 組織依存パッケージとして作成するか。
            devhub: DevHub エイリアス/ユーザー名。
        """
        cmd: List[str] = [
            "sf",
            "package",
            "create",
            "--name",
            name,
            "--path",
            path,
            "--package-type",
            "Unlocked" if unlocked else "Managed",
            "--target-dev-hub",
            devhub,
        ]
        if org_dependent:
            cmd.append("--org-dependent")
        sf_cli.run_command(cmd, cwd=self.project_root, check=True)

    def create_package_version(
        self,
        package: str,
        wait_min: int,
        *,
        devhub: str,
        bypass_install_key: bool = True,
        verbose: bool = True,
    ) -> None:
        """`sf package version create` でパッケージバージョンを作成します。

        Args:
            package: パッケージ名または ID。
            wait_min: 待機時間（分）。
            devhub: DevHub エイリアス/ユーザー名。
            bypass_install_key: インストールキー入力をバイパスするか。
            verbose: 詳細ログを有効化するか。
        """
        cmd: List[str] = [
            "sf",
            "package",
            "version",
            "create",
            "--package",
            package,
            "--wait",
            str(wait_min),
            "--target-dev-hub",
            devhub,
        ]
        if bypass_install_key:
            cmd.insert(cmd.index("--wait"), "--installation-key-bypass")
        if verbose:
            cmd.append("--verbose")
        # 長時間実行になりやすいためストリーミング表示に変更
        self._run_with_streaming(
            cmd,
            title=f"パッケージバージョン作成中 ({package})",
            log_basename="package_version_create",
        )

    def delete_package(
        self, package_id: str, *, devhub: str, no_prompt: bool = True
    ) -> None:
        """`sf package delete` でパッケージを削除します。

        Args:
            package_id: 削除対象のパッケージID。
            devhub: DevHub エイリアス/ユーザー名。
            no_prompt: 削除確認のプロンプトをスキップするか。
        """
        cmd = [
            "sf",
            "package",
            "delete",
            "--package",
            package_id,
            "--target-dev-hub",
            devhub,
        ]
        if no_prompt:
            cmd.append("--no-prompt")
        sf_cli.run_command(cmd, cwd=self.project_root, check=True)

    def delete_package_version(
        self, version_id_04t: str, *, devhub: str, no_prompt: bool = True
    ) -> None:
        """`sf package version delete` でパッケージバージョンを削除します。

        Args:
            version_id_04t: 04t で始まる SubscriberPackageVersionId。
            devhub: DevHub エイリアス/ユーザー名。
            no_prompt: 削除確認のプロンプトをスキップするか。
        """
        cmd = [
            "sf",
            "package",
            "version",
            "delete",
            "--package",
            version_id_04t,
            "--target-dev-hub",
            devhub,
        ]
        if no_prompt:
            cmd.append("--no-prompt")
        sf_cli.run_command(cmd, cwd=self.project_root, check=True)

    # -----------------------------
    # Metadata retrieve/convert/sync
    # -----------------------------
    def retrieve_convert_sync(
        self, manifest_file: str, source_org: str, target_dir: str
    ) -> None:
        """メタデータを取得→変換→同期します（作業ディレクトリ一時作成）。

        手順:
            1. `sf project retrieve start` で mdapi を取得
            2. `sf project convert mdapi` でソース形式へ変換
            3. `rsync` で target_dir に同期し、必要に応じて Prettier で整形

        Args:
            manifest_file: 取得に用いる package.xml のパス。
            source_org: 取得元組織のエイリアス/ユーザー名。
            target_dir: 同期先のパス（プロジェクト相対）。
        """
        work_dir = (
            self.project_root
            / f"temp-retrieve-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            self._run_with_streaming(
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
                log_basename="retrieve",
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
            self._run_with_streaming(
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
                log_basename="convert_mdapi",
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
            # rsync 出力は多いためストリーミングで表示
            self._run_with_streaming(
                rsync_cmd, title=f"rsync 同期中 → {target_dir}", log_basename="rsync"
            )
            logger.success(f"メタデータの更新が完了しました: {target_dir}")
            # Optional: summary
            try:
                file_count = sum(1 for _ in target_path.rglob("*") if _.is_file())
                logger.info(f"更新されたファイル数: {file_count}")
            except Exception:
                pass
            self.format_with_prettier(str(target_path))
        except subprocess.CalledProcessError:
            logger.error("rsync による同期に失敗しました")
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        finally:
            logger.step("作業ディレクトリのクリーンアップ")
            shutil.rmtree(work_dir, ignore_errors=True)

    def format_with_prettier(self, target_dir: str) -> None:
        """Prettier が使用可能であれば、XML/JS/CSS を整形します。

        Args:
            target_dir: 整形対象ルートディレクトリ。
        """
        if shutil.which("npx") is None:
            logger.warn("npx/Prettierが利用できません（スキップします）")
            return
        try:
            subprocess.run(
                ["npx", "prettier", "--write", f"{target_dir}/**/*.xml"],
                cwd=self.project_root,
                check=False,
                text=True,
            )
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

    # -----------------------------
    # Deploy (dry run)
    # -----------------------------
    def deploy_dry_run_by_manifest(
        self,
        manifest_file: str,
        target_org: str,
        test_level: str,
        specified_tests: str = "",
    ) -> None:
        """`sf project deploy start --manifest` を Dry Run で実行します。

        Args:
            manifest_file: 使用するマニフェストファイル。
            target_org: 実行先の組織（エイリアス/ユーザー名）。
            test_level: テストレベル。
            specified_tests: RunSpecifiedTests の場合のテスト名（カンマ区切り）。
        """
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
        self._run_with_streaming(
            cmd, title="デプロイ確認 (manifest)", log_basename="deploy_dryrun_manifest"
        )

    def deploy_dry_run_by_source_dir(self, source_dir: str, target_org: str) -> None:
        """`sf project deploy start --source-dir` を Dry Run で実行します。

        Args:
            source_dir: デプロイ対象のソースディレクトリ。
            target_org: 実行先の組織（エイリアス/ユーザー名）。
        """
        cmd = [
            "sf",
            "project",
            "deploy",
            "start",
            "--source-dir",
            source_dir,
            "--target-org",
            target_org,
            "--dry-run",
            "--verbose",
        ]
        self._run_with_streaming(
            cmd, title="デプロイ確認 (source-dir)", log_basename="deploy_dryrun_srcdir"
        )

"""
SFDMU data synchronization functionality.
Rich UI port of scripts/mes-dev-cli/modules/sfdmu_sync.sh
"""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.box import DOUBLE, ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from ..core.common import (
    Logger,
    SalesforceCliError,
    config,
    logger,
    sf_cli,
    ui,
)


class SfdmuSyncManager:
    """SFDMU data synchronization with Rich UI."""

    def __init__(self) -> None:
        self.console = Console()
        self.project_root: Path = config.project_root
        self.config_file: Path = self.project_root / "sfdmu" / "sync_profiles.json"
        self.history_file: Path = self.project_root / "logs" / "sfdmu_history.json"

    # =========================
    # Main menu
    # =========================
    def show_menu(self) -> None:
        while True:
            self._show_header()
            options = [
                "定義済み同期プロファイルの表示",
                "同期プロファイルの実行",
                "同期履歴の確認",
                "戻る",
            ]
            try:
                choice = ui.select_from_menu("実行する操作を選択してください:", options)
            except Exception:
                return

            if choice == 0:
                self._show_sync_profiles()
            elif choice == 1:
                self._execute_sync_profile()
            elif choice == 2:
                self._show_sync_history()
            else:
                return

            if not ui.confirm("SFDMU データ同期を続けますか？", default=True):
                return

    # =========================
    # Views
    # =========================
    def _show_header(self) -> None:
        panel = Panel(
            Text.assemble(("🔄 ", "bold green"), ("SFDMU Data Sync", "bold cyan")),
            title="[bold bright_blue]SFDMU データ同期[/bold bright_blue]",
            border_style="bright_blue",
            box=DOUBLE,
            width=90,
        )
        self.console.print(panel)
        self.console.print(Rule(style="bright_blue"))

    def _show_sync_profiles(self) -> None:
        logger.step("定義済み同期プロファイルの表示")
        if not self.config_file.exists():
            logger.error(
                f"同期プロファイル設定ファイルが見つかりません: {self.config_file}"
            )
            return

        try:
            profiles = self._load_profiles()
        except Exception as e:
            logger.error(f"同期プロファイルの読み込みに失敗しました: {e}")
            return

        if not profiles:
            logger.warn("同期プロファイルが未定義です")
            return

        # Summary table
        table = Table(
            title="[bold bright_cyan]利用可能な同期プロファイル[/bold bright_cyan]",
            header_style="bold bright_blue",
            box=ROUNDED,
            width=110,
        )
        table.add_column("#", justify="center", style="bold yellow", width=3)
        table.add_column("ID", style="white", width=12)
        table.add_column("名前", style="white", width=28)
        table.add_column("ソース→ターゲット", style="cyan", width=30)
        table.add_column("有効", justify="center", width=6)
        table.add_column("パス", style="dim")

        for i, p in enumerate(profiles):
            src = p.get("sourceAlias") or "未指定"
            tgt = p.get("targetAlias") or "未指定"
            table.add_row(
                str(i),
                p.get("id", ""),
                p.get("name", ""),
                f"{src} → {tgt}",
                "✅" if p.get("enabled", True) else "❌",
                p.get("path", ""),
            )
        self.console.print(table)
        self.console.print()

        # ここでは一覧のみ表示します（詳細閲覧機能は廃止）。

    def _execute_sync_profile(self) -> None:
        logger.step("同期プロファイルの実行")
        if not self.config_file.exists():
            logger.error(
                f"同期プロファイル設定ファイルが見つかりません: {self.config_file}"
            )
            return

        try:
            profiles = [p for p in self._load_profiles() if p.get("enabled", True)]
        except Exception as e:
            logger.error(f"同期プロファイルの読み込みに失敗しました: {e}")
            return

        if not profiles:
            logger.warn("有効な同期プロファイルが見つかりません")
            return

        options = []
        for p in profiles:
            src = p.get("sourceAlias") or "未指定"
            tgt = p.get("targetAlias") or "未指定"
            options.append(f"{p.get('name')} ({src} → {tgt})")
        options.append("キャンセル")

        try:
            idx = ui.select_from_menu(
                "実行する同期プロファイルを選択してください:", options
            )
        except Exception:
            return
        if idx == len(options) - 1:
            return
        self._execute_sfdmu_sync(profiles[idx])

    # =========================
    # Core execution
    # =========================
    def _execute_sfdmu_sync(self, profile: Dict[str, Any]) -> None:
        profile_id = profile.get("id", "")
        name = profile.get("name", profile_id)
        path_str = profile.get("path", "")
        verbose = profile.get("verbose", True)
        src_token = profile.get("sourceAlias")
        tgt_token = profile.get("targetAlias")

        # Resolve source/target usernames
        if src_token:
            src_username = sf_cli.alias_to_username(src_token) or ""
            if not src_username:
                logger.error(
                    f"ソース組織のエイリアスを解決できませんでした: {src_token}"
                )
                logger.info(
                    f"sf org login --alias {src_token} でエイリアスを登録してください"
                )
                return
        else:
            src_username = (
                ui.select_org(
                    "ソース組織の選択", include_scratch=False, return_type="username"
                )
                or ""
            )
            if not src_username:
                logger.error("ソース組織が選択されませんでした")
                return

        if tgt_token:
            tgt_username = sf_cli.alias_to_username(tgt_token) or ""
            if not tgt_username:
                logger.error(
                    f"ターゲット組織のエイリアスを解決できませんでした: {tgt_token}"
                )
                logger.info(
                    f"sf org login --alias {tgt_token} でエイリアスを登録してください"
                )
                return
        else:
            tgt_username = (
                ui.select_org(
                    "ターゲット組織の選択",
                    include_scratch=False,
                    return_type="username",
                )
                or ""
            )
            if not tgt_username:
                logger.error("ターゲット組織が選択されませんでした")
                return

        # Confirm
        info = Panel(
            Text.assemble(
                ("プロファイル: ", "bold white"),
                (f"{name}\n", "green"),
                ("パス: ", "bold white"),
                (f"{path_str}\n", "cyan"),
                ("ソース: ", "bold white"),
                (f"{src_username}\n", "white"),
                ("ターゲット: ", "bold white"),
                (f"{tgt_username}", "white"),
            ),
            title="[bold bright_cyan]同期実行確認[/bold bright_cyan]",
            border_style="bright_cyan",
            box=ROUNDED,
            width=90,
        )
        self.console.print(info)
        if not ui.confirm("この設定で同期を実行しますか？", default=False):
            logger.info("同期がキャンセルされました")
            return

        # Pre-checks
        if not self._check_sfdmu_prerequisites(path_str, src_username, tgt_username):
            return

        # Build command
        full_path = str((self.project_root / path_str).resolve())
        cmd = [
            "sf",
            "sfdmu",
            "run",
            "--path",
            full_path,
            "--sourceusername",
            src_username,
            "--targetusername",
            tgt_username,
        ]
        if verbose:
            cmd.append("--verbose")

        # Prepare log file
        log_dir = self.project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"sfdmu_{datetime.now():%Y%m%d_%H%M%S}_{profile_id}.log"

        logger.info(f"SFDMUコマンド実行: {' '.join(cmd)}")
        start = time.time()
        success = False
        duration = 0

        # 出力ストリーミングとインジケータ（スピナー＋経過時間）
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write(f"=== SFDMU同期開始: {datetime.now():%Y-%m-%d %H:%M:%S} ===\n")
            lf.write(f"プロファイル: {profile_id} ({name})\n")
            lf.write(f"コマンド: {' '.join(cmd)}\n\n")

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

                # 画面に出力を流しつつ、進行中を示すスピナーを表示
                with Progress(
                    SpinnerColumn(style="bright_cyan"),
                    TextColumn("[bold cyan]SFDMU 実行中...[/bold cyan]"),
                    TextColumn("[dim]| 出力: {task.fields[last_line]}"),
                    TimeElapsedColumn(),
                    transient=True,
                    console=self.console,
                ) as progress:
                    task = progress.add_task("run", total=None, last_line="起動中")

                    if proc.stdout is not None:
                        for raw in proc.stdout:
                            line = raw.rstrip("\n")
                            # ログへ書き込み
                            lf.write(raw)
                            # 画面へ逐次表示（ANSIカラー保持）
                            try:
                                self.console.print(Text.from_ansi(line))
                            except Exception:
                                self.console.print(line)
                            # スピナーの説明を更新（長すぎる場合は切り詰め）
                            progress.update(
                                task, last_line=(line[-80:] if line else "...")
                            )

                    returncode = proc.wait()
                    success = returncode == 0

            except KeyboardInterrupt:
                # 中断時はプロセスを停止
                try:
                    proc.terminate()  # type: ignore[name-defined]
                except Exception:
                    pass
                try:
                    # 速やかに停止しない場合は kill
                    proc.wait(timeout=3)  # type: ignore[name-defined]
                except Exception:
                    try:
                        proc.kill()  # type: ignore[name-defined]
                    except Exception:
                        pass
                lf.write("\n[ユーザー中断]\n")
                success = False
            except Exception as e:
                lf.write(f"\n実行時例外: {e}\n")
                success = False
            finally:
                end = time.time()
                duration = int(end - start)
                lf.write("\n")
                lf.write(
                    ("=== SFDMU同期完了: " if success else "=== SFDMU同期エラー: ")
                    + f"{datetime.now() :%Y-%m-%d %H:%M:%S} ===\n"
                )
                lf.write(f"実行時間: {duration}秒\n")

        # 完了サマリ
        if success:
            logger.success("SFDMU同期が完了しました")
            logger.info(f"実行時間: {duration}秒")
            logger.info(f"ログファイル: {log_file}")
            self._record_sync_history(
                profile_id, name, "success", duration, str(log_file)
            )
        else:
            logger.error("SFDMU同期でエラーが発生しました")
            logger.info(f"ログファイル: {log_file}")
            self._record_sync_history(
                profile_id, name, "error", duration, str(log_file)
            )

    # =========================
    # Prerequisites & helpers
    # =========================
    def _check_sfdmu_prerequisites(
        self, path: str, src_username: str, tgt_username: str
    ) -> bool:
        logger.step("SFDMU実行前チェック")
        errors: List[str] = []

        # Load org cache early
        try:
            sf_cli.load_org_cache()
        except Exception:
            errors.append("組織情報の取得に失敗しました")

        # Check SFDMU plugin installed
        try:
            res = subprocess.run(
                ["sf", "plugins", "--core", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            plugins = json.loads(res.stdout or "[]")
            found = False
            # The output may be a list or an object with a 'plugins' key depending on CLI version
            items = plugins if isinstance(plugins, list) else plugins.get("plugins", [])
            for p in items:
                name = (p.get("name") or p.get("id") or "").lower()
                if name == "sfdmu" or "sfdmu" in name:
                    found = True
                    break
            if not found:
                errors.append("SFDMUプラグインがインストールされていません")
        except Exception:
            errors.append("SFDMUプラグインの確認に失敗しました")

        # Path checks
        full_path = self.project_root / path
        if not full_path.is_dir():
            errors.append(f"SFDMUパスが存在しません: {full_path}")
        elif not (full_path / "export.json").is_file():
            errors.append(f"export.jsonが見つかりません: {full_path / 'export.json'}")

        # Org presence checks (warn-only if not present)
        all_orgs = {
            u for (u, _a, _s) in [(o[0], o[1], o[2]) for o in sf_cli.get_all_orgs()]
        }
        if src_username and src_username not in all_orgs:
            logger.warn(f"ソース組織が認証されていない可能性があります: {src_username}")
        if tgt_username and tgt_username not in all_orgs:
            logger.warn(
                f"ターゲット組織が認証されていない可能性があります: {tgt_username}"
            )

        if errors:
            logger.error("前提条件エラー:")
            for e in errors:
                print(f"  - {e}")
            return False

        logger.success("前提条件チェック完了")
        return True

    def _record_sync_history(
        self,
        profile_id: str,
        profile_name: str,
        status: str,
        duration: int,
        log_file: str,
    ) -> None:
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self.history_file.write_text(
                json.dumps({"history": []}, ensure_ascii=False), encoding="utf-8"
            )

        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8") or "{}")
        except Exception:
            data = {"history": []}

        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "profileId": profile_id,
            "profileName": profile_name,
            "status": status,
            "duration": int(duration),
            "logFile": log_file,
        }
        hist = data.get("history", [])
        hist.append(entry)
        data["history"] = hist
        self.history_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _show_sync_history(self) -> None:
        logger.step("同期履歴の確認")
        if not self.history_file.exists():
            logger.info("同期履歴が見つかりません")
            return
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
        except Exception:
            logger.error("履歴ファイルの読み込みに失敗しました")
            return
        history = data.get("history", [])
        if not history:
            logger.info("同期履歴はありません")
            return

        # Sort by timestamp desc
        def key_ts(x: Dict[str, Any]) -> str:
            v = x.get("timestamp")
            return v if isinstance(v, str) else ""

        items = sorted(history, key=key_ts, reverse=True)[:10]

        table = Table(
            title="[bold]同期履歴 (最新10件)[/bold]",
            header_style="bold",
            box=ROUNDED,
            width=110,
        )
        table.add_column("#", justify="center", width=3, style="bold yellow")
        table.add_column("日時", style="white", width=20)
        table.add_column("プロファイル", style="white", width=30)
        table.add_column("ステータス", justify="center", width=10)
        table.add_column("時間(秒)", justify="right", width=10)
        table.add_column("ログ", style="dim")
        for i, h in enumerate(items):
            table.add_row(
                str(i),
                h.get("timestamp", ""),
                h.get("profileName", ""),
                ("✅" if h.get("status") == "success" else "❌"),
                str(h.get("duration", "")),
                h.get("logFile", ""),
            )
        self.console.print(table)
        self.console.print()

        # Next actions
        options = ["詳細履歴の表示", "ログファイルの確認", "履歴のクリア", "戻る"]
        try:
            idx = ui.select_from_menu("実行する操作を選択してください:", options)
        except Exception:
            return
        if idx == 0:
            self._show_detailed_history(history)
        elif idx == 1:
            self._show_log_files(items)
        elif idx == 2:
            self._clear_sync_history()

    def _show_detailed_history(self, history: List[Dict[str, Any]]) -> None:
        items = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
        text = json.dumps(items, ensure_ascii=False, indent=2)
        self.console.print(
            Panel.fit(text, title="詳細同期履歴", border_style="cyan", box=ROUNDED)
        )

    def _show_log_files(self, recent_items: List[Dict[str, Any]]) -> None:
        options = []
        paths: List[str] = []
        for h in recent_items:
            title = f"{h.get('timestamp')}: {h.get('profileName')} - {h.get('logFile')}"
            options.append(title)
            paths.append(h.get("logFile", ""))
        options.append("戻る")
        try:
            idx = ui.select_from_menu(
                "確認するログファイルを選択してください:", options
            )
        except Exception:
            return
        if idx == len(options) - 1:
            return
        selected = paths[idx]
        p = Path(selected)
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"ログファイルの読み込みに失敗しました: {e}")
                return
            self.console.print(
                Panel.fit(
                    content,
                    title=f"ログ内容: {p.name}",
                    border_style="white",
                    box=ROUNDED,
                )
            )
        else:
            logger.error(f"ログファイルが見つかりません: {selected}")

    def _clear_sync_history(self) -> None:
        if ui.confirm("同期履歴をすべてクリアしますか？", default=False):
            try:
                self.history_file.parent.mkdir(parents=True, exist_ok=True)
                self.history_file.write_text(
                    json.dumps({"history": []}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.success("同期履歴をクリアしました")
            except Exception as e:
                logger.error(f"履歴のクリアに失敗しました: {e}")

    # =========================
    # Data loading
    # =========================
    def _load_profiles(self) -> List[Dict[str, Any]]:
        data = json.loads(self.config_file.read_text(encoding="utf-8"))
        profiles_raw = data.get("profiles", [])
        # 正しい型に絞り込む（型安全）
        if not isinstance(profiles_raw, list):
            return []
        typed: List[Dict[str, Any]] = []
        for p in profiles_raw:
            if isinstance(p, dict):
                typed.append(p)
        # Keep order as-is
        return typed


# Module instance for convenient access
sfdmu_sync_manager = SfdmuSyncManager()

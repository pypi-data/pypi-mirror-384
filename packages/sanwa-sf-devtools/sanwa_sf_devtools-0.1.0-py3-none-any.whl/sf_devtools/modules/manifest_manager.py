"""
Manifest (Package.xml) management functionality.
Rich UI port of scripts/mes-dev-cli/modules/manifest_manager.sh
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from ..core.common import (
    Logger,
    SalesforceCli,
    SalesforceCliError,
    UserInterface,
    config,
    logger,
    sf_cli,
    ui,
)


class ManifestManager:
    """Manifest (Package.xml) management functionality."""

    def __init__(self) -> None:
        self.console = Console()
        self.project_root: Path = config.project_root
        self.manifest_dir: Path = self.project_root / "manifest"
        self.package_xml: Path = self.manifest_dir / "package.xml"
        self.core_xml: Path = self.manifest_dir / "core.xml"
        self.mes_xml: Path = self.manifest_dir / "mes.xml"

    def show_menu(self) -> None:
        """Show manifest management menu (ported from shell)."""
        while True:
            logger.info("Package.xml管理")

            options = [
                "Package.xml → core.xml / mes.xml コピー",
                "core.xml / mes.xml → Package.xml 戻し",
                "戻る",
            ]

            try:
                choice = ui.select_from_menu("操作を選択してください:", options)

                if choice == 0:
                    self._copy_from_generator()
                elif choice == 1:
                    self._copy_to_generator()
                elif choice == 2:
                    return

                # 操作完了後、続行確認
                if not ui.confirm("マニフェスト管理を続けますか？", default=True):
                    return

            except Exception as e:
                logger.error(f"操作中にエラーが発生しました: {e}")
                if not ui.confirm("マニフェスト管理を続けますか？", default=True):
                    return

    # ========================================
    # Package.xml Generator連携機能
    # ========================================
    def _copy_from_generator(self) -> None:
        """Package.xml → core.xml / mes.xml コピー"""
        logger.step("Package.xml → core.xml / mes.xml コピー")

        # package.xmlの存在確認
        if not self.package_xml.is_file():
            logger.error(f"package.xml が見つかりません: {self.package_xml}")
            logger.info("Package.xml Generator を使用してpackage.xmlを生成してください")
            return

        # package.xmlの内容プレビュー
        self._preview_file(self.package_xml, title="package.xml の内容")

        # コピー先の選択
        options = [
            "core.xml (基盤メタデータ)",
            "mes.xml (MESパッケージメタデータ)",
            "両方",
            "キャンセル",
        ]

        try:
            idx = ui.select_from_menu("コピー先を選択:", options)
        except Exception:
            return
        if idx == 3:
            return

        if idx == 0:
            if self._confirm_copy_operation(
                self.package_xml, self.core_xml, "core.xml"
            ):
                self._copy_manifest_file(self.package_xml, self.core_xml, "core.xml")
        elif idx == 1:
            if self._confirm_copy_operation(self.package_xml, self.mes_xml, "mes.xml"):
                self._copy_manifest_file(self.package_xml, self.mes_xml, "mes.xml")
        elif idx == 2:
            if self._confirm_copy_operation(
                self.package_xml, self.core_xml, "core.xml"
            ):
                self._copy_manifest_file(self.package_xml, self.core_xml, "core.xml")
                if self._confirm_copy_operation(
                    self.package_xml, self.mes_xml, "mes.xml"
                ):
                    self._copy_manifest_file(self.package_xml, self.mes_xml, "mes.xml")

    def _copy_to_generator(self) -> None:
        """core.xml / mes.xml → Package.xml Generator 戻し"""
        logger.step("core.xml / mes.xml → Package.xml Generator 戻し")

        # ソースファイルの選択
        options = ["core.xml", "mes.xml", "キャンセル"]
        try:
            idx = ui.select_from_menu("戻し元ファイルを選択:", options)
        except Exception:
            return
        if idx == 2:
            return

        source_file = self.core_xml if idx == 0 else self.mes_xml

        if not source_file.is_file():
            logger.error(f"ソースファイルが見つかりません: {source_file}")
            return

        # package.xmlが存在する場合の確認とバックアップ
        if self.package_xml.is_file():
            logger.warn("package.xml が既に存在します")
            if not ui.confirm("上書きしますか？", default=False):
                logger.info("操作をキャンセルしました")
                return

            backup_file = self._backup_file(self.package_xml)
            logger.info(f"バックアップを作成しました: {backup_file.name}")

        if self._confirm_copy_operation(source_file, self.package_xml, "package.xml"):
            self._copy_manifest_file(source_file, self.package_xml, "package.xml")
            logger.success("Package.xml Generator で編集可能になりました")
            logger.info("編集後は再度 core.xml または mes.xml にコピーしてください")
        else:
            logger.info("操作をキャンセルしました")

    # ========================================
    # ヘルパー関数
    # ========================================
    def _confirm_copy_operation(
        self, source: Path, target: Path, target_name: str
    ) -> bool:
        """コピー操作の最終確認とソース情報提示。"""
        logger.step("コピー操作の確認")

        # ソースファイルの情報表示
        self._preview_file(source, title=f"コピー元ファイル: {source.name}")

        logger.info(f"コピー先: {target_name}")

        # 既存ファイルがある場合の警告
        if target.is_file():
            logger.warn(f"⚠️  既存の {target_name} が上書きされます")
            self._show_file_quick_info(target, title="既存ファイル情報")

        # 重要な警告
        self.console.print(
            Panel.fit(
                Text(
                    "この操作によりファイルが変更されます。バックアップは自動作成されますが、慎重に確認してください。"
                ),
                title="🔥 重要な警告",
                border_style="red",
                box=ROUNDED,
            )
        )

        return ui.confirm(
            f"本当に {target_name} にコピーしてもよろしいですか？", default=False
        )

    def _copy_manifest_file(self, source: Path, target: Path, target_name: str) -> bool:
        """既存ファイルのバックアップを取りつつコピーを実行。スピナーで進行表示。"""
        # 既存のターゲットがあればバックアップ
        backup_made: Optional[Path] = None
        if target.is_file():
            backup_made = self._backup_file(target)
            logger.info(f"✅ バックアップ作成: {backup_made.name}")

        # コピー実行（スピナー）
        with Progress(
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[bold cyan]コピー実行中...[/bold cyan]"),
            TextColumn("[dim]| 状況: {task.fields[last_line]}"),
            TimeElapsedColumn(),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task("copy", total=None, last_line="準備中")

            try:
                progress.update(task, last_line="コピー中")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(source), str(target))
                progress.update(task, last_line="整合性確認中")
                # 簡易検証（サイズと行数）
                if target.stat().st_size <= 0:
                    raise RuntimeError("コピー結果ファイルサイズが0です")
            except Exception as e:
                logger.error(f"❌ コピーに失敗しました: {e}")
                return False

        # 結果表示
        logger.success(f"✅ コピー完了: {source.name} → {target_name}")
        self._show_copy_result(target)
        self.console.print(f"ファイルパス: {target}")
        return True

    def _backup_file(self, path: Path) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = Path(str(path) + f".backup.{ts}")
        backup.write_bytes(path.read_bytes())
        return backup

    def _show_copy_result(self, target: Path) -> None:
        try:
            line_count = sum(
                1 for _ in target.open("r", encoding="utf-8", errors="ignore")
            )
        except Exception:
            line_count = 0
        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
            meta_types = content.count("<name>")
        except Exception:
            meta_types = 0

        table = Table(title="結果確認", box=ROUNDED)
        table.add_column("項目", style="bold")
        table.add_column("値")
        table.add_row("ファイル行数", str(line_count))
        table.add_row("メタデータタイプ数(推定)", str(meta_types))
        self.console.print(table)

    def _show_file_quick_info(self, file: Path, title: str = "ファイル情報") -> None:
        size = file.stat().st_size if file.exists() else 0
        try:
            line_count = sum(
                1 for _ in file.open("r", encoding="utf-8", errors="ignore")
            )
        except Exception:
            line_count = 0
        panel = Panel.fit(
            Text.assemble(
                ("ファイル: ", "bold"),
                (f"{file.name}\n"),
                ("サイズ: ", "bold"),
                (f"{size} bytes\n"),
                ("行数: ", "bold"),
                (f"{line_count}\n"),
            ),
            title=title,
            border_style="cyan",
            box=ROUNDED,
        )
        self.console.print(panel)

    def _preview_file(self, file: Path, title: str = "ファイルプレビュー") -> None:
        if not file.is_file():
            logger.error(f"ファイルが見つかりません: {file}")
            return

        # 概要
        self._show_file_quick_info(file, title=f"{title} - 概要")

        # 先頭10行
        try:
            head_lines = []
            with file.open("r", encoding="utf-8", errors="ignore") as f:
                for i in range(10):
                    line = f.readline()
                    if not line:
                        break
                    head_lines.append(line.rstrip("\n"))
        except Exception:
            head_lines = []

        # 総行数を数えつつ末尾5行
        tail_lines = []
        try:
            with file.open("r", encoding="utf-8", errors="ignore") as f:
                buffer = []
                for line in f:
                    buffer.append(line.rstrip("\n"))
                    if len(buffer) > 5:
                        buffer.pop(0)
                tail_lines = buffer
        except Exception:
            tail_lines = []

        # 表示
        head_panel = Panel.fit(
            "\n".join([f"    {l}" for l in head_lines]) or "(empty)",
            title="ファイル内容プレビュー（先頭10行）",
            border_style="green",
            box=ROUNDED,
        )
        if len(head_lines) >= 10:
            self.console.print(head_panel)
            self.console.print("    ...")
        else:
            self.console.print(head_panel)
        tail_panel = Panel.fit(
            "\n".join([f"    {l}" for l in tail_lines]) or "(empty)",
            title="ファイル内容プレビュー（末尾5行）",
            border_style="green",
            box=ROUNDED,
        )
        self.console.print(tail_panel)


# Module instance for convenient access
manifest_manager = ManifestManager()

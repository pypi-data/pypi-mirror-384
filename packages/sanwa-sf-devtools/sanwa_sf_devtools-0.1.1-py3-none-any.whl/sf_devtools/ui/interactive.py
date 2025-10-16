"""
Enhanced interactive user interface for SF DevTools.
Integration with all migrated modules from shell scripts.
"""

import sys
from typing import Any, Dict, List, Optional

import typer
from rich.align import Align
from rich.box import DOUBLE, HEAVY, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .. import __version__
from ..core.common import check_prerequisites, logger, ui
from ..modules.core_package import CorePackageManager

# 各モジュールのインポート
from ..modules.manifest_manager import ManifestManager
from ..modules.mes_package import MesPackageManager
from ..modules.package_deploy import PackageDeployManager
from ..modules.sfdmu_sync import SfdmuSyncManager
from .help_views import show_help, show_version

console = Console()


class InteractiveUI:
    """Enhanced interactive user interface class."""

    def __init__(self) -> None:
        self.running = True

    def show_banner(self) -> None:
        """Show welcome banner with rich formatting."""
        console.clear()

        # メインタイトル
        title_text = Text()
        title_text.append("🚀 ", style="bold yellow")
        title_text.append("Salesforce", style="bold blue")
        title_text.append(" 開発用 CLI", style="bold cyan")

        # サブタイトル
        subtitle_text = Text()
        subtitle_text.append(f"バージョン: ", style="dim")
        subtitle_text.append(f"{__version__}", style="bold green")
        subtitle_text.append(" | ", style="dim")
        subtitle_text.append("Python版", style="bold magenta")

        # 説明文
        description = Text(
            "Salesforce 開発を効率化する対話型CLI", style="italic bright_white"
        )

        # 操作説明
        controls = Text()
        controls.append("💡 ", style="yellow")
        controls.append("対話型メニューで簡単に操作 | ", style="green")
        controls.append("⌨️ ", style="cyan")
        controls.append("Ctrl+C で終了", style="red")

        # パネルの作成
        banner_content = Align.center(
            "\n".join(
                [
                    title_text.plain,
                    "",
                    subtitle_text.plain,
                    "",
                    description.plain,
                    "",
                    controls.plain,
                ]
            )
        )

        # 豪華なパネルで表示
        banner_panel = Panel(
            Align.center(
                Text.assemble(
                    ("☁️  "),
                    ("Salesforce", "bold blue"),
                    (" 開発用 CLI", "bold cyan"),
                    (" | ", "dim"),
                    ("バージョン: ", "dim"),
                    (f"{__version__}", "bold green"),
                    "\n\n",
                    ("Salesforce 開発を効率化する対話型CLI", "italic bright_white"),
                    "\n\n",
                    ("⌨️  ", "cyan"),
                    ("Ctrl+C で終了", "red"),
                )
            ),
            title="[bold bright_blue]✨ SF DevTools へようこそ ✨[/bold bright_blue]",
            border_style="bright_blue",
            box=DOUBLE,
            padding=(1, 2),
            width=80,
        )

        console.print(banner_panel)
        console.print()

        # 装飾的な区切り線
        console.print(
            Rule(
                "[bold bright_blue]🎯 メインメニュー[/bold bright_blue]",
                style="bright_blue",
            )
        )
        console.print()

    def show_main_menu(self) -> int:
        """Show main menu with rich table formatting."""

        # メニューオプションの定義
        menu_items = [
            {
                "icon": "📦",
                "name": "Manifest(Package.xml)管理",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "マニフェストファイルの作成・編集・統合",
            },
            {
                "icon": "🏗️",
                "name": "Core パッケージ管理",
                "status": "✅ 利用可能",
                "status_style": "bold yellow",
                "description": "ベースとなるCoreパッケージの作成・管理",
            },
            {
                "icon": "⚙️",
                "name": "MES パッケージ管理",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "MESパッケージの作成・バージョン管理",
            },
            {
                "icon": "🚀",
                "name": "パッケージテスト・デプロイ",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "パッケージのテスト・デプロイメント",
            },
            {
                "icon": "🌍",
                "name": "スクラッチ組織管理",
                "status": "🚧 工事中",
                "status_style": "bold yellow",
                "description": "開発用スクラッチ組織の作成・管理",
            },
            {
                "icon": "🔄",
                "name": "SFDMU データ同期",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "SFDMUプラグインを使用したデータ同期",
            },
            {
                "icon": "⚙️",
                "name": "設定・環境確認",
                "status": "🚧 工事中",
                "status_style": "bold yellow",
                "description": "開発環境の設定と確認",
            },
            {
                "icon": "📚",
                "name": "ヘルプ・ドキュメント",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "ヘルプ情報とドキュメントの表示",
            },
            {
                "icon": "🚪",
                "name": "終了",
                "status": "✅ 利用可能",
                "status_style": "bold green",
                "description": "アプリケーションを終了",
            },
        ]

        # テーブルの作成
        table = Table(
            title="[bold bright_cyan]📋 機能メニュー[/bold bright_cyan]",
            show_header=True,
            header_style="bold bright_blue",
            border_style="bright_blue",
            box=ROUNDED,
            padding=(0, 1),
            width=100,
        )

        table.add_column("#", style="bold bright_yellow", width=3, justify="center")
        table.add_column("機能", style="bold white", width=35)
        table.add_column("ステータス", width=15, justify="center")
        table.add_column("説明", style="dim", width=40)

        # テーブル行の追加
        for i, item in enumerate(menu_items):
            table.add_row(
                f"{i}",
                f"{item['icon']} {item['name']}",
                f"[{item['status_style']}]{item['status']}[/{item['status_style']}]",
                item["description"],
            )

        console.print(table)
        console.print()

        # 選択用のオプションリスト（従来のinquirer用）
        options = [
            f"{i}️⃣  {item['icon']} {item['name']}" for i, item in enumerate(menu_items)
        ]

        try:
            choice = ui.select_from_menu("🎯 実行する操作を選択してください:", options)
            return choice
        except (KeyboardInterrupt, EOFError):
            return 8  # 終了

    def run(self) -> None:
        """Main loop execution."""
        # Show banner
        self.show_banner()

        # Check prerequisites
        try:
            if not check_prerequisites(interactive=True, raise_on_error=True):
                return
        except typer.Exit:
            return

        # Main menu loop
        while self.running:
            try:
                choice = self.show_main_menu()
                if choice == 0:  # Manifest(Package.xml)管理
                    manifestManager = ManifestManager()
                    manifestManager.show_menu()

                if choice == 1:  # Core パッケージ管理
                    core_package_manager = CorePackageManager()
                    core_package_manager.show_menu()

                elif choice == 2:  # MES パッケージ管理
                    mes_package_manager = MesPackageManager()
                    mes_package_manager.show_menu()

                elif choice == 3:  # パッケージテスト・デプロイ
                    deploy_manager = PackageDeployManager()
                    deploy_manager.show_menu()

                elif choice == 4:  # スクラッチ組織管理
                    self._show_under_construction(
                        "🌍 スクラッチ組織管理", "開発用スクラッチ組織の作成・管理機能"
                    )
                elif choice == 5:  # SFDMU データ同期
                    sfdmu_manager = SfdmuSyncManager()
                    sfdmu_manager.show_menu()
                elif choice == 6:  # 設定・環境確認
                    self._show_under_construction(
                        "⚙️ 設定・環境確認", "開発環境の設定と確認機能"
                    )
                elif choice == 7:  # ヘルプ・ドキュメント
                    show_help()
                elif choice == 8:  # 終了
                    self.running = False
                    self._show_goodbye()
                    break

            except (KeyboardInterrupt, EOFError):
                self.running = False
                self._show_goodbye()
                break

    def _show_under_construction(self, feature_name: str, description: str) -> None:
        """Show under construction message with rich formatting."""
        console.print()

        construction_panel = Panel(
            Align.center(
                Text.assemble(
                    ("🚧 ", "bold yellow"),
                    ("実装中", "bold yellow"),
                    (" 🚧", "bold yellow"),
                    "\n\n",
                    (feature_name, "bold cyan"),
                    ("\n\n", ""),
                    (description, "dim"),
                    ("\n\n", ""),
                    ("この機能は現在開発中です。", "italic"),
                    ("\n", ""),
                    ("今後のアップデートをお待ちください！", "italic green"),
                )
            ),
            title="[bold bright_yellow]🚧 Coming Soon 🚧[/bold bright_yellow]",
            border_style="yellow",
            box=DOUBLE,
            padding=(1, 2),
            width=70,
        )

        console.print(construction_panel)
        console.print()

        if not ui.confirm("メインメニューに戻りますか？", default=True):
            self.running = False

    def _show_goodbye(self) -> None:
        """Show goodbye message with rich formatting."""
        console.print()

        goodbye_panel = Panel(
            Align.center(
                Text.assemble(
                    ("SF DevTools をご利用いただき、", "bright_white"),
                    ("\n", ""),
                    ("ありがとうございました。", "bright_white"),
                )
            ),
            title="[bold bright_green]🎉 See You Again! 🎉[/bold bright_green]",
            border_style="bright_green",
            box=DOUBLE,
            padding=(1, 2),
            width=60,
        )

        console.print(goodbye_panel)
        console.print()

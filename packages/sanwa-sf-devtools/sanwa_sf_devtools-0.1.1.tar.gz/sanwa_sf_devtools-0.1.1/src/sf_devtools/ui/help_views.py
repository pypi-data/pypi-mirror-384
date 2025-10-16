"""
Help and version display views for SF DevTools.
Separated from interactive.py for better code organization.
"""

import typer
from rich.align import Align
from rich.box import DOUBLE, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .. import __version__
from ..core.common import ui

console = Console()


def show_help() -> None:
    """Show help information with rich formatting."""
    console.clear()

    # ヘルプタイトル
    console.print(
        Panel(
            "[bold bright_cyan]📚 Salesforce MES 開発用 CLI ヘルプガイド[/bold bright_cyan]",
            border_style="bright_cyan",
            box=DOUBLE,
        )
    )
    console.print()

    # 概要セクション
    overview_panel = Panel(
        "[bright_white]このツールは、Salesforce MES パッケージ開発を効率化する統合CLIです。\n"
        "対話型インターフェースにより、複雑な操作を簡単に実行できます。[/bright_white]",
        title="[bold green]🎯 概要[/bold green]",
        border_style="green",
        box=ROUNDED,
    )
    console.print(overview_panel)
    console.print()

    # 機能一覧テーブル
    features_table = Table(
        title="[bold bright_blue]✨ 主な機能[/bold bright_blue]",
        show_header=True,
        header_style="bold bright_blue",
        border_style="bright_blue",
        box=ROUNDED,
    )
    features_table.add_column("機能", style="bold cyan", width=30)
    features_table.add_column("説明", style="white", width=50)

    features = [
        ("📦 Manifest管理", "マニフェストファイルの統合管理"),
        ("🏗️ Core パッケージ管理", "ベースとなるCoreパッケージの作成・管理"),
        ("⚙️ MES パッケージ管理", "MESパッケージの作成・バージョン管理"),
        ("🚀 パッケージテスト・デプロイ", "パッケージのテスト・デプロイメント"),
        ("🌍 スクラッチ組織管理", "開発用スクラッチ組織の作成・管理"),
        ("🔄 SFDMU データ同期", "SFDMUプラグインを使用したデータ同期"),
        ("⚙️ 設定・環境確認", "開発環境の設定と確認"),
    ]

    for feature, description in features:
        features_table.add_row(feature, description)

    console.print(features_table)
    console.print()

    # 使用方法パネル
    usage_content = """[bold cyan]対話型モード:[/bold cyan]
[green]sf_devtools[/green]                    対話型インターフェースを起動

[bold cyan]情報表示:[/bold cyan]
[green]sf_devtools --version[/green]         バージョン情報を表示
[green]sf_devtools --help[/green]            ヘルプを表示"""

    usage_panel = Panel(
        usage_content,
        title="[bold yellow]💻 使用方法[/bold yellow]",
        border_style="yellow",
        box=ROUNDED,
    )
    console.print(usage_panel)
    console.print()

    # 設定ファイル情報
    config_content = """[cyan]~/.mes-dev-cli-config[/cyan]     ユーザー設定ファイル
[cyan]./.mes-dev-cli-config[/cyan]     プロジェクト設定ファイル"""

    config_panel = Panel(
        config_content,
        title="[bold magenta]⚙️ 設定ファイル[/bold magenta]",
        border_style="magenta",
        box=ROUNDED,
    )

    # ドキュメント情報
    docs_content = """[cyan]documents/DEV_README.md[/cyan]   開発者向けガイド
[cyan]scripts/README.md[/cyan]         スクリプト詳細説明"""

    docs_panel = Panel(
        docs_content,
        title="[bold blue]📖 詳細ドキュメント[/bold blue]",
        border_style="blue",
        box=ROUNDED,
    )

    # サポート情報
    support_content = """問題が発生した場合は、以下の手順をお試しください：
1. [green]設定・環境確認[/green] → [green]診断レポート生成[/green] を実行
2. エラーメッセージをコピーして開発チームに報告
3. [cyan]documents/DEV_README.md[/cyan] でトラブルシューティングを確認"""

    support_panel = Panel(
        support_content,
        title="[bold red]🆘 サポート[/bold red]",
        border_style="red",
        box=ROUNDED,
    )

    # パネルを2列で表示
    console.print(Columns([config_panel, docs_panel]))
    console.print()
    console.print(support_panel)
    console.print()

    # 区切り線
    console.print(
        Rule("[bold bright_cyan]✨ 戻る ✨[/bold bright_cyan]", style="bright_cyan")
    )

    if ui.confirm("📋 メインメニューに戻りますか？", default=True):
        return
    else:
        raise typer.Exit(0)


def show_version() -> None:
    """Show version information with rich formatting."""
    console.clear()

    # バージョン情報テーブル
    version_table = Table(
        title="[bold bright_green]🚀 アプリケーション情報[/bold bright_green]",
        show_header=False,
        border_style="bright_green",
        box=DOUBLE,
        padding=(1, 2),
        width=60,
    )

    version_table.add_column("項目", style="bold cyan", width=20)
    version_table.add_column("詳細", style="bright_white", width=35)

    version_info = [
        ("🏷️ 名前", "Salesforce MES 開発用 CLI"),
        ("📊 バージョン", f"{__version__} (Python版)"),
        ("👥 作成者", "Sanwa Forklift Development Team"),
        ("🛠️ 技術", "Python + Typer + Rich"),
        ("📅 リリース", "2025年版"),
        ("🌟 種別", "対話型コマンドライン"),
    ]

    for item, detail in version_info:
        version_table.add_row(item, detail)

    console.print(Align.center(version_table))
    console.print()

    # 技術スタック情報
    tech_panel = Panel(
        Align.center(
            Text.assemble(
                ("🐍 ", "yellow"),
                ("Python", "bold blue"),
                (" + ", "dim"),
                ("⌨️ ", "cyan"),
                ("Typer", "bold cyan"),
                (" + ", "dim"),
                ("🎨 ", "magenta"),
                ("Rich", "bold magenta"),
                (" + ", "dim"),
                ("❓ ", "green"),
                ("Inquirer", "bold green"),
                "\n\n",
                ("現代的で美しいCLIフレームワークの組み合わせ", "italic dim"),
            )
        ),
        title="[bold bright_blue]⚙️ 技術スタック[/bold bright_blue]",
        border_style="bright_blue",
        box=ROUNDED,
    )

    console.print(tech_panel)
    console.print()

    # 機能ハイライト
    features_text = Text()
    features_text.append("✨ ", style="yellow")
    features_text.append("対話型インターフェース", style="bold green")
    features_text.append(" | ", style="dim")
    features_text.append("🎨 ", style="magenta")
    features_text.append("リッチな出力", style="bold magenta")
    features_text.append(" | ", style="dim")
    features_text.append("⚡ ", style="cyan")
    features_text.append("高速実行", style="bold cyan")

    features_panel = Panel(
        Align.center(features_text),
        title="[bold bright_yellow]🌟 特徴[/bold bright_yellow]",
        border_style="bright_yellow",
        box=ROUNDED,
    )

    console.print(features_panel)
    console.print()

    # 区切り線
    console.print(
        Rule("[bold bright_green]✨ 戻る ✨[/bold bright_green]", style="bright_green")
    )

    if ui.confirm("📋 メインメニューに戻りますか？", default=True):
        return
    else:
        raise typer.Exit(0)

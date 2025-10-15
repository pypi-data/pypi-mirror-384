"""
Salesforce 開発用統合CLI（Python版）のメインエントリポイント
"""

import sys

import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .ui.interactive import InteractiveUI

console = Console()

# メインアプリケーション
app = typer.Typer(
    help="🚀 Salesforce 開発用統合CLI（対話型インターフェース）",
    no_args_is_help=False,
    rich_markup_mode="rich",
    invoke_without_command=True,
)


def version_callback(value: bool) -> None:
    """バージョン情報を表示するコールバック"""
    if value:
        console.print(
            Panel.fit(
                f"[bold blue]SF DevTools[/bold blue] v{__version__}\n"
                f"[dim]Salesforce 開発用統合CLI（対話型インターフェース）[/dim]\n"
                f"[dim]作成者: Sanwa Forklift Development Team[/dim]",
                title="バージョン情報",
                border_style="blue",
            )
        )
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="バージョン情報を表示",
    ),
) -> None:
    """
    🚀 Salesforce 開発用統合CLI（対話型インターフェース）

    このツールは、Salesforce 開発を効率化する対話型CLIです。

    使用方法:
    • sf_devtools - 対話型インターフェースを起動
    • sf_devtools --version - バージョン情報を表示

    対話型インターフェースでメニューから簡単に操作できます。
    """
    # サブコマンドが指定されていない場合、対話型インターフェースを起動
    if ctx.invoked_subcommand is None:
        try:
            ui = InteractiveUI()
            ui.run()
        except KeyboardInterrupt:
            console.print(
                "\n[green]👋 SF DevTools をご利用いただき、ありがとうございました！[/green]"
            )
        except Exception as e:
            console.print(f"[red]❌ エラーが発生しました: {e}[/red]")
            console.print(
                "[dim]問題が解決しない場合は、開発チームにお問い合わせください。[/dim]"
            )
        finally:
            raise typer.Exit()


if __name__ == "__main__":
    app()

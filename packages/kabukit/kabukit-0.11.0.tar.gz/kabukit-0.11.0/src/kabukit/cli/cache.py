"""Cache management commands."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.tree import Tree

from kabukit.utils.config import get_cache_dir

if TYPE_CHECKING:
    from pathlib import Path

app = typer.Typer(add_completion=False, help="キャッシュを管理します。")


def add_to_tree(tree: Tree, path: Path) -> None:
    for p in sorted(path.iterdir()):
        if p.is_dir():
            branch = tree.add(p.name)
            add_to_tree(branch, p)
        else:
            size = p.stat().st_size
            formatted_size = format_size(size)
            tree.add(f"{p.name} ({formatted_size})")


@app.command()
def tree() -> None:
    """キャッシュディレクトリのツリー構造を表示します。"""
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        typer.echo(f"キャッシュディレクトリ '{cache_dir}' は存在しません。")
        return

    console = Console()
    tree_view = Tree(str(cache_dir))
    add_to_tree(tree_view, cache_dir)
    console.print(tree_view)


@app.command()
def clean() -> None:
    """キャッシュディレクトリを削除します。"""
    cache_dir = get_cache_dir()

    if not cache_dir.exists():
        typer.echo(f"キャッシュディレクトリ '{cache_dir}' は存在しません。")
        return

    try:
        shutil.rmtree(cache_dir)
        msg = f"キャッシュディレクトリ '{cache_dir}' を正常にクリーンアップしました。"
        typer.echo(msg)
    except OSError:
        msg = f"キャッシュディレクトリ '{cache_dir}' のクリーンアップ中に"
        msg += "エラーが発生しました。"
        typer.secho(msg, fg=typer.colors.RED, bold=True)
        raise typer.Exit(1) from None


def format_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"

    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"

    return f"{size_in_bytes / (1024 * 1024):.1f} MB"

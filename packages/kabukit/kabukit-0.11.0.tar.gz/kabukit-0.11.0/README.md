# kabukit

[![PyPI Version][pypi-v-image]][pypi-v-link]
[![Python Version][python-v-image]][python-v-link]
[![Build Status][GHAction-image]][GHAction-link]
[![Coverage Status][codecov-image]][codecov-link]
[![Documentation Status][docs-image]][docs-link]

A Python toolkit for Japanese financial market data,
supporting J-Quants and EDINET APIs.

kabukit は、 [J-Quants API](https://jpx-jquants.com/) および [EDINET API](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0110.html) から、効率的に日本の金融市場データを取得するツールキットです。

高速なデータ処理ライブラリである [Polars](https://pola.rs/) と、モダンな非同期 HTTP クライアントである [httpx](https://www.python-httpx.org/) を基盤として構築されており、パフォーマンスを重視しています。

## インストール

`pip` または `uv` を使ってインストールします。Python バージョンは 3.12 以上が必要です。

```bash
pip install kabukit
```

## コマンドラインから使う

kabukit は、 [J-Quants API](https://jpx-jquants.com/) および [EDINET API](https://disclosure2dl.edinet-fsa.go.jp/guide/static/disclosure/WZEK0110.html) からデータを取得するための便利なコマンドラインインターフェース（CLI）を提供します。

具体的な使い方は、次の利用ガイドを参照してください。

- [コマンドラインインターフェースの使い方](https://daizutabi.github.io/kabukit/guides/cli/)

## ノートブックから使う

kabukit は、コマンドラインだけでなく、Python コードからも API として利用できます。httpx を使って非同期でデータを取得するため、[Jupyter](https://jupyter.org/) や [marimo](https://marimo.io/) のような非同期処理を直接扱えるノートブック環境と非常に相性が良いです。

具体的な使い方は、以下の利用ガイドを参照してください。

- [J-Quants API の使い方](https://daizutabi.github.io/kabukit/guides/jquants/)
- [EDINET API の使い方](https://daizutabi.github.io/kabukit/guides/edinet/)

<!-- Badges -->

[pypi-v-image]: https://img.shields.io/pypi/v/kabukit.svg
[pypi-v-link]: https://pypi.org/project/kabukit/
[python-v-image]: https://img.shields.io/pypi/pyversions/kabukit.svg
[python-v-link]: https://pypi.org/project/kabukit
[GHAction-image]: https://github.com/daizutabi/kabukit/actions/workflows/ci.yaml/badge.svg?branch=main&event=push
[GHAction-link]: https://github.com/daizutabi/kabukit/actions?query=event%3Apush+branch%3Amain
[codecov-image]: https://codecov.io/github/daizutabi/kabukit/graph/badge.svg?token=Yu6lAdVVnd
[codecov-link]: https://codecov.io/github/daizutabi/kabukit?branch=main
[docs-image]: https://img.shields.io/badge/docs-latest-blue.svg
[docs-link]: https://daizutabi.github.io/kabukit/

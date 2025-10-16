# SF DevTools Python 版

Salesforce 開発を効率化するための統合 CLI ツールです。`Typer` をベースにしたモダンな構成と、`Rich` による視覚的にわかりやすい出力を備えています。

## 特徴

- Typer による高速な CLI 構築とサブコマンド設計
- Rich を使ったカラー表示・パネル表示
- インタラクティブメニュー（Inquirer）による操作性
- Salesforce CLI (`sf`) をラップした組織/パッケージ操作
- 前提条件チェックや設定ディレクトリの自動解決

## 導入ワークフロー（別リポジトリへの自動展開）

この CLI は、別の Salesforce 開発リポジトリを支援する補助ツールとして利用できます。パッケージをビルドして配布し、対象リポジトリのセットアップ手順に組み込む想定です。

1. **バージョン管理**

    - `pyproject.toml` の `version` を更新し、`CHANGELOG` 等があれば整備します。
    - テスト (`PYTHONPATH=src pytest`) と静的検査を実行し、リリースタグに備えます。

1. **アーティファクト生成**

    - `python -m pip install build`
    - `python -m build`
    - `dist/` ディレクトリに配布物（sdist / wheel）が生成されます。

1. **配布**

    - PyPI に公開（本リポジトリの Release ワークフローで自動化）。
    - テスト用には TestPyPI を併用可能。

1. **対象リポジトリでの自動導入**

    - `requirements.txt` もしくは `pyproject.toml` に PyPI の依存を追加します。

    `requirements.txt`

    ```text
    sanwa-sf-devtools==<version>
    ```

    `pyproject.toml`

    ```toml
    [project]
    dependencies = [
        "sanwa-sf-devtools==<version>",
    ]
    ```

    - Dev Container や CI のセットアップスクリプトで `python -m pip install -r requirements.txt` を実行して自動導入します。
    - CLI 呼び出し例をドキュメント化（例: `sf_devtools --interactive`）。

1. **更新のロールアウト**

    - 新バージョンをリリースしたら、対象リポジトリの依存バージョンを更新する PR を自動生成する仕組み (Renovate/Dependabot) を検討してください。
    - 自動テストに `sf_devtools --version` や主要コマンドのスモークを組み込み、導入確認を行います。

## クイックスタート

> CI/リリースの自動化: 本リポジトリには GitHub Actions ワークフローが同梱されています。
>
> - CI: push/PR で lint, typecheck, test, build を Python 3.10/3.12 マトリクスで実行（`.github/workflows/ci.yml`）
> - Release: タグ `v*` で sdist/wheel をビルドし PyPI へ公開、GitHub Release に添付（`.github/workflows/release.yml`）

```bash
# 開発に必要な依存を一式インストール
python -m pip install -e ".[dev]"

# パッケージのインストール名: sanwa-sf-devtools（公開時）
# コマンド名は sf_devtools （従来通り）です

# CLI ヘルプを確認
sf_devtools --help

# 対話型 UI を起動
sf_devtools --interactive
```

### 主なコマンド

- `sf_devtools --interactive` : 対話型メニューを起動
- `sf_devtools org list` : 認証済み組織の一覧を表示
- `sf_devtools org list --json` : JSON 形式で一覧を取得
- `sf_devtools --version` : バージョン情報を表示

## 開発ワークフロー

### 必須ツール

- Python 3.10 以上
- Salesforce CLI (`sf`)
- `jq`, `rsync`（前提条件チェックで利用）

### セットアップ手順

1. リポジトリをクローンし、任意で仮想環境を作成
2. ルートディレクトリで `python -m pip install -e ".[dev]"`
3. CLI を試す場合は `sf_devtools --help` を実行

### テスト & 品質チェック

```bash
# 単体テスト
PYTHONPATH=src pytest

# コードフォーマット
black src/sf_devtools tests
isort src/sf_devtools tests

# 型チェック
mypy src/sf_devtools
```

### Black を中心とした整形フロー（ローカル/CI の統一）

CI では `black --check` と `isort --check-only` を実行し、フォーマット崩れがあると失敗します。ローカルでは以下で自動整形・確認ができます。

```bash
# 自動整形（Black/Isort）
black src/sf_devtools src/tests
isort src/sf_devtools src/tests

# 差分なし確認（CI と同等）
black --check src/sf_devtools src/tests
isort --check-only src/sf_devtools src/tests
```

pre-commit を使うとコミット前に自動で Black/Isort（＋ Flake8）が走ります。

```bash
# 初回のみ（dev 依存に含まれています）
pre-commit install

# 全ファイルに対して一度だけ実行
pre-commit run --all-files
```

CI で失敗した場合は、上記の自動整形コマンドを実行して差分をコミットすれば解消できます。

### ビルド

パッケージ配布物 (sdist / wheel) を生成するには `build` モジュールを利用してください。

```bash
python -m pip install build  # 未導入の場合のみ
python -m build
```

`dist/` にアーティファクト（例: `sanwa_sf_devtools-<version>.tar.gz`, `sanwa_sf_devtools-<version>-py3-none-any.whl`）が生成されます。

## プロジェクト構成

```text
src/
  sf_devtools/   # ライブラリ / CLI 本体
  tests/         # pytest ベースのユニットテスト
test_modules.py  # 互換性確認用スモークテスト
```

## 今後の拡張予定

- パッケージ管理コマンドの拡充
- デプロイメント関連ユーティリティ
- スクラッチ組織管理機能の強化
- SFDMU 同期サポート
- 設定管理・メタデータ操作機能

## リリース運用マニュアル（Playbook）

このプロジェクトは GitHub Actions で CI/Release を自動化しています。人手作業は最小限ですが、以下の手順で安定したリリースを進めてください。

### 前提

- Python 3.10 以上
- リポジトリに対する push 権限と Release 作成権限
- main ブランチがグリーン（CI 通過）であること

### 1. バージョン更新と変更履歴の整備

1. `pyproject.toml` の `[project] version` を次のバージョンに更新
2. `README.md`/`MIGRATION_SUMMARY.md`/`CHANGELOG.md`（存在する場合）を更新
3. コミット: `chore(release): vX.Y.Z` のようなメッセージでコミット/プッシュ

### 2. ローカルで最終確認（任意）

```bash
# 依存の同期
python -m pip install -e ".[dev]"

# 品質ゲート
python -m black --check src/sf_devtools src/tests
python -m isort --check-only src/sf_devtools src/tests
python -m mypy src/sf_devtools
python -m pytest -q

# 配布物の生成
python -m pip install build
python -m build
```

`dist/` 配下に sdist/wheel が生成されればOKです。

### 3. タグ付けで Release 自動化を起動（PyPI へ公開）

```bash
git pull --rebase
git tag vX.Y.Z
git push origin vX.Y.Z
```

- `.github/workflows/release.yml` が走り、sdist/wheel がビルドされ PyPI へ公開、あわせて GitHub Release に添付されます。
- リリースノートは自動生成（必要に応じて手動で追記/編集）。

### 4. リリース検証

クリーン環境で以下を実施し、インストールと起動ができることを確認します。

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "sanwa-sf-devtools==X.Y.Z"
sf_devtools --version
sf_devtools --help
```

問題があれば Release を下書きへ戻すか、修正版 `vX.Y.Z+1` を切って再リリースしてください。

### 5. メンテナンスポリシー（推奨）

- CI の mypy/pytest がグリーンでない限りリリースしない
- 依存更新は Renovate/Dependabot で自動 PR、CI で安全性を担保
- セキュリティ修正はパッチバージョンで迅速に対応

## 別リポジトリへの取り込みマニュアル（PyPI）

Salesforce 開発用の別リポジトリから、本ツールを PyPI 経由で導入し、コマンドで起動できるようにする手順です。

### 1. 依存の追加

`requirements.txt`

```text
sanwa-sf-devtools==X.Y.Z
```

`pyproject.toml`

```toml
[project]
dependencies = [
        "sanwa-sf-devtools==X.Y.Z",
]
```

### 2. セットアップ（Dev Container / ローカル）

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

初回セットアップ時に `sf` CLI, `jq`, `rsync` も整えてください（本ツールの前提条件）。

### 3. CI での導入とスモークテスト

```yaml
name: Tool smoke
on: [push]
jobs:
    smoke:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
                with:
                    python-version: '3.10'
            - name: Install tool
                run: |
                    python -m pip install --upgrade pip
                    python -m pip install sanwa-sf-devtools==X.Y.Z
            - name: Smoke run
                run: |
                    sf_devtools --version
                    sf_devtools --help | head -n 20
```

Salesforce 組織に対する操作（`sf` コマンド）を伴う場合は、認証トークンや SFDX 設定を CI へ安全に注入してください（GitHub Secrets など）。

### 4. 使い方の例（対象リポジトリ側）

- 対話型 UI: `sf_devtools --interactive`
- 組織一覧: `sf_devtools org list`
- JSON 出力: `sf_devtools org list --json`

### 5. バージョンアップのロールアウト

- 本リポジトリで新しいタグ `vX.Y.Z` を発行すると PyPI に公開され、GitHub Release に配布物が添付されます。
- 対象リポジトリでは `requirements.txt`（または `pyproject.toml`）の依存を `sanwa-sf-devtools==X.Y.Z` に更新し、PR として配布します。
- Renovate/Dependabot を利用して自動更新 PR を作ることも可能です（PyPI 依存のバージョンマッチを設定）。

### 6. トラブルシューティング

- `sf_devtools: command not found`
  - インストールが完了しているか、仮想環境が有効か確認
    - `python -m pip show sanwa-sf-devtools`（配布名は `sanwa-sf-devtools`。インポート名/CLI は `sf_devtools`）
- `sf` CLI が見つからない
  - Salesforce CLI のインストールと PATH 設定を確認
- ImportError/ModuleNotFoundError
    - Python のバージョンが 3.10 以上か、依存が正しく解決されているかを確認

<!-- 付録（必要になった場合のみ有効化）: プライベートな VCS 依存や社内インデックスでの導入手順は、PyPI へ方針転換したため本文から削除しました。 -->


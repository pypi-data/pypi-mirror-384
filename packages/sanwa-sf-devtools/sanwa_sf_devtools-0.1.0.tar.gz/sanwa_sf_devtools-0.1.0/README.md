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
    - `dist/` ディレクトリに `sf_devtools-<version>.tar.gz` と `sf_devtools-<version>-py3-none-any.whl` が生成されます。

1. **配布**

    - 社内 PyPI や GitHub Releases にビルド済みアーカイブをアップロードします。
    - 例: `https://github.com/sanwa-system/sanwa-sf-devtools/releases/tag/v<version>` に `dist/*` を添付。

1. **対象リポジトリでの自動導入**

    - `requirements.txt` もしくは `pyproject.toml` に GitHub リリース URL / 社内 PyPI を参照する形で依存を追加します。

    ```text
    sf_devtools @ https://github.com/sanwa-system/sanwa-sf-devtools/releases/download/v<version>/sf_devtools-<version>-py3-none-any.whl
    ```

    - Dev Container や CI のセットアップスクリプトで `python -m pip install -r requirements.txt` を実行して自動導入します。
    - CLI 呼び出し例をドキュメント化（例: `sf_devtools --interactive`）。

1. **更新のロールアウト**

    - 新バージョンをリリースしたら、対象リポジトリの依存バージョンを更新する PR を自動生成する仕組み (Renovate/Dependabot) を検討してください。
    - 自動テストに `sf_devtools --version` や主要コマンドのスモークを組み込み、導入確認を行います。

## クイックスタート

> CI/リリースの自動化: 本リポジトリには GitHub Actions ワークフローが同梱されています。
>
> - CI: push/PR で lint, typecheck, test, build を実行（`.github/workflows/ci.yml`）
> - Release: タグ `v*` で sdist/wheel をビルドしリリースに添付（`.github/workflows/release.yml`）

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

- Python 3.12 以上
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

`dist/` にアーティファクト（`sf_devtools-<version>.tar.gz`, `sf_devtools-<version>-py3-none-any.whl`）が生成されます。

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

- Python 3.12 以上
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

### 3. タグ付けで Release 自動化を起動（GitHub Packages へ公開を含む）

```bash
git pull --rebase
git tag vX.Y.Z
git push origin vX.Y.Z
```

- `.github/workflows/release.yml` が走り、sdist/wheel がビルドされ GitHub Release に添付されます。
- さらに GitHub Packages（Python レジストリ）へも自動で公開されます。
- リリースノートは自動生成（必要に応じて手動で追記/編集）。

### 4. リリース検証

クリーン環境で以下を実施し、インストールと起動ができることを確認します。

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install "sf_devtools @ https://github.com/sanwa-system/sanwa-sf-devtools/releases/download/vX.Y.Z/sf_devtools-X.Y.Z-py3-none-any.whl"
sf_devtools --version
sf_devtools --help
```

問題があれば Release を下書きへ戻すか、修正版 `vX.Y.Z+1` を切って再リリースしてください。

### 5. メンテナンスポリシー（推奨）

- CI の mypy/pytest がグリーンでない限りリリースしない
- 依存更新は Renovate/Dependabot で自動 PR、CI で安全性を担保
- セキュリティ修正はパッチバージョンで迅速に対応

## 別リポジトリへの取り込みマニュアル

Salesforce 開発用の別リポジトリから、本ツールを依存として導入し、コマンドで起動できるようにする手順です。GitHub Release の配布物を利用する想定です。

### 1. 依存の追加（GitHub Packages を利用）

- pip のインデックスに GitHub Packages を追加した上で、通常の依存として指定します。

`requirements.txt`

```text
sf-devtools==0.1.0
```

`pyproject.toml`

```toml
[project]
dependencies = [
    "sf-devtools==0.1.0",
]
```

注: GitHub Packages の追加方法は次節「セットアップ」で説明します。

### 2. セットアップ（Dev Container / ローカル）

pip に GitHub Packages を追加します（OWNER は `sanwa-system`）。

`~/.pip/pip.conf` または コンテナ内の `/etc/pip.conf` など:

```ini
[global]
index-url = https://pypi.org/simple
extra-index-url = https://USERNAME:TOKEN@pypi.pkg.github.com/sanwa-system/simple
```

- USERNAME は GitHub ユーザー名
- TOKEN は Personal Access Token (classic) で最低 `read:packages` を付与

その後は通常通り:

```bash
python -m pip install -r requirements.txt
```

初回セットアップ時に `sf` CLI, `jq`, `rsync` も整えてください（本ツールの前提条件）。

### 3. CI での導入とスモークテスト（GITHUB_TOKEN 利用）

例として GitHub Actions（Node/Java など他スタックでも同様）:

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
                    python-version: '3.12'
                    - name: Install tool
                        env:
                            PIP_EXTRA_INDEX_URL: https://github:${{ secrets.GITHUB_TOKEN }}@pypi.pkg.github.com/sanwa-system/simple
                        run: |
                            python -m pip install --upgrade pip
                            python -m pip install -r requirements.txt
            - name: Smoke run
                run: |
                    sf_devtools --version
                    sf_devtools --help
```

Salesforce 組織に対する操作（`sf` コマンド）を伴う場合は、認証トークンや SFDX 設定を CI へ安全に注入してください（GitHub Secrets など）。

### 4. 使い方の例（対象リポジトリ側）

- 対話型 UI: `sf_devtools --interactive`
- 組織一覧: `sf_devtools org list`
- JSON 出力: `sf_devtools org list --json`

### 5. バージョンアップのロールアウト

- 本リポジトリで新しいタグ `vX.Y.Z` を発行すると Release に配布物が添付されます。
- 対象リポジトリでは `requirements.txt` の URL を新バージョンへ更新し、PR として配布します。
- Renovate/Dependabot を利用して自動更新 PR を作ることも可能です（URL のバージョンマッチパターンを設定）。

### 6. トラブルシューティング

- `sf_devtools: command not found`
  - インストールが完了しているか、仮想環境が有効か確認
  - `python -m pip show sf-devtools`（パッケージ名が `sf_devtools` である点に注意）
- `sf` CLI が見つからない
  - Salesforce CLI のインストールと PATH 設定を確認
- ImportError/ModuleNotFoundError
  - Python のバージョンが 3.12 以上か、依存が正しく解決されているかを確認

## プライベート導入（SSH / VCS インストール）マニュアル

プライベートリポジトリゆえに Release アセットの直リンクは 404 になることがあります。Git 認証（SSH）でタグから直接インストールする運用を推奨します。

### A. 開発側（このリポジトリ）

1. タグでの配布を前提にする
     - リリース時は `vX.Y.Z` のタグを main に打つ（既存の Release ワークフローはそのまま利用可能）
2. リポジトリのアクセス方針
     - 組織の開発者は通常の GitHub SSH キーで clone/checkout できるようにする
     - CI/自動化での導入向けには、導入側リポジトリ専用の Deploy Key（読み取り専用）を発行するのが安全
3. セキュリティ注意
     - タグは改ざん防止のため保護設定を検討
     - 秘密鍵は開発者個人のマシンまたは CI のシークレットにのみ保存。リポジトリや requirements にトークン/鍵を埋め込まない

### B. 導入リポジトリ（/ 導入環境）

1. SSH キー準備
     - 開発者端末: GitHub に公開鍵を登録（既存運用でOK）
     - CI: 導入リポジトリの Settings → Deploy keys に公開鍵（Read only）を登録。秘密鍵は CI Secrets に保存

2. known_hosts の準備（CI）
     - GitHub を known_hosts に追加（ssh-keyscan を利用）

3. requirements.txt で VCS 依存を指定
     - 例: タグ固定

         ```text
         git+ssh://git@github.com/sanwa-system/sanwa-sf-devtools.git@vX.Y.Z
         ```

     - 例: ブランチ固定（推奨はタグ）

         ```text
         git+ssh://git@github.com/sanwa-system/sanwa-sf-devtools.git@main
         ```

4. ローカル導入（開発端末）

     ```bash
     # 事前に SSH 接続確認
     ssh -T git@github.com  # Hi <user> が出ればOK

     # インストール
     python -m pip install -r requirements.txt
     sf_devtools --version
     ```

5. CI（GitHub Actions）での導入例

     ```yaml
     name: Install sf_devtools via SSH
     on: [push]
     jobs:
         install:
             runs-on: ubuntu-latest
             steps:
                 - uses: actions/checkout@v4
                 - uses: actions/setup-python@v5
                     with:
                         python-version: '3.12'
                 - name: Prepare SSH for GitHub
                     run: |
                         mkdir -p ~/.ssh
                         ssh-keyscan github.com >> ~/.ssh/known_hosts
                         chmod 644 ~/.ssh/known_hosts
                 - name: Start ssh-agent and add deploy key
                     uses: webfactory/ssh-agent@v0.9.0
                     with:
                         ssh-private-key: ${{ secrets.SF_DEVTOOLS_DEPLOY_KEY }}
                 - name: Install dependencies
                     run: |
                         python -m pip install --upgrade pip
                         python -m pip install -r requirements.txt
                 - name: Smoke
                     run: |
                         sf_devtools --version
                         sf_devtools --help
     ```

6. よくあるエラー
     - Permission denied (publickey)
         - Deploy Key が未設定/権限不足、または ssh-agent に秘密鍵が読み込まれていない
     - Host key verification failed
         - `known_hosts` 未登録。`ssh-keyscan github.com` を追加
     - Could not find a version that satisfies the requirement ...
         - URL のタグ/ブランチ名が存在するか再確認。タグ運用なら `vX.Y.Z` の誤字に注意


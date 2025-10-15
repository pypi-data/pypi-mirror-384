#!/bin/bash
# DevContainer セットアップスクリプト
# コンテナ作成後に自動実行されるスクリプト

set -e  # エラー時にスクリプトを停止（ただし一部は明示的に継続）

echo "🚀 Sanwa MES 開発環境のセットアップを開始します..."

# 共通: リトライ用関数
retry() {
    local -r max_attempts="${1:-5}"
    local -r sleep_sec="${2:-5}"
    shift 2
    local attempt=1
    until "$@"; do
        exit_code=$?
        if (( attempt >= max_attempts )); then
            return "$exit_code"
        fi
        echo "⏳ リトライ ${attempt}/${max_attempts} (exit=${exit_code})..."
        attempt=$(( attempt + 1 ))
        sleep "$sleep_sec"
    done
}

# ネットワーク到達性チェック（npm レジストリ）
echo "🌐 ネットワーク到達性を確認中..."
set +e
retry 5 3 npm ping >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  npm レジストリへの到達性が不安定です（後で自動リトライします）"
fi
set -e

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Node.js 依存関係のインストール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📦 Node.js 依存関係をインストール中..."
if [ -f "package.json" ]; then
    npm install
    echo "✅ Node.js 依存関係のインストールが完了しました"
else
    echo "⚠️  package.json が見つかりません"
fi

# npm のネットワーク/プロキシ設定を調整
echo "🔧 npm 設定を調整中..."
# リトライ回数とタイムアウトを延長
npm config set fetch-retries 5 >/dev/null
npm config set fetch-retry-mintimeout 20000 >/dev/null
npm config set fetch-retry-maxtimeout 120000 >/dev/null
npm config set registry "https://registry.npmjs.org/" >/dev/null

# 環境変数のプロキシ設定がある場合は npm にも適用
if [ -n "${HTTP_PROXY:-}" ]; then
    npm config set proxy "$HTTP_PROXY" >/dev/null || true
fi
if [ -n "${HTTPS_PROXY:-}" ]; then
    npm config set https-proxy "$HTTPS_PROXY" >/dev/null || true
fi
if [ -n "${NO_PROXY:-}" ]; then
    npm config set noproxy "$NO_PROXY" >/dev/null || true
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OpenAI Codex のインストール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "OpenAI Codexをインストール中..."
# Codex のインストールはネットワーク環境に左右されるため、リトライし、最終的に失敗してもセットアップ継続
set +e
retry 5 5 npm install -g @openai/codex
codex_install_status=$?
set -e
if [ $codex_install_status -ne 0 ]; then
        echo "❌ OpenAI Codex のインストールに失敗しましたが、セットアップは続行します。"
        echo "   後でコンテナ内ターミナルから次を実行してください: npm install -g @openai/codex"
else
        echo "✅ OpenAI Codex のインストールが完了しました"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Gemini CLI のインストール
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "Gemini CLIをインストール中..."
# Gemini CLI もネットワークに依存するため、Codex 同様にリトライし失敗しても継続
set +e
retry 5 5 npm install -g @google/gemini-cli
gemini_install_status=$?
set -e
if [ $gemini_install_status -ne 0 ]; then
        echo "❌ Gemini CLI のインストールに失敗しましたが、セットアップは続行します。"
        echo "   後でコンテナ内ターミナルから次を実行してください: npm install -g @google/gemini-cli"
else
        echo "✅ Gemini CLI のインストールが完了しました"
        if command -v gemini >/dev/null 2>&1; then
            gemini --version || true
        fi
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Python 環境のセットアップ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "🐍 Python 環境をセットアップ中..."

# pipのアップグレード
python3 -m pip install --upgrade pip

# MES CLI Python版のインストール
if [ -d "sf_devtools-py" ]; then
    echo "📦 SF DevTools Python版をインストール中..."
    pushd sf_devtools-py >/dev/null
    
    # エディタブルモードでインストール
    python3 -m pip install -e .
    
    # 開発用依存関係をインストール
    python3 -m pip install -e ".[dev]"
    
    # インストール確認
    if python3 -m sf_devtools.main --version > /dev/null 2>&1; then
        echo "✅ SF DevTools Python版のインストールが完了しました"
        python3 -m sf_devtools.main --version
    else
        echo "❌ SF DevTools Python版のインストールに失敗しました"
    fi
    
    popd >/dev/null
else
    echo "⚠️  scripts/sf_devtools-py ディレクトリが見つかりません"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Salesforce CLI の確認
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "⚡ Salesforce CLI の確認中..."
if sf --version > /dev/null 2>&1; then
    echo "✅ Salesforce CLI が利用可能です"
    sf --version
else
    echo "❌ Salesforce CLI が見つかりません"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 権限の設定
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# echo "🔒 権限を設定中..."
# ワークスペース内のスクリプトファイルに実行権限を付与
# find . -name "*.sh" -type f -exec chmod +x {} \;

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# セットアップ完了
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "🎉 セットアップが完了しました！"
echo ""
echo "利用可能なコマンド:"
echo "  • sf_devtools --interactive  - 対話型モード（推奨）"
echo "  • sf_devtools hello          - Python CLI のテスト"
echo "  • sf_devtools org list       - 組織一覧表示"
echo "  • codex --help               - OpenAI Codex のヘルプ"
echo "  • codex                      - OpenAI Codex を起動"
echo "  • gemini --help              - Gemini CLI のヘルプ"
echo "  • gemini                     - Gemini CLI を起動"
echo "  • sf org list                - Salesforce CLI での組織一覧"
echo "  • npm run test               - Node.js テスト実行"
echo "  • cd scripts/sf_devtools-py && pytest  - Python テスト実行"
echo ""
echo "開発を開始してください！ 🚀"

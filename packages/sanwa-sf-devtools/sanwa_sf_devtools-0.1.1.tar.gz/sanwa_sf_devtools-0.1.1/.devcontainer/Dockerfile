# ──────────────────────────────
# Base: Salesforce CLI (latest-full)
# ──────────────────────────────
FROM salesforce/cli:latest-full

# 必要なパッケージのインストール
RUN apt update && apt install -y \
    zsh \
    curl \
    fonts-powerline \
    vim \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

# zshをデフォルトのシェルに設定
RUN chsh -s $(which zsh)

# Starshipのインストール
RUN curl -sS https://starship.rs/install.sh | sh -s -- --yes

# Oh My Zshのインストール
RUN sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)" --unattended

# Starship設定を.zshrcに追加
RUN echo 'eval "$(starship init zsh)"' >> /root/.zshrc

# StarshipのPastel Powerlineプリセットを適用
RUN mkdir -p /root/.config && starship preset pastel-powerline -o /root/.config/starship.toml

# Salesforce CLI プラグイン: SFDMU をインストール
RUN sf plugins install sfdmu@latest

# Python開発環境の設定
# pipをアップグレード
RUN python3 -m pip install --upgrade pip

# 一般的なPython開発ツールをグローバルにインストール
RUN python3 -m pip install \
    black>=23.0.0 \
    isort>=5.12.0 \
    mypy>=1.0.0 \
    pytest>=7.0.0 \
    pytest-cov>=4.0.0 \
    typer[all]>=0.9.0 \
    rich>=13.0.0 \
    pydantic>=2.0.0 \
    simple-salesforce>=1.12.0 \
    requests>=2.28.0

# ワークスペース位置（devcontainer.json と一致）
ENV WORKSPACE_DIR=/sanwa-sf-devtools
ENV PYTHONPATH="$WORKSPACE_DIR:$PYTHONPATH"

# コンテナ内のデフォルトシェルをzshに変更
CMD ["zsh"]
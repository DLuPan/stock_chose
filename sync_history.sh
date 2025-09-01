#!/bin/bash
#========================================================
# Script Name   : sync_history.sh
# Description   : 自动同步并运行 stock_chose 项目
# Author        : dlupan
# Date          : $(date '+%Y-%m-%d')
#========================================================

set -euo pipefail   # 严格模式：错误立即退出，未定义变量报错，管道出错退出

#-----------------------------
# 全局变量
#-----------------------------
REPO_URL="git@github.com:DLuPan/stock_chose.git"
LOCAL_DIR="/usr/local/apps/sync_stock/stock_chose"
BRANCH="main"
LOG_DIR="/usr/local/apps/sync_stock"
LOG_FILE="$LOG_DIR/output_$(date +%Y%m%d).log"
MAX_LOGS=10   # 最多保留的日志文件数
MAX_RETRIES=3 # git pull 最大重试次数
RETRY_DELAY=3 # 重试间隔（秒）

#-----------------------------
# 定位 uv 命令
#-----------------------------
find_uv() {
    if command -v uv >/dev/null 2>&1; then
        echo "$(command -v uv)"
    elif [ -x "$HOME/.local/bin/uv" ]; then
        echo "$HOME/.local/bin/uv"
    elif [ -x "/usr/local/bin/uv" ]; then
        echo "/usr/local/bin/uv"
    else
        echo "Error: uv not found in PATH or common locations." >&2
        exit 1
    fi
}

UV_BIN=$(find_uv)
export PATH="$(dirname "$UV_BIN"):$PATH"

#-----------------------------
# 工具函数
#-----------------------------
log() {
    local msg="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg"
}

cleanup_logs() {
    log "Cleaning old logs, keeping only the last $MAX_LOGS..."
    ls -1t "$LOG_DIR"/output_*.log 2>/dev/null | tail -n +$((MAX_LOGS+1)) | xargs -r rm -f
}

setup_git() {
    git config --global safe.directory "$LOCAL_DIR"
    git config --global user.email "wingsgod@outlook.com"
    git config --global user.name "dlupan"
}

# 新增：带重试的 git pull 函数
git_pull_with_retry() {
    local retries=0
    local success=false
    
    while [ $retries -lt $MAX_RETRIES ]; do
        log "Attempting git pull (attempt $((retries+1))/$MAX_RETRIES)..."
        # 放弃所有本地修改
        # 更改远程 URL 为 SSH 格式
        git remote set-url origin git@github.com:DLuPan/stock_chose.git
        git checkout -- .

        # 获取并强制使用远程内容
        git fetch --all
        git reset --hard origin/main
        if git pull origin "$BRANCH"; then
            success=true
            log "Git pull successful on attempt $((retries+1))"
            break
        else
            retries=$((retries+1))
            local remaining_attempts=$((MAX_RETRIES - retries))
            
            if [ $remaining_attempts -gt 0 ]; then
                log "Git pull failed on attempt $retries. Retrying in $RETRY_DELAY seconds... ($remaining_attempts attempts remaining)"
                sleep $RETRY_DELAY
            else
                log "Git pull failed after $MAX_RETRIES attempts."
            fi
        fi
    done
    
    if [ "$success" = false ]; then
        log "ERROR: All git pull attempts failed. Exiting."
        exit 1
    fi
}

clone_or_update_repo() {
    if [ ! -d "$LOCAL_DIR" ]; then
        log "Cloning repository..."
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$LOCAL_DIR"
    fi

    cd "$LOCAL_DIR"
    
    # 替换原来的 git pull 为带重试的版本
    git_pull_with_retry
}

sync_dependencies() {
    export UV_DEFAULT_INDEX="https://mirrors.aliyun.com/pypi/simple"
    log "Syncing dependencies with uv..."
    uv sync
}

run_tasks() {
    local cur_date
    cur_date=$(date +"%Y%m%d")

    log "Running sync-all..."
    uv run --package core cli sync-all

    for run in {1..15}; do
        log "Starting execution $run of 15..."
        uv run --package core cli sync-hist-all --end-date "$cur_date" --adjust hfq --max-workers 20

        if [ $run -lt 15 ]; then
            log "Waiting 30s before next run..."
            sleep 30
        fi
    done
    log "Running generate-stock-report with hfq adjustment..."
    uv run --package core cli generate-stock-report --adjust hfq
    
}

commit_and_push() {
    cd "$LOCAL_DIR"
    git add .
    if git commit -m "Automated update: $(date '+%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1; then
        log "Changes committed."
    else
        log "No changes to commit."
    fi
    git push -f origin "$BRANCH"
    log "Changes pushed to remote."
}

#-----------------------------
# 主流程
#-----------------------------
main() {
    # 日志输出：同时写文件和终端
    exec > >(tee -a "$LOG_FILE") 2>&1

    log "=== Script started ==="

    cleanup_logs
    setup_git
    clone_or_update_repo
    sync_dependencies
    run_tasks
    commit_and_push

    log "=== Script finished ==="
}

main "$@"
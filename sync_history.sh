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

clone_or_update_repo() {
    if [ ! -d "$LOCAL_DIR" ]; then
        log "Cloning repository..."
        git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$LOCAL_DIR"
    fi

    cd "$LOCAL_DIR"
    log "Pulling latest changes..."
    git pull origin "$BRANCH"
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

    for run in {1..8}; do
        log "Starting execution $run of 8..."
        uv run --package core cli sync-hist-all --end-date "$cur_date" --adjust hfq --max-workers 20

        if [ $run -lt 8 ]; then
            log "Waiting 30 minutes before next run..."
            sleep 1800
        fi
    done
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

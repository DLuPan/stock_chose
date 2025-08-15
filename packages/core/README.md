# 数据同步指令
``` shell
# 同步所有股票的实时数据
uv run --package cli sync-all
uv run --package cli sync-hist-all --start-date 19700101 --end-date 20250815 --adjust hfq
```
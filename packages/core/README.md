# 数据同步指令
``` shell
# 同步所有股票的实时数据
uv run .\packages\core\src\core\cli.py sync-all
uv run .\packages\core\src\core\cli.py sync-hist-all --start-date 19700101 --end-date 20250815 --adjust hfq
```
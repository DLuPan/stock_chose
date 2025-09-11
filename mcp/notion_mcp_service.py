# notion_mcp_service.py
import os
import json
import requests
from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()

# 读取环境变量
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Validate required environment variables
if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY environment variable is required")
if not DATABASE_ID:
    raise ValueError("NOTION_DATABASE_ID environment variable is required")

# Notion API 配置
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_API_VERSION
}

mcp = FastMCP("notion-tasks")


class NotionAPIError(Exception):
    """Notion API 错误异常"""
    pass


def notion_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """发送 Notion API 请求"""
    url = f"{NOTION_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, headers=HEADERS, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_detail = ""
        if hasattr(e.response, 'json') and e.response:
            try:
                error_detail = f" - {e.response.json()}"
            except:
                error_detail = f" - Status: {e.response.status_code}"
        raise NotionAPIError(f"Notion API 请求失败: {e}{error_detail}")


def page_to_task(page: Dict[str, Any]) -> dict:
    """将 Notion Page 转换为 Python dict"""
    props = page["properties"]
    
    # Safe property access with fallbacks
    def get_title(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        if prop.get("title") and len(prop["title"]) > 0:
            return prop["title"][0].get("plain_text")
        return None
    
    def get_status(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        return prop.get("status", {}).get("name")
    
    def get_select(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        return prop.get("select", {}).get("name")
    
    def get_multi_select(prop_name: str) -> List[str]:
        prop = props.get(prop_name, {})
        return [c["name"] for c in prop.get("multi_select", [])]
    
    def get_date(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        return prop.get("date", {}).get("start")
    
    def get_rich_text(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        if prop.get("rich_text") and len(prop["rich_text"]) > 0:
            return prop["rich_text"][0].get("plain_text")
        return None
    
    def get_url(prop_name: str) -> Optional[str]:
        prop = props.get(prop_name, {})
        return prop.get("url")

    return {
        "id": page["id"],
        "task": get_title("Task"),
        "status": get_status("Status"),
        "priority": get_select("Priority"),
        "category": get_multi_select("Category"),
        "due_date": get_date("Due Date"),
        "recurring": get_select("Recurring"),
        "notes": get_rich_text("Notes"),
        "url": get_url("URL"),
    }


@mcp.tool()
def list_tasks(status: Optional[str] = None) -> List[dict]:
    """获取任务列表，可选按状态过滤
    
    Args:
        status: 任务状态过滤，可选值: 'Not Started', 'In Progress', 'Waiting', 'Done', 'Cancelled'
    
    Returns:
        List[dict]: 任务列表，每个任务包含以下字段:
        - id: 任务ID
        - task: 任务名称
        - status: 任务状态
        - priority: 优先级 ('High', 'Medium', 'Low')
        - category: 分类列表 (['Work', 'Personal', 'Health', 'Shopping', 'Home', 'Education', 'Social', 'Errands'])
        - due_date: 截止日期
        - recurring: 重复周期 ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')
        - notes: 备注
        - url: 相关URL
    """
    endpoint = f"/databases/{DATABASE_ID}/query"
    data = {}
    
    if status:
        data["filter"] = {
            "property": "Status",
            "status": {"equals": status}
        }
    
    results = notion_request("POST", endpoint, data)
    return [page_to_task(p) for p in results["results"]]


@mcp.tool()
def create_task(
    task: str,
    status: str = "Not Started",
    priority: Optional[str] = None,
    category: Optional[List[str]] = None,
    due_date: Optional[str] = None,
    recurring: Optional[str] = None,
    notes: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """创建一个任务
    
    Args:
        task: 任务名称 (必需)
        status: 任务状态，默认 'Not Started'，可选值: 'Not Started', 'In Progress', 'Waiting', 'Done', 'Cancelled'
        priority: 优先级，可选值: 'High', 'Medium', 'Low'
        category: 分类列表，可选值: ['Work', 'Personal', 'Health', 'Shopping', 'Home', 'Education', 'Social', 'Errands']
        due_date: 截止日期，格式: YYYY-MM-DD
        recurring: 重复周期，可选值: 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly'
        notes: 备注信息
        url: 相关URL链接
    
    Returns:
        dict: 新创建的任务信息
    """
    endpoint = "/pages"
    
    properties = {
        "Task": {"title": [{"text": {"content": task}}]},
        "Status": {"status": {"name": status}},
        "Category": {"multi_select": [{"name": c} for c in (category or [])]},
    }
    
    if priority:
        properties["Priority"] = {"select": {"name": priority}}
    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}
    if recurring:
        properties["Recurring"] = {"select": {"name": recurring}}
    if notes:
        properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    if url:
        properties["URL"] = {"url": url}
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }
    
    new_page = notion_request("POST", endpoint, data)
    return page_to_task(new_page)


@mcp.tool()
def update_task(
    task_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[List[str]] = None,
    due_date: Optional[str] = None,
    recurring: Optional[str] = None,
    notes: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """更新一个任务
    
    Args:
        task_id: 任务ID (必需)
        status: 任务状态，可选值: 'Not Started', 'In Progress', 'Waiting', 'Done', 'Cancelled'
        priority: 优先级，可选值: 'High', 'Medium', 'Low'
        category: 分类列表，可选值: ['Work', 'Personal', 'Health', 'Shopping', 'Home', 'Education', 'Social', 'Errands']
        due_date: 截止日期，格式: YYYY-MM-DD
        recurring: 重复周期，可选值: 'Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly'
        notes: 备注信息
        url: 相关URL链接
    
    Returns:
        dict: 更新后的任务信息
    """
    endpoint = f"/pages/{task_id}"
    
    props = {}
    if status:
        props["Status"] = {"status": {"name": status}}
    if priority:
        props["Priority"] = {"select": {"name": priority}}
    if category:
        props["Category"] = {"multi_select": [{"name": c} for c in category]}
    if due_date:
        props["Due Date"] = {"date": {"start": due_date}}
    if recurring:
        props["Recurring"] = {"select": {"name": recurring}}
    if notes:
        props["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
    if url:
        props["URL"] = {"url": url}
    
    data = {"properties": props}
    updated_page = notion_request("PATCH", endpoint, data)
    return page_to_task(updated_page)


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """删除一个任务（实际上是归档）
    
    Args:
        task_id: 任务ID (必需)
    
    Returns:
        dict: 包含删除状态的信息
    """
    endpoint = f"/pages/{task_id}"
    data = {"archived": True}
    notion_request("PATCH", endpoint, data)
    return {"id": task_id, "deleted": True}


if __name__ == "__main__":
    mcp.run()
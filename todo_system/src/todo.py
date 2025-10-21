# 專案 - Todo 任務管理系統
# 這個模組提供了一個簡單的命令列任務管理工具
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 配置設定 - 定義專案路徑和資料檔案位置
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TASKS_FILE = DATA_DIR / "tasks.json"  # 任務資料檔案位置
DEFAULT_TASKS_DATA = {
    "tasks": [],
    "next_id": 1
}


class TodoManager:
    """任務管理器"""

    def __init__(self):
        """初始化任務管理器"""
        self.tasks_file = TASKS_FILE
        self._ensure_data_file()

    def _ensure_data_file(self):
        """確保資料檔案存在"""
        if not self.tasks_file.exists():
            self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data(DEFAULT_TASKS_DATA)

    def _load_data(self) -> Dict:
        """載入任務資料"""
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return DEFAULT_TASKS_DATA.copy()

    def _save_data(self, data: Dict):
        """儲存任務資料"""
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_task(self, title: str, description: str = "") -> Dict:
        """新增任務

        Args:
            title: 任務標題
            description: 任務描述（選填）

        Returns:
            新增的任務字典
        """
        data = self._load_data()

        task = {
            "id": data["next_id"],
            "title": title,
            "description": description,
            "completed": False
        }

        data["tasks"].append(task)
        data["next_id"] += 1

        self._save_data(data)
        return task

    def list_tasks(self, show_completed: bool = True) -> List[Dict]:
        """列出所有任務

        Args:
            show_completed: 是否顯示已完成的任務，預設為 True

        Returns:
            任務列表
        """
        data = self._load_data()
        tasks = data["tasks"]

        if not show_completed:
            # 過濾掉已完成的任務，只顯示進行中的
            tasks = [t for t in tasks if not t["completed"]]

        return tasks

    def get_task(self, task_id: int) -> Optional[Dict]:
        """取得特定任務"""
        data = self._load_data()

        for task in data["tasks"]:
            if task["id"] == task_id:
                return task

        return None

    def complete_task(self, task_id: int) -> bool:
        """標記任務為已完成"""
        data = self._load_data()

        for task in data["tasks"]:
            if task["id"] == task_id:
                task["completed"] = True
                self._save_data(data)
                return True

        return False

    def delete_task(self, task_id: int) -> bool:
        """刪除任務"""
        data = self._load_data()
        original_length = len(data["tasks"])

        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

        if len(data["tasks"]) < original_length:
            self._save_data(data)
            return True

        return False

    def get_task_stats(self) -> Dict:
        """取得任務統計資訊"""
        data = self._load_data()
        tasks = data["tasks"]

        total = len(tasks)
        completed = sum(1 for t in tasks if t["completed"])
        active = total - completed

        return {
            "total": total,
            "completed": completed,
            "active": active,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }


def print_task(task: Dict):
    """列印單一任務"""
    status = "[完成]" if task["completed"] else "[未完成]"
    print(f"{status} [{task['id']}] {task['title']}")
    if task.get("description"):
        print(f"   描述: {task['description']}")


def get_task_id_from_args() -> Optional[int]:
    """從命令列參數取得任務 ID"""
    if len(sys.argv) < 3:
        print("錯誤：請提供任務 ID")
        return None

    try:
        return int(sys.argv[2])
    except ValueError:
        print("錯誤：任務 ID 必須是數字")
        return None


def main():
    """主程式"""
    manager = TodoManager()

    if len(sys.argv) < 2:
        print("用法:")
        print("  uv run src/todo.py add <標題> [描述]    - 新增任務")
        print("  uv run src/todo.py list                 - 列出所有任務")
        print("  uv run src/todo.py list [--active]      - 列出未完成任務")
        print("  uv run src/todo.py complete <ID>        - 標記任務完成")
        print("  uv run src/todo.py delete <ID>          - 任務刪除")
        return

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("錯誤：請提供任務標題")
            return

        title = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""

        task = manager.add_task(title, description)
        print(f"已新增任務: [{task['id']}] {task['title']}")

    elif command == "list":
        show_completed = "--active" not in sys.argv
        tasks = manager.list_tasks(show_completed=show_completed)

        if not tasks:
            print("目前沒有任務")
        else:
            print(f"任務列表 (共 {len(tasks)} 個):")
            for task in tasks:
                print_task(task)

    elif command == "complete":
        task_id = get_task_id_from_args()
        if task_id is not None:
            if manager.complete_task(task_id):
                print(f"已完成任務: {task_id}")
            else:
                print(f"找不到任務: {task_id}")

    elif command == "delete":
        task_id = get_task_id_from_args()
        if task_id is not None:
            if manager.delete_task(task_id):
                print(f"已刪除任務: {task_id}")
            else:
                print(f"找不到任務: {task_id}")

    else:
        print(f"未知的指令: {command}")


if __name__ == "__main__":
    main()

# 測試 Notification Hook - 捕捉 JSON 範例資料

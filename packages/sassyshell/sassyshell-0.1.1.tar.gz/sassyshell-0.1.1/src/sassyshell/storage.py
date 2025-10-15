import json
from pathlib import Path
from .config import settings

def save_data(data: dict, path: Path):
    with open(path, "r") as f:
        content: list = json.load(f)

    for item in content:
        if data.get("generalized_command") == item.get("generalized_command"):
            item.get("statistics")["times_called"] += 1
            item.get("user_query").append(data.get("user_query")[0]) # type: ignore
            item["user_query"] = item.get("user_query")[-settings.max_history_size:] # type: ignore
            break
    else:
        content.append(data)

    with open(path, "w") as f:
        json.dump(content, f, indent=4)


def get_data(path: Path):
    if not Path(path).exists():
        Path(path).touch()
        Path(path).write_text("[]")
    
    with open(path, "r") as f:
        return json.load(f)
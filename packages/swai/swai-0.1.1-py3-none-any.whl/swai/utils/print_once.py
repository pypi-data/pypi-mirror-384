import hashlib
import os

def print_once_per_terminal(message):
    try:
        tty_path = os.ttyname(0)  # 标准输入所连接的 TTY；必要时可尝试 1 或 2
    except OSError:
        # 非交互环境（比如被重定向/cron）就直接返回或按需处理
        tty_path = "default-tty"
    
    session = os.getppid() or "default-session"
    env_items = ""
    env_keys = sorted(os.environ.keys())
    for key in env_keys:
        env_items += f"{key}={os.environ[key]};"
    key = f"{tty_path}-{session}-{env_items}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    base_dir = "/tmp"
    marker_dir = os.path.join(base_dir, "swai-cli")
    os.makedirs(marker_dir, exist_ok=True)
    marker_file = os.path.join(marker_dir, f"swai-cli-{key_hash}")
    
    if not os.path.exists(marker_file):
        with open(marker_file, "w") as f:
            f.write("")
        print(message)

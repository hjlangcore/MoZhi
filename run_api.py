"""
启动脚本 - 正确设置 Python 路径并启动应用
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from src.core.logging_config import setup_logging
    
    setup_logging()
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)

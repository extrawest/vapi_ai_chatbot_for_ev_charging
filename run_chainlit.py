import os
import sys
import subprocess
from pathlib import Path

from src.utils import setup_logger

logger = setup_logger(__name__)

def main():
    project_root = Path(__file__).parent

    sys.path.insert(0, str(project_root))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    chainlit_app_path = project_root / "src" / "ui" / "chainlit_app.py"

    if not chainlit_app_path.exists():
        logger.info(f"Error: Chainlit app not found at {chainlit_app_path}")
        sys.exit(1)

    cmd = ["chainlit", "run", str(chainlit_app_path), "--host", "0.0.0.0", "--port", "8001"]

    logger.info(f"Starting Chainlit UI at http://localhost:8001")
    logger.info(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        logger.info("\nStopping Chainlit UI...")
    except subprocess.CalledProcessError as e:
        logger.info(f"Error running Chainlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
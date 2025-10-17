import os
from pathlib import Path

CI_COMMIT_REF_NAME = os.environ.get("CI_COMMIT_REF_NAME", "local")
CI_COMMIT_SHA = os.environ.get("CI_COMMIT_SHA", "0000000000000000000000000000000000000000")
CI_COMMIT_SHORT_SHA = CI_COMMIT_SHA[0:8]
BASE_DIR = Path(__file__).resolve().parent

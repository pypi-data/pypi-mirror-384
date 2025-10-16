import multiprocessing
import os
from typing import Literal

PLATFORMS = Literal["illumina", "ont"]

CPU_COUNT = multiprocessing.cpu_count()

CLI_ACCESS_TOKEN = os.environ.get("CLI_ACCESS_TOKEN", None)

DEFAULT_HOST = os.environ.get("DEFAULT_HOST", "portal.gpas.global")
DEFAULT_APP_HOST = os.environ.get("DEFAULT_APP_HOST", "app.gpas.global")
DEFAULT_UPLOAD_HOST = os.environ.get("DEFAULT_UPLOAD_HOST", "api.upload.gpas.global")
DEFAULT_PROTOCOL = "https"
DEFAULT_COUNTRY: None = None
DEFAULT_DISTRICT = ""
DEFAULT_SUBDIVISION = ""
DEFAULT_INSTRUMENTPLATFORM = "illumina"
DEFAULT_PIPELINE = "mycobacteria"
DEFAULT_ONT_READ_SUFFIX = ".fastq.gz"
DEFAULT_ILLUMINA_READ1_SUFFIX = "_1.fastq.gz"
DEFAULT_ILLUMINA_READ2_SUFFIX = "_2.fastq.gz"
DEFAULT_ILLUMINA_READ1_SUFFIX_CLEAN = ".clean_1.fastq.gz"
DEFAULT_ILLUMINA_READ2_SUFFIX_CLEAN = ".clean_2.fastq.gz"
DEFAULT_MAX_BATCH_SIZE = 50

# For Login Handling
AUTH_DOMAIN = os.environ.get("AUTH_DOMAIN", "eit-pathogena-dev.uk.auth0.com")
AUTH_CLIENT_ID = os.environ.get(
    "AUTH_CLIENT_ID", "jDX7UUir4Vbzat3nKyyW2FACq2dRE7or"
)  # TODO(Michael): https://eit-oxford.atlassian.net/browse/EV-2328 PROD client id for this
AUTH_AUDIENCE = os.environ.get("AUTH_AUDIENCE", "https://portal.gpas.global")
AUTH_ISSUER = os.environ.get("AUTH_ISSUER", "https://account.portal.gpas.global")
ALGORITHMS = ["RS256"]


HOSTILE_INDEX_NAME = "human-t2t-hla-argos985-mycob140"

DEFAULT_CHUNK_SIZE = int(
    os.getenv("NEXT_PUBLIC_CHUNK_SIZE", 10 * 1000 * 1000)
)  # 10000000 = 10 mb

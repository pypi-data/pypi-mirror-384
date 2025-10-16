"""
This module contains the constants used in the application.
"""

import os
import logging

logger = logging.getLogger("constants")

PROJECT_ID = os.getenv("PROJECT_ID", None)
if PROJECT_ID is None:
    logging.debug("PROJECT_ID environment variable not set")

BUCKET_NAME = os.getenv("BUCKET_NAME", None)
if BUCKET_NAME is None:
    logging.debug("BUCKET_NAME environment variable not set")

FIRESTORE_DATABASE_INTERNAL = os.getenv("FIRESTORE_DATABASE_INTERNAL", None)
if FIRESTORE_DATABASE_INTERNAL is None:
    logging.debug("FIRESTORE_DATABASE_INTERNAL environment variable not set")

TOPIC_ID = os.getenv("TOPIC_ID", None)
if TOPIC_ID is None:
    logging.debug("TOPIC_ID environment variable not set")

FS_ORGANIZATION_COLLECTION = "organizations"
FS_USER_COLLECTION = "user"

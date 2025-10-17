"""
Copyright (c) 2010-present by Jaxl Innovations Private Limited.

All rights reserved.

Redistribution and use in source and binary forms,
with or without modification, is strictly prohibited.
"""

from enum import Enum


class V1CampaignListStatusItem(str, Enum):
    APPROVED = "APPROVED"
    FINISHED = "FINISHED"
    INITIALIZING = "INITIALIZING"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    RUNNING = "RUNNING"
    SCHEDULED = "SCHEDULED"
    STOPPED = "STOPPED"
    UNDER_REVIEW = "UNDER_REVIEW"

    def __str__(self) -> str:
        return str(self.value)

import json
from datetime import datetime

from imerit_ango.models.enums import ExportTypes, ExportFormats
from typing import List, Dict, Any, Optional


class TimeFilter:
    def __init__(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
        self.from_date = from_date
        self.to_date = to_date

    def toDict(self) -> Dict[str, Any]:
        if self.from_date and self.to_date:
            return {
                "$gt": f"{self.from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}",
                "$lt": f"{self.to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"
            }
        elif self.from_date:
            return {"$gt": f"{self.from_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"}
        elif self.to_date:
            return {"$lt": f"{self.to_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}"}
        return {}

    def to_json(self) -> str:
        return json.dumps(self.toDict())


class ExportOptions:
    def __init__(self,
                 stage: List[str] = ['Complete'],
                 batches: List[str] = None,
                 export_format: ExportFormats = ExportFormats.JSON,
                 export_type: ExportTypes = ExportTypes.TASK,
                 include_key_frames_only: bool = False,
                 include_idle_blur_durations: bool = False,
                 sendEmail: bool = False,
                 includeMetadata: bool = True,
                 includeHistory: bool = True,
                 doNotNotify: bool = True,
                 updated_at: TimeFilter = None,
                 created_at: TimeFilter = None
                 ):
        self.stage = stage
        self.batches = batches
        self.export_format = export_format
        self.export_type = export_type
        self.include_key_frames_only = include_key_frames_only
        self.sendEmail = sendEmail
        self.includeMetadata = includeMetadata
        self.includeHistory = includeHistory
        self.doNotNotify = doNotNotify
        self.updated_at = updated_at
        self.created_at = created_at
        self.include_idle_blur_durations = include_idle_blur_durations

    def toDict(self) -> Dict[str, Any]:
        result = {
            "sendEmail": str(self.sendEmail).lower(),
            "includeMetadata": str(self.includeMetadata).lower(),
            "includeHistory": str(self.includeHistory).lower(),
            "doNotNotify": str(self.doNotNotify).lower(),
            "format": self.export_format.value,
            "type": self.export_type.value,
            "includeOnlyKeyFrames": str(self.include_key_frames_only).lower(),
            "includeIdleBlurDurations": str(self.include_idle_blur_durations).lower()
        }
        if self.batches:
            result["batches"] = json.dumps(self.batches)
        if self.stage and self.export_type == ExportTypes.TASK:
            result["stage"] = json.dumps(self.stage)
        if self.updated_at:
            result["updatedAt"] = self.updated_at.to_json()
        if self.created_at:
            result["createdAt"] = self.created_at.to_json()

        return result

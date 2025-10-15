"""
Base models and utilities for the RBAC package
"""
from datetime import datetime
from django.db import models
from django.utils import timezone
from django_extensions.db.fields import ModificationDateTimeField
from pydantic.v1 import BaseModel, Extra


def get_current_dtm():
    """
    Get current datetime with timezone support
    
    Returns:
        datetime: Current datetime with timezone awareness
    """
    try:
        return timezone.localtime(timezone.now())
    except Exception:
        return datetime.now()


class DefaultTimeStamp(models.Model):
    """
    Abstract base model providing consistent timestamp fields
    """
    created_dtm = models.DateTimeField(default=get_current_dtm)
    updated_dtm = ModificationDateTimeField()

    class Meta:
        abstract = True


class ForbidExtra(BaseModel):
    """
    Pydantic base model that forbids extra fields
    """
    class Config:
        extra = Extra.forbid
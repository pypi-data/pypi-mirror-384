from django.db import models
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings as settings_raw
from rest_framework import fields as serializer_fields

from .fields import (
    ForeignKey,
    ManyToManyField,
    OneToOneField,
    DecimalField,
    IntegerField,
    CharField,
    TextField,
    EmailField,
    DateField,
    DateTimeField,
    FileField,
    ImageField,
    TypedSerializerMethodField,
    BooleanField,
    ArrayField,
)
from .patches import run_patches

run_patches()

settings = settings_raw.__dict__
settings["APPS"] = ["main"]
if getattr(settings_raw, "DRF_REACT_BY_SCHEMA", None):
    settings["APPS"] = settings_raw.DRF_REACT_BY_SCHEMA.get("APPS", ["main"])

__all__ = [
    "ForeignKey",
    "ManyToManyField",
    "OneToOneField",
    "DecimalField",
    "IntegerField",
    "CharField",
    "TextField",
    "EmailField",
    "DateField",
    "DateTimeField",
    "FileField",
    "ImageField",
    "TypedSerializerMethodField",
    "BooleanField",
    "ArrayField",
]

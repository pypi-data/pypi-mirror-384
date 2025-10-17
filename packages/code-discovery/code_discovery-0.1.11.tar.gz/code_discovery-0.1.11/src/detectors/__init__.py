"""Framework detector modules."""

from detectors.base import BaseDetector
from detectors.java_spring import SpringBootDetector
from detectors.java_micronaut import MicronautDetector
from detectors.python_fastapi import FastAPIDetector
from detectors.python_flask import FlaskDetector
from detectors.dotnet import DotNetDetector

__all__ = [
    "BaseDetector",
    "SpringBootDetector",
    "MicronautDetector",
    "FastAPIDetector",
    "FlaskDetector",
    "DotNetDetector",
]


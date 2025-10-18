"""Sparv plugin for annotating sentences with emotional classification."""

from sparv import api as sparv_api

from sbx_emotions_kb_emoclass.annotations import annotate_sentence
from sbx_emotions_kb_emoclass.constants import PROJECT_NAME

__all__ = ["annotate_sentence"]


__description__ = "Annotate sentences with emotional classification."
__version__ = "0.1.0"

__config__ = [
    sparv_api.Config(
        f"{PROJECT_NAME}.annotation_lang",
        description="The language to use in the annotations, currently 'en' or 'sv'.",
        default=None,
    )
]

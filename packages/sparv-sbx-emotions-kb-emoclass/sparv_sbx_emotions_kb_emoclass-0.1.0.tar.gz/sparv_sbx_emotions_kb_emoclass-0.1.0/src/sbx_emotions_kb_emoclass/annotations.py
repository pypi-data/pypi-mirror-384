"""Annotations for emotional classification."""

from sparv import api as sparv_api  # type: ignore [import-untyped]

from sbx_emotions_kb_emoclass.constants import PROJECT_NAME

logger = sparv_api.get_logger(__name__)

SEP_TOKEN: str = " "


@sparv_api.annotator("Emotional classification of sentences", language=["swe"])
def annotate_sentence(
    out_sentence_emotions: sparv_api.Output = sparv_api.Output(
        f"<sentence>:{PROJECT_NAME}.sentence-emotion--kb-emoclass",
        description="Emotional analysis of sentence with KBLab/emotional-classification",
    ),
    word: sparv_api.Annotation = sparv_api.Annotation("<token:word>"),
    sentence: sparv_api.Annotation = sparv_api.Annotation("<sentence>"),
    annotation_lang: str | None = sparv_api.Config(f"{PROJECT_NAME}.annotation_lang"),
) -> None:
    """Sentiment analysis of sentence with KBLab/robust-swedish-sentiment-multiclass."""
    from sbx_emotions_kb_emoclass.emotional_classifier import (  # noqa: PLC0415
        EmotionalClassifier,
    )

    try:
        classifier = EmotionalClassifier(lang=annotation_lang)
    except ValueError as exc:
        raise sparv_api.SparvErrorMessage(
            f"'{PROJECT_NAME}.annotation_lang' got an unrecognized value: '{annotation_lang}'"
        ) from exc
    sentences, _orphans = sentence.get_children(word)
    token_word = list(word.read())
    out_sentence_emotions_annotation = sentence.create_empty_attribute()

    logger.progress(total=len(sentences))  # type: ignore
    for sent_i, sent in enumerate(sentences):
        sent_to_tag = SEP_TOKEN.join([token_word[token_index] for token_index in sent])
        out_sentence_emotions_annotation[sent_i] = classifier.predict_emotion_sentence(
            sent_to_tag
        )
        logger.debug("annotation[%d]=%s", sent_i, out_sentence_emotions_annotation[sent_i])

    out_sentence_emotions.write(out_sentence_emotions_annotation)

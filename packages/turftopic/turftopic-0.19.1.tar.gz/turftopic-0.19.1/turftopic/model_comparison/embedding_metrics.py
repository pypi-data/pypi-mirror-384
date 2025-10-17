import itertools
import warnings
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
from rich.console import Console
from rich.table import Table
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from turftopic.base import Encoder
from turftopic.container import TopicContainer
from turftopic.encoders.multimodal import MultimodalEncoder
from turftopic.multimodal import (
    ImageRepr,
    MultimodalEmbeddings,
    _load_images,
    encode_multimodal,
)


def encode_texts(encoder, texts: list[str]) -> np.ndarray:
    if hasattr(encoder, "get_text_embeddings"):
        return encoder.get_text_embeddings(texts)
    return encoder.encode(texts)


def encode_images(encoder, images: list[ImageRepr]):
    images = list(_load_images(images))
    if hasattr(encoder, "get_image_embeddings"):
        return encoder.get_image_embeddings(images)
    return encoder.encode(images)


def _topic_distances(embeddings: np.ndarray, labels: np.ndarray) -> np.ndarray:
    topic_embeddings = [
        embeddings[labels == label] for label in np.unique(labels)
    ]
    topic_dist = []
    for i_topic, j_topic in itertools.combinations(
        np.arange(len(topic_embeddings)), 2
    ):
        dist = 1 - cosine_similarity(
            topic_embeddings[i_topic], topic_embeddings[j_topic]
        )
        topic_dist.append(np.mean(dist))
    return np.array(topic_dist)


def _topic_coherences(
    embeddings: np.ndarray, labels: np.ndarray
) -> np.ndarray:
    sims = []
    for label in np.unique(labels):
        topic_embeddings = embeddings[labels == label]
        sim = cosine_similarity(topic_embeddings, topic_embeddings)
        sim[np.triu_indices(sim.shape[0], 0)] = np.nan
        sims.append(np.nanmean(sim))
    return np.array(sims)


def _topic_coverage(
    desc_embeddings: np.ndarray, document_embeddings: np.ndarray
) -> np.ndarray:
    sim = cosine_similarity(document_embeddings, desc_embeddings)
    # Selecting the maximally similar description item to a document
    max_sim = np.max(sim, axis=1)
    return max_sim


def _encode_descriptives(
    encoder, data: TopicContainer, top_k: int
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Encodes descriptive words, documents and images."""
    top_words = data.get_top_words(top_k=top_k)
    top_documents = data.get_top_documents(top_k=top_k)
    embeddings = defaultdict(list)
    labels = defaultdict(list)
    n_topics = len(top_words)
    try:
        classes = data.classes_
    except AttributeError:
        classes = list(range(n_topics))
    for topic_id, words, docs in zip(classes, top_words, top_documents):
        if topic_id == -1:
            # Skipping outlier topic
            continue
        embeddings["words"].extend(encode_texts(encoder, words))
        labels["words"].extend([topic_id] * len(words))
        embeddings["documents"].extend(encode_texts(encoder, docs))
        labels["documents"].extend([topic_id] * len(docs))
    try:
        top_images = data.get_top_images(top_k=top_k)
        for topic_id, images in zip(classes, top_images):
            if topic_id == -1:
                # Skipping outlier topic
                continue
            try:
                embeddings["images"].extend(encode_images(encoder, images))
            except Exception as e:
                warnings.warn(
                    f"Couldn't encode images due to error: {e}, proceeding without image encoding."
                )
            labels["images"].extend([topic_id] * len(images))
    except Exception:
        warnings.warn("No images, proceeding without them.")
        pass
    embeddings = {key: np.array(emb) for key, emb in embeddings.items()}
    labels = {key: np.array(lab) for key, lab in labels.items()}
    return embeddings, labels


@dataclass
class EvaluationResult:
    res: dict[str, dict[str, np.ndarray]]

    @property
    def modalities(self) -> set[str]:
        return set(self.res.keys())

    @property
    def coherence(self) -> float:
        all_scores = []
        for modality in self.res:
            all_scores.extend(self.res[modality]["coherence"])
        return np.mean(all_scores)

    @property
    def diversity(self) -> float:
        all_scores = []
        for modality in self.res:
            all_scores.extend(self.res[modality]["diversity"])
        return np.mean(all_scores)

    @property
    def interpretability(self) -> float:
        return np.sqrt(self.coherence * self.diversity)

    @property
    def coverage(self) -> float:
        all_scores = []
        for modality in self.res:
            all_scores.extend(self.res[modality]["coverage"])
        return np.mean(all_scores)

    def _summary_table(self):
        index = []
        cols = ["coherence", "diversity", "coverage"]
        rows = []
        for modality in self.res:
            row = []
            for metric in cols:
                row.append(np.mean(self.res[modality][metric]))
            rows.append(row)
            index.append(modality)
        return index, cols, rows

    def __str__(self) -> str:
        index, cols, rows = self._summary_table()
        table = Table(show_lines=True)
        table.add_column("Modality")
        for column in cols:
            table.add_column(column.capitalize())
        for ind, row in zip(index, rows):
            row = [f"{val:.2f}" for val in row]
            table.add_row(ind.capitalize(), *row)
        console = Console()
        with console.capture() as capture:
            console.print(table)
        return capture.get()

    def summary_df(self):
        try:
            import pandas as pd
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "You should install pandas before using dataframe utilities in Turftopic."
            ) from e
        index, cols, rows = self._summary_table()
        return pd.DataFrame(rows, columns=cols, index=index)


class Evaluator:
    def __init__(
        self,
        top_k: int = 10,
        encoder: Union[Encoder, MultimodalEncoder, str] = "all-MiniLM-L6-v2",
    ):
        self.encoder = encoder
        if isinstance(self.encoder, str):
            self.encoder_ = SentenceTransformer(self.encoder)
        else:
            self.encoder_ = self.encoder
        self.top_k = top_k

    def evaluate(
        self,
        data: TopicContainer,
        embeddings: Optional[Union[np.ndarray, MultimodalEmbeddings]] = None,
    ):
        res = defaultdict(dict)
        if embeddings is None:
            if hasattr(data, "images"):
                embeddings = encode_multimodal(
                    self.encoder_, data.corpus, data.images
                )
                document_embeddings = embeddings["document_embeddings"]
            else:
                document_embeddings = encode_texts(self.encoder_, data.corpus)
        elif isinstance(embeddings, dict):
            document_embeddings = embeddings["document_embeddings"]
        else:
            document_embeddings = embeddings
        desc_embeddings, labels = _encode_descriptives(
            self.encoder_, data, self.top_k
        )
        for modality in desc_embeddings:
            coherence = _topic_coherences(
                desc_embeddings[modality], labels[modality]
            )
            res[modality]["coherence"] = coherence
            diversity = _topic_distances(
                desc_embeddings[modality], labels[modality]
            )
            res[modality]["diversity"] = diversity
            coverage = _topic_coverage(
                desc_embeddings[modality], document_embeddings
            )
            res[modality]["coverage"] = coverage
        return EvaluationResult(res)


def compare_models(results: list[EvaluationResult]):
    import pandas as pd
    import statsmodels.formula.api as smf

    modalities = set(results[0])

    records = []
    for modality in ["words", "documents"]:
        for i, _res in enumerate(eval_res):
            for score in _res.res[modality]["coverage"]:
                records.append(
                    dict(model=f"Model {i}", modality=modality, score=score)
                )
    df = pd.DataFrame.from_records(records)
    rand_eff_mod = smf.ols(
        formula="score ~ C(model)",
        data=df,
        groups=df["modality"],
    )
    reg_res = rand_eff_mod.fit()
    reg_res.summary()

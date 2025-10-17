import warnings
from typing import Optional

import numpy as np
import torch
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import trange
from transformers import AutoTokenizer, BertModel


class ColBERTKeywordExtractor:
    def __init__(
        self,
        top_n: int,
        model_name: str,
        vectorizer: CountVectorizer,
        batch_size: int = 32,
    ):
        self.top_n = top_n
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.vectorizer = vectorizer
        self.batch_size = batch_size
        self.key_to_index: dict[str, int] = {}
        self.term_embeddings: Optional[np.ndarray] = None

    def encode_batch(self, sentences: list[str]) -> list[np.ndarray]:
        with torch.no_grad():
            inputs = self.tokenizer(
                sentences, return_tensors="pt", padding=True
            )
            outputs = self.model(**inputs)
        hidden_state = outputs.last_hidden_state
        embeddings = []
        for h, m in zip(hidden_state, inputs["attention_mask"]):
            embeddings.append(h[m > 0].numpy())
        return embeddings

    @property
    def vocab(self) -> np.ndarray:
        res = [""] * self.n_vocab
        for key, index in self.key_to_index.items():
            res[index] = key
        return np.array(res)

    @property
    def n_vocab(self) -> int:
        return len(self.key_to_index)

    def _add_terms(self, new_terms: list[str]):
        for term in new_terms:
            self.key_to_index[term] = self.n_vocab
        term_encodings = self.encode_batch(new_terms)
        term_encodings = np.stack(
            [np.mean(_t, axis=0) for _t in term_encodings]
        )
        if self.term_embeddings is not None:
            self.term_embeddings = np.concatenate(
                (self.term_embeddings, term_encodings), axis=0
            )
        else:
            self.term_embeddings = term_encodings

    def batch_extract_keywords(
        self,
        documents: list[str],
        embeddings: Optional[np.ndarray] = None,
        seed_embedding: Optional[np.ndarray] = None,
        fitting: bool = True,
    ) -> list[dict[str, float]]:
        if not len(documents):
            return []
        if embeddings is not None:
            warnings.warn(
                "embeddings parameter specified, but get ignored when using ColBERT."
            )
        keywords = []
        if fitting:
            document_term_matrix = self.vectorizer.fit_transform(documents)
        else:
            document_term_matrix = self.vectorizer.transform(documents)
        batch_vocab = self.vectorizer.get_feature_names_out()
        new_terms = list(set(batch_vocab) - set(self.key_to_index.keys()))
        if len(new_terms):
            self._add_terms(new_terms)
        for i in trange(
            0, len(documents), self.batch_size, desc="Extracting keywords"
        ):
            _docs = documents[i : i + self.batch_size]
            _embs = self.encode_batch(_docs)
            for j in range(0, self.batch_size):
                terms = document_term_matrix[i + j, :].todense()
                mask = terms > 0
                if not np.any(mask):
                    keywords.append(dict())
                    continue
                important_terms = np.ravel(np.asarray(mask))
                word_embeddings = [
                    self.term_embeddings[self.key_to_index[term]]
                    for term in batch_vocab[important_terms]
                ]
                sim = cosine_similarity(word_embeddings, _embs[j])
                maxsim = np.max(sim, axis=1)
                kth = min(self.top_n, len(maxsim) - 1)
                top = np.argpartition(-maxsim, kth)[:kth]
                top_words = batch_vocab[important_terms][top]
                top_sims = [sim for sim in maxsim[top] if sim > 0]
                keywords.append(dict(zip(top_words, top_sims)))
        return keywords

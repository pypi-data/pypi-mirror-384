import json
import logging
import os
import random
from typing import Any, Iterator

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm, trange
from sortedcontainers import SortedSet

from search_index.base import SearchIndex
from search_index._internal import IndexData


def select_faiss_index(d: int, n: int) -> tuple[str, faiss.Index]:
    """

    Selects the appropriate Faiss index for the given number of
    dimensions and datapoints.

    """
    if n < 1_000_000:
        return "Flat", faiss.IndexIDMap2(
            faiss.index_factory(d, "Flat", faiss.METRIC_INNER_PRODUCT)
        )

    n_clusters = round(4 * n**0.5)
    index = f"IVF{n_clusters}"
    if n_clusters >= 2**16:
        # use HNSW32 instead of flat quantizer for large number of clusters
        index += "_HNSW32"
    index += ",Flat"
    return index, faiss.index_factory(d, index, faiss.METRIC_INNER_PRODUCT)


def select_faiss_binary_index(d: int, n: int) -> tuple[str, faiss.IndexBinary]:
    """

    Selects the appropriate Faiss binary index for the given number of datapoints.

    """
    # remove True here once search parameters for IVF binary indices are implemented
    if True or n < 1_000_000:
        return "BFlat", faiss.IndexBinaryIDMap2(faiss.index_binary_factory(d, "BFlat"))

    n_clusters = round(4 * n**0.5)
    index = f"BIVF{n_clusters}"
    if n_clusters >= 2**16:
        # use HNSW32 instead of flat quantizer for large number of clusters
        index += "_HNSW32"
    return index, faiss.index_binary_factory(d, index)


class EmbeddingModel:
    def __init__(self, model: str, device: str | None = None):
        self.model = model
        self.encoder = SentenceTransformer(model, device=device)
        self.dim: int = self.encoder.get_sentence_embedding_dimension()  # type: ignore
        assert self.dim is not None, "unable to get embedding dimension"

    def same_as(self, model: str) -> bool:
        return self.model == model

    def embed(
        self,
        texts: list[str],
        precision: str = "float32",
        embedding_dim: int | None = None,
        batch_size: int | None = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        assert precision in ["float32", "ubinary"], f"invalid precision {precision}"

        if embedding_dim and embedding_dim < self.dim:
            dim = embedding_dim
        else:
            dim = self.dim

        if precision == "ubinary":
            assert dim % 8 == 0, "embedding dimension must be a multiple of 8"
            dim = dim // 8

        if not texts:
            return np.empty((0, dim))

        if batch_size is None:
            batch_size = len(texts)

        # sort texts by length to minimize padding
        indices = np.argsort([-len(text) for text in texts])
        sorted_texts = [texts[i] for i in indices]
        full_embeddings = []
        # doing our own loop here because sentence transformers
        # only converts to target precision at the end, which
        # might OOM for large datasets
        for i in trange(
            0,
            len(sorted_texts),
            batch_size,
            desc="Calculating embeddings",
            disable=not show_progress,
        ):
            batch = sorted_texts[i : i + batch_size]
            embeddings = self.encoder.encode(  # type: ignore
                batch,
                normalize_embeddings=True,
                batch_size=len(batch),
                precision=precision,  # type: ignore
                show_progress_bar=False,
            )[:, :dim]
            full_embeddings.extend(embeddings)

        embeddings = np.vstack(full_embeddings)
        inv_indices = np.argsort(indices)
        # make sure inv indices correctly restores the original order
        assert all(t == sorted_texts[i] for t, i in zip(texts, inv_indices))
        return embeddings[inv_indices]


def get_index_from_id(id: int, id_per_index: list[int]) -> int:
    # id to index stores the first id for each index
    # so we can do a binary search to find the index
    # for a given id
    left = 0
    right = len(id_per_index)
    answer = -1
    while left < right:
        mid = (left + right) // 2

        if id < id_per_index[mid]:
            right = mid
        else:
            answer = mid
            left = mid + 1

    assert answer >= 0
    return answer


def get_column_from_id(id: int, id_per_index: list[int]) -> int:
    index = get_index_from_id(id, id_per_index)
    first_id = id_per_index[index]
    return id - first_id + 1  # +1 because first column is identifier


class SimilarityIndex(SearchIndex):
    def __init__(
        self,
        model: EmbeddingModel,
        data: IndexData,
        index: faiss.Index,
        config: dict[str, Any],
        id_per_index: list[int],
        subset: SortedSet | None = None,
    ) -> None:
        self.model = model
        self.data = data
        self.index = index
        self.config = config
        self.id_per_index = id_per_index
        self.subset = subset

    @staticmethod
    def build(
        data: IndexData,
        index_dir: str,
        model: str | None = None,
        embedding_dim: int | None = None,
        batch_size: int = 32,
        device: str = "cuda",
        train_on_gpu: bool = False,
        precision: str | None = None,
        show_progress: bool = False,
        **kwargs: Any,
    ) -> None:
        """

        Builds the index from the given file and saves
        it in the index dir.

        """
        logger = logging.getLogger("SIMILARITY INDEX BUILD")

        def data_iter() -> Iterator[tuple[int, int, str]]:
            id = 0
            for i, (_, *texts) in enumerate(data):
                for text in texts:
                    yield id, i, text
                    id += 1

        # calculate index size
        id_per_index = []
        last = None
        index_size = 0
        for id, index, _ in data_iter():
            if last is None or index != last:
                id_per_index.append(id)
                last = index
            index_size += 1

        assert len(id_per_index) == len(data)

        # set some sensible defaults
        if precision is None:
            # set precision based on index size
            precision = "float32" if index_size < 1_000_000 else "ubinary"

        if model is None:
            model = "Qwen/Qwen3-Embedding-0.6B"

        emb_model = EmbeddingModel(model, device)

        if precision == "float32":
            index_name, index = select_faiss_index(emb_model.dim, index_size)
        else:
            index_name, index = select_faiss_binary_index(emb_model.dim, index_size)

        if show_progress:
            logger.info(
                f"Building a {index_name} index for {len(data):,} records "
                f"with a total of {index_size:,} entries"
            )

        added_ids = set()
        if "IVF" in index_name:
            if faiss.get_num_gpus() > 0 and train_on_gpu:
                if show_progress:
                    logger.info(
                        f"Setting up clustering index on {faiss.get_num_gpus()} GPUs "
                        "for training"
                    )
                try:
                    ci = faiss.index_cpu_to_all_gpus(faiss.IndexFlatIP(index.d))
                    index.clustering_index = ci
                except Exception as e:
                    logger.error(f"Failed to move clustering index to GPUs: {e}")

            train_size = min(
                index_size,
                round(1.1 * index.cp.min_points_per_centroid * index.nlist),
            )
            train_factor = train_size / index_size
            data_samples = int(train_factor * len(data))

            train_ids = random.sample(range(index_size), data_samples)
            train_texts = []
            for id in tqdm(
                train_ids,
                desc="Getting train data",
                total=data_samples,
                disable=not show_progress,
            ):
                index = get_index_from_id(id, id_per_index)
                row = data.get_row(index)
                column = get_column_from_id(id, id_per_index)
                text = row[column]
                train_texts.append(text)

            train_embeddings = emb_model.embed(
                train_texts,
                precision=precision,
                embedding_dim=embedding_dim,
                batch_size=batch_size,
                show_progress=show_progress,
            )

            if show_progress:
                logger.info(
                    f"Training {index_name} index with {index.nlist:,} clusters on "
                    f"{len(train_embeddings):,} embeddings from {data_samples:,} records"
                )
            index.train(train_embeddings)

            # add train embeddings to index
            index.add_with_ids(train_embeddings, train_ids)
            added_ids.update(train_ids)

        if len(added_ids) < len(data):
            index_ids = []
            index_texts = []
            for id, _, text in tqdm(
                data_iter(),
                desc="Getting index data",
                total=len(data),
                disable=not show_progress,
            ):
                if id in added_ids:
                    continue

                index_ids.append(id)
                index_texts.append(text)

            embeddings = emb_model.embed(
                index_texts,
                precision=precision,
                embedding_dim=embedding_dim,
                batch_size=batch_size,
                show_progress=show_progress,
            )
            index.add_with_ids(embeddings, index_ids)

        os.makedirs(index_dir, exist_ok=True)
        index_file = os.path.join(index_dir, "faiss.index")
        if precision == "float32":
            faiss.write_index(index, index_file)
        else:
            faiss.write_index_binary(index, index_file)

        id_per_index_file = os.path.join(index_dir, "index.id-per-index")
        id_per_index_np = np.array(id_per_index, dtype=np.uint32)
        id_per_index_np.tofile(id_per_index_file)

        with open(os.path.join(index_dir, "config.json"), "w") as f:
            json.dump(
                {
                    "index_name": index_name,
                    "model": model,
                    "precision": precision,
                    "embedding_dim": embedding_dim,
                },
                f,
            )

    @staticmethod
    def load(
        data: IndexData,
        index_dir: str,
        model: EmbeddingModel | None = None,
        device: str = "cuda",
    ) -> "SimilarityIndex":
        """

        Loads the index from the given data file and index directory.

        """
        with open(os.path.join(index_dir, "config.json")) as f:
            config = json.load(f)

        index_file = os.path.join(index_dir, "faiss.index")
        if config["precision"] == "float32":
            index = faiss.read_index(index_file)
        else:
            index = faiss.read_index_binary(index_file)

        if not torch.cuda.is_available():
            # for inference, fall back to CPU if no GPU is available
            device = "cpu"

        if model is None or not model.same_as(config["model"]):
            model = EmbeddingModel(model=config["model"], device=device)

        id_per_index_file = os.path.join(index_dir, "index.id-per-index")
        id_per_index_np = np.fromfile(id_per_index_file, dtype=np.uint32)
        id_per_index = id_per_index_np.tolist()

        return SimilarityIndex(model, data, index, config, id_per_index)

    def find_matches(
        self,
        query: str,
        k: int = 100,
        min_score: float | None = None,
        nprobe: int = 10,
    ) -> list[tuple[int, float, int]]:
        """

        Returns a sorted list of tuples containing ID, score,
        and corresponding value column for all matches for the given query.

        """
        # we want to scale k because we might have ids in the top k
        # results that point to the same data point, in which case
        # we get less than k unique results; this is an approximation
        # to scale k based on the number of indexed vectors per data point
        k_factor = self.index.ntotal / max(1, len(self.data))
        # scale also by 2 to be sure
        k_scaled = round(k * k_factor * 2)

        if self.subset is not None:
            # subset contains ids, but we need to convert to index
            # internal ids for the selector
            sub_ids = []
            for index in self.subset:
                first_id = self.id_per_index[index]
                if index + 1 < len(self.id_per_index):
                    last_id = self.id_per_index[index + 1]
                else:
                    last_id = self.index.ntotal
                sub_ids.extend(range(first_id, last_id))

            selector = faiss.IDSelectorBatch(sub_ids)
        else:
            selector = None

        name = self.config["index_name"]
        is_ivf = "IVF" in name
        is_binary = name.startswith("B")
        assert is_binary == (self.config["precision"] == "ubinary"), (
            "Model and index mismatch"
        )

        search_kwargs = {}
        if is_ivf:
            # ivf float index
            search_kwargs["params"] = faiss.SearchParametersIVF(
                sel=selector, nprobe=nprobe
            )
        else:
            # flat float index
            search_kwargs["params"] = faiss.SearchParameters(sel=selector)

        query_embeddings = self.model.embed(
            [query],
            precision=self.config["precision"],
            embedding_dim=self.config["embedding_dim"],
        )
        scores, ids = self.index.search(query_embeddings, k_scaled, **search_kwargs)
        dim = query_embeddings.shape[1] * (8 if is_binary else 1)

        # deduplicate based on index, not id
        seen = set()
        deduped = []
        for score, id in zip(scores[0], ids[0]):
            if id < 0:
                break
            elif len(deduped) >= k:
                break

            index = get_index_from_id(id, self.id_per_index)
            if index in seen:
                continue

            if is_binary:
                # convert binary index score to [0, 1] range to more
                # align with cosine-similarity for float indices
                # (even though cosine-similarity can be [-1, 1])
                score = (dim - score) / dim

            if min_score is not None and score < min_score:
                # break because scores are sorted
                break

            seen.add(index)

            column = get_column_from_id(id, self.id_per_index)
            deduped.append((index, score, column))

        return deduped

    def get_identifier(self, id: int) -> str:
        """

        Returns the identifier for the given ID.

        """
        return self.data.get_val(id, 0)

    def get_name(self, id: int) -> str:
        """

        Returns the name for the given ID.

        """
        return self.data.get_val(id, 1)

    def get_row(self, id: int) -> str:
        """

        Returns the line from the data file for the given ID.
        ID must be between 0 and the index length.

        """
        return self.data.get_row(id)

    def get_val(self, id: int, col: int) -> str:
        """

        Returns the column value for the given ID.

        """
        return self.data.get_val(id, col)

    def sub_index_by_ids(self, ids: list[int]) -> "SimilarityIndex":
        """

        Creates a sub-index containing only the given IDs.

        """
        assert all(0 <= id < len(self.data) for id in ids), "invalid ID in ID list"
        if self.subset is not None:
            subset = self.subset.intersection(ids)
        else:
            subset = SortedSet(ids)

        return SimilarityIndex(
            self.model,
            self.data,
            self.index,
            self.config,
            self.id_per_index,
            subset,
        )

    def __len__(self) -> int:
        """

        Returns the number of items in the index.

        """
        if self.subset is not None:
            return len(self.subset)
        else:
            return len(self.data)

    def __iter__(self) -> Iterator[list[str]]:
        """

        Iterates over the index data.

        """
        if self.subset is not None:
            for id in self.subset:
                yield self.data.get_row(id)
        else:
            yield from self.data

    def get_type(self) -> str:
        """

        Returns the type of the index.

        """
        return "similarity"

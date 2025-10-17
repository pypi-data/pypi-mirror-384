import sys
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

from corvic import result


def _validate_embedding_array(
    embeddings: NDArray[Any],
) -> result.Ok[None] | result.InvalidArgumentError:
    embeddings_ndim = 2
    if embeddings.ndim != embeddings_ndim:
        return result.InvalidArgumentError(
            f"embeddings ndim must be {embeddings_ndim}",
            ndim=embeddings.ndim,
        )
    if not np.issubdtype(embeddings.dtype, np.number):
        return result.InvalidArgumentError(
            "embeddings must have a numerical dtype",
            dtype=str(embeddings.dtype),
        )
    return result.Ok(None)


class DimensionReducer(Protocol):
    def reduce_dimensions(
        self, vectors: NDArray[Any], output_dimensions: int, metric: str
    ) -> result.Ok[NDArray[Any]] | result.InvalidArgumentError: ...


class UmapDimensionReducer(DimensionReducer):
    def reduce_dimensions(
        self,
        vectors: NDArray[Any],
        output_dimensions: int,
        metric: str,
    ) -> result.Ok[NDArray[Any]] | result.InvalidArgumentError:
        match _validate_embedding_array(vectors):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass

        vectors = np.nan_to_num(vectors.astype(np.float32))
        if vectors.shape[1] == output_dimensions:
            return result.Ok(vectors)
        n_neighbors = 15
        init = "spectral"
        # y spectral initialization cannot be used when n_neighbors
        # is greater or equal to the number of samples
        if vectors.shape[0] <= n_neighbors:
            init = "random"
            # n_neighbors is larger than the dataset size; truncating to X.shape[0] - 1
            n_neighbors = vectors.shape[0] - 1

        if vectors.shape[0] <= output_dimensions + 1:
            init = "random"

        # import umap locally to reduce loading time
        # TODO(Hunterlige): Replace with lazy_import
        try:
            from umap import umap_ as umap
        except ImportError as exc:
            raise ImportError("corvic-engine[ml] required") from exc

        projector = umap.UMAP(
            n_neighbors=n_neighbors,
            n_components=output_dimensions,
            metric=metric,
            init=init,
            low_memory=False,
            verbose=False,
            tqdm_kwds={"file": sys.stdout},
        )
        return result.Ok(projector.fit_transform(vectors))


class TruncateDimensionReducer(DimensionReducer):
    def reduce_dimensions(
        self, vectors: NDArray[Any], output_dimensions: int, metric: str
    ) -> result.Ok[NDArray[Any]] | result.InvalidArgumentError:
        match _validate_embedding_array(vectors):
            case result.InvalidArgumentError() as err:
                return err
            case result.Ok():
                pass
        return result.Ok(vectors[:, :output_dimensions])

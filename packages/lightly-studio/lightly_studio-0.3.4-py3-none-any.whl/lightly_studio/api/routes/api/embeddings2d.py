"""Routes delivering 2D embeddings for visualization."""

from __future__ import annotations

import io
from uuid import UUID

import numpy as np
import pyarrow as pa
from fastapi import APIRouter, HTTPException, Response
from numpy.typing import NDArray
from pyarrow import ipc
from pydantic import BaseModel, Field
from sklearn.manifold import TSNE
from sqlmodel import select

from lightly_studio.db_manager import SessionDep
from lightly_studio.models.dataset import DatasetTable
from lightly_studio.models.embedding_model import EmbeddingModelTable
from lightly_studio.resolvers import sample_embedding_resolver, sample_resolver
from lightly_studio.resolvers.samples_filter import SampleFilter

embeddings2d_router = APIRouter()


class GetEmbeddings2DRequest(BaseModel):
    """Request body for retrieving 2D embeddings."""

    filters: SampleFilter | None = Field(
        None,
        description="Filter parameters identifying matching samples",
    )


@embeddings2d_router.post("/embeddings2d/tsne")
def get_embeddings2d__tsne(
    session: SessionDep,
    body: GetEmbeddings2DRequest | None = None,
) -> Response:
    """Return 2D embeddings serialized as an Arrow stream."""
    # TODO(Malte, 09/2025): Support choosing the dataset via API parameter.
    dataset = session.exec(select(DatasetTable).limit(1)).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="No dataset configured.")

    # TODO(Malte, 09/2025): Support choosing the embedding model via API parameter.
    embedding_model = session.exec(
        select(EmbeddingModelTable)
        .where(EmbeddingModelTable.dataset_id == dataset.dataset_id)
        .limit(1)
    ).first()
    if embedding_model is None:
        raise HTTPException(status_code=404, detail="No embedding model configured.")

    embeddings = sample_embedding_resolver.get_all_by_dataset_id(
        session=session,
        dataset_id=dataset.dataset_id,
        embedding_model_id=embedding_model.embedding_model_id,
    )

    embedding_values = np.asarray([e.embedding for e in embeddings], dtype=np.float32)
    embedding_values_tsne = _calculate_tsne_embeddings(embedding_values)
    x = embedding_values_tsne[:, 0]
    y = embedding_values_tsne[:, 1]

    matching_sample_ids: set[UUID] | None = None
    filters = body.filters if body else None
    if filters:
        matching_samples_result = sample_resolver.get_all_by_dataset_id(
            session=session,
            dataset_id=dataset.dataset_id,
            filters=filters,
        )
        matching_sample_ids = {sample.sample_id for sample in matching_samples_result.samples}

    sample_ids = [embedding.sample_id for embedding in embeddings]
    if matching_sample_ids is None:
        fulfils_filter = [1] * len(sample_ids)
    else:
        fulfils_filter = [1 if sample_id in matching_sample_ids else 0 for sample_id in sample_ids]

    # TODO(Malte, 09/2025): Save the 2D-embeddings in the database to avoid recomputing
    # them on every request.

    # TODO(Malte, 09/2025): Include a sample identifier in the returned payload.
    table = pa.table(
        {
            "x": pa.array(x, type=pa.float32()),
            "y": pa.array(y, type=pa.float32()),
            "fulfils_filter": pa.array(fulfils_filter, type=pa.uint8()),
            "sample_id": pa.array([str(sample_id) for sample_id in sample_ids], type=pa.string()),
        }
    )

    buffer = io.BytesIO()
    with ipc.new_stream(buffer, table.schema) as writer:
        writer.write_table(table)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.apache.arrow.stream",
        headers={
            "Content-Disposition": "inline; filename=embeddings2d.arrow",
            "Content-Type": "application/vnd.apache.arrow.stream",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _calculate_tsne_embeddings(embedding_values: NDArray[np.float32]) -> NDArray[np.float32]:
    # TODO(Malte, 10/2025): Switch to a better and faster projection method than
    # scikit-learn's TSNE.
    # See https://linear.app/lightly/issue/LIG-7678/embedding-plot-investigate-fasterandbetter-2d-computation-options
    n_samples = embedding_values.shape[0]
    # For 0, 1 or 2 samples we hard-code deterministic coordinates.
    if n_samples == 0:
        return np.zeros((0, 2), dtype=np.float32)
    if n_samples == 1:
        return np.asarray([[0.0, 0.0]], dtype=np.float32)
    if n_samples == 2:  # noqa: PLR2004
        return np.asarray([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32)

    # Copied from lightly-core:
    # https://github.com/lightly-ai/lightly-core/blob/b738952516e916eba42fdd28498491ff18df5c1e/appv2/packages/queueworker/src/jobs/embeddings2d/function-source/main.py#L179-L186
    embeddings_2d: NDArray[np.float32] = TSNE(
        init="pca",  # changed in https://github.com/scikit-learn/scikit-learn/issues/18018
        learning_rate="auto",  # changed in https://github.com/scikit-learn/scikit-learn/issues/18018
        n_components=2,
        # Perplexity must be _less_ than the number of entries. 30 is the default value.
        # https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
        perplexity=min(30.0, float(n_samples - 1)),
        # Make the computation deterministic.
        random_state=0,
    ).fit_transform(embedding_values)
    return embeddings_2d

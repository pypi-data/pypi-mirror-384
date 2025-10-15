# tests/test_vector_store_models.py

from projectdavid_common.schemas.vectors_schema import VectorStoreCreate


def test_vector_store_create_valid():
    obj = VectorStoreCreate(
        shared_id="vs_001",
        name="My Store",
        user_id="user_123",
        vector_size=384,
        distance_metric="cosine",
    )
    assert obj.distance_metric == "COSINE"

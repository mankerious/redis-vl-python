from pprint import pprint

import numpy as np

from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

data = [
    {
        "id": 1,
        "user": "john",
        "age": 1,
        "job": "engineer",
        "credit_score": "high",
        "user_embedding": np.array([0.1, 0.1, 0.5], dtype=np.float32).tobytes(),
    },
    {
        "id": 2,
        "user": "mary",
        "age": 2,
        "job": "doctor",
        "credit_score": "low",
        "user_embedding": np.array([0.1, 0.1, 0.5], dtype=np.float32).tobytes(),
    },
    {
        "id": 3,
        "user": "joe",
        "age": 3,
        "job": "dentist",
        "credit_score": "medium",
        "user_embedding": np.array([0.9, 0.9, 0.1], dtype=np.float32).tobytes(),
    },
]

schema = {
    "index": {
        "name": "user_index",
        "prefix": "users",
        "storage_type": "hash",
    },
    "fields": {
        "tag": [{"name": "credit_score"}],
        "text": [{"name": "job"}],
        "numeric": [{"name": "age"}],
        "vector": [
            {
                "name": "user_embedding",
                "dims": 3,
                "distance_metric": "cosine",
                "algorithm": "flat",
                "datatype": "float32",
            }
        ],
    },
}


def test_simple(client):
    index = SearchIndex.from_dict(schema)
    # assign client (only for testing)
    index.set_client(client)
    # create the index
    index.create(overwrite=True)

    # load data into the index in Redis
    index.load(data)

    query = VectorQuery(
        vector=[0.1, 0.1, 0.5],
        vector_field_name="user_embedding",
        return_fields=["user", "age", "job", "credit_score"],
        num_results=3,
    )

    results = index.search(query.query, query_params=query.params)
    results_2 = index.query(query)
    assert len(results.docs) == len(results_2.docs)

    # make sure correct users returned
    # users = list(results.docs)
    # print(len(users))
    users = [doc for doc in results.docs]
    assert users[0].user in ["john", "mary"]
    assert users[1].user in ["john", "mary"]

    # make sure vector scores are correct
    # query vector and first two are the same vector.
    # third is different (hence should be positive difference)
    assert float(users[0].vector_distance) == 0.0
    assert float(users[1].vector_distance) == 0.0
    assert float(users[2].vector_distance) > 0

    print()
    for doc in results.docs:
        print("Score:", doc.vector_distance)
        pprint(doc)

    index.delete()

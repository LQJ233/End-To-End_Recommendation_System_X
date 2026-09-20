from training.incremental_train import load_vocabs_from_schema


def test_load_vocabs_from_schema_converts_string_keys_to_ints():
    schema = {
        "vocabs": {
            "user_id": {"10": 1, "20": 2},
            "item_id": {"100": 1},
        }
    }

    vocabs = load_vocabs_from_schema(schema)

    assert vocabs["user_id"][10] == 1
    assert vocabs["user_id"][20] == 2
    assert vocabs["item_id"][100] == 1

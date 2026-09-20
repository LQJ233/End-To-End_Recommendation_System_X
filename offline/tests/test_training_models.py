import torch

from training.models import DeepFM, TwoTower


def test_deepfm_returns_logits_with_batch_dimension():
    model = DeepFM(
        vocab_sizes=[10, 20, 30],
        numeric_dim=2,
        embedding_dim=4,
        hidden_dims=[8, 4],
    )
    categorical = torch.tensor([[1, 2, 3], [2, 3, 4]], dtype=torch.long)
    numeric = torch.tensor([[0.1, 0.2], [0.3, 0.4]], dtype=torch.float32)

    logits = model(categorical, numeric)

    assert logits.shape == (2,)
    assert torch.isfinite(logits).all()


def test_two_tower_returns_normalized_user_and_item_embeddings():
    model = TwoTower(
        user_vocab_sizes=[10, 5],
        item_vocab_sizes=[20, 6],
        embedding_dim=8,
    )
    user_categorical = torch.tensor([[1, 2], [2, 3]], dtype=torch.long)
    item_categorical = torch.tensor([[3, 4], [4, 5]], dtype=torch.long)

    user_embeddings, item_embeddings = model(user_categorical, item_categorical)

    assert user_embeddings.shape == (2, 8)
    assert item_embeddings.shape == (2, 8)
    assert torch.allclose(
        torch.linalg.norm(user_embeddings, dim=1),
        torch.ones(2),
        atol=1e-4,
    )

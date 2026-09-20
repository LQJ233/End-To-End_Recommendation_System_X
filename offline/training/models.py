import torch
from torch import nn
import torch.nn.functional as F


class DeepFM(nn.Module):
    def __init__(
        self,
        vocab_sizes: list[int],
        numeric_dim: int,
        embedding_dim: int = 16,
        hidden_dims: list[int] | None = None,
    ) -> None:
        super().__init__()
        hidden_dims = hidden_dims or [64, 32]
        self.embeddings = nn.ModuleList(
            [nn.Embedding(size, embedding_dim) for size in vocab_sizes]
        )
        self.linear_embeddings = nn.ModuleList(
            [nn.Embedding(size, 1) for size in vocab_sizes]
        )
        self.numeric_linear = nn.Linear(numeric_dim, 1)
        self.numeric_projection = nn.Linear(numeric_dim, embedding_dim)

        input_dim = embedding_dim + numeric_dim
        layers = []
        for hidden_dim in hidden_dims:
            layers.extend([nn.Linear(input_dim, hidden_dim), nn.ReLU()])
            input_dim = hidden_dim
        layers.append(nn.Linear(input_dim, 1))
        self.mlp = nn.Sequential(*layers)

    def forward(self, categorical: torch.Tensor, numeric: torch.Tensor) -> torch.Tensor:
        embeddings = torch.stack(
            [
                embedding(categorical[:, index])
                for index, embedding in enumerate(self.embeddings)
            ],
            dim=1,
        )
        linear_logits = sum(
            embedding(categorical[:, index]).squeeze(-1)
            for index, embedding in enumerate(self.linear_embeddings)
        )
        linear_logits = linear_logits + self.numeric_linear(numeric).squeeze(-1)

        summed = embeddings.sum(dim=1)
        squared_summed = (embeddings * embeddings).sum(dim=1)
        fm_logits = 0.5 * (summed * summed - squared_summed).sum(dim=1)

        mlp_input = torch.cat([embeddings.mean(dim=1), numeric], dim=1)
        mlp_logits = self.mlp(mlp_input).squeeze(-1)
        return linear_logits + fm_logits + mlp_logits


class TwoTower(nn.Module):
    def __init__(
        self,
        user_vocab_sizes: list[int],
        item_vocab_sizes: list[int],
        embedding_dim: int = 32,
    ) -> None:
        super().__init__()
        self.user_embeddings = nn.ModuleList(
            [nn.Embedding(size, embedding_dim) for size in user_vocab_sizes]
        )
        self.item_embeddings = nn.ModuleList(
            [nn.Embedding(size, embedding_dim) for size in item_vocab_sizes]
        )
        user_input_dim = len(user_vocab_sizes) * embedding_dim
        item_input_dim = len(item_vocab_sizes) * embedding_dim
        self.user_tower = nn.Sequential(
            nn.Linear(user_input_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim),
        )
        self.item_tower = nn.Sequential(
            nn.Linear(item_input_dim, embedding_dim),
            nn.ReLU(),
            nn.Linear(embedding_dim, embedding_dim),
        )

    @staticmethod
    def _encode(embeddings: nn.ModuleList, categorical: torch.Tensor) -> torch.Tensor:
        return torch.cat(
            [
                embedding(categorical[:, index])
                for index, embedding in enumerate(embeddings)
            ],
            dim=1,
        )

    def forward(
        self,
        user_categorical: torch.Tensor,
        item_categorical: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        user_vector = self.user_tower(self._encode(self.user_embeddings, user_categorical))
        item_vector = self.item_tower(self._encode(self.item_embeddings, item_categorical))
        return F.normalize(user_vector, dim=1), F.normalize(item_vector, dim=1)

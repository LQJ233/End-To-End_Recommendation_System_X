"""Two-tower recall model.

User tower 与 item tower 输出 L2 归一化向量, 点积作为相似度.
item tower 的 forward 离线全量推一遍后写入 Milvus, user tower 在线实时跑.

设计要点:
    - 共享 item_id embedding: user tower 里"点击/加购/购买序列"和 item tower 里
      的 item_id 共用同一张 embedding 表. 否则"用户点过 X"和"商品 X 本身" 在模型
      看来是两个不相干的实体, 召回质量损失明显.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


class _Tower(nn.Module):
    """单塔: 全部 cat 经 embed + cont 拼接 -> MLP -> L2 norm.

    Args:
        cat_vocabs: name -> vocab_size, 用于本塔独有的 cat 列.
        cont_dim:   连续特征维度.
        emb_dim:    embedding 维度.
        output_dim: MLP 输出维度.
        seq_names:  如果是 user tower, 指定要做 mean-pool 的序列名.
        shared_item_id_embed:  共享的 item_id embedding 表. 既给 seq 用,
                               也作为本塔 "item_id" cat 的 embedding (避免重复创建).
    """

    def __init__(self,
                 cat_vocabs: Dict[str, int],
                 cont_dim: int,
                 emb_dim: int,
                 output_dim: int,
                 seq_names: Optional[List[str]] = None,
                 shared_item_id_embed: Optional[nn.Embedding] = None):
        super().__init__()
        self.cat_embeds = nn.ModuleDict()
        for name, size in cat_vocabs.items():
            if name == "item_id" and shared_item_id_embed is not None:
                # 共享: 不重复建表
                self.cat_embeds[name] = shared_item_id_embed
            else:
                self.cat_embeds[name] = nn.Embedding(max(2, size), emb_dim)

        self.seq_names = list(seq_names or [])
        if self.seq_names:
            if shared_item_id_embed is None:
                raise ValueError("seq_names provided but shared_item_id_embed is None")
            self.seq_embed = shared_item_id_embed

        input_dim = emb_dim * (len(cat_vocabs) + len(self.seq_names)) + cont_dim
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
        )

    def forward(self, cat: Dict[str, torch.Tensor], cont: torch.Tensor,
                seqs: Optional[Dict[str, torch.Tensor]] = None) -> torch.Tensor:
        parts = [self.cat_embeds[k](v) for k, v in cat.items()]
        if seqs:
            for name in self.seq_names:
                seq = seqs.get(name)
                if seq is None:
                    continue
                parts.append(self.seq_embed(seq).mean(dim=1))
        x = torch.cat(parts + [cont], dim=-1)
        return F.normalize(self.mlp(x), dim=-1)


class UserTower(_Tower):
    pass


class ItemTower(_Tower):
    pass


class TwoTowerModel(nn.Module):
    def __init__(self,
                 user_cat_vocabs: Dict[str, int],
                 item_cat_vocabs: Dict[str, int],
                 user_cont_dim: int,
                 item_cont_dim: int,
                 emb_dim: int = 16,
                 output_dim: int = 64):
        super().__init__()

        # ---- 共享的 item_id embedding ----
        item_id_vocab = item_cat_vocabs.get("item_id", 100_000)
        self.item_id_embed = nn.Embedding(max(2, item_id_vocab), emb_dim)

        # ---- User tower: cat 表里去掉 item_id (用户没有 item_id 特征), seq 用共享 embed ----
        self.user_tower = UserTower(
            cat_vocabs={k: v for k, v in user_cat_vocabs.items() if k != "item_id"},
            cont_dim=user_cont_dim,
            emb_dim=emb_dim,
            output_dim=output_dim,
            seq_names=["click_seq", "cart_seq", "purchase_seq"],
            shared_item_id_embed=self.item_id_embed,
        )

        # ---- Item tower: cat 包含 item_id, 由 _Tower 自动用共享 embed ----
        self.item_tower = ItemTower(
            cat_vocabs=item_cat_vocabs,
            cont_dim=item_cont_dim,
            emb_dim=emb_dim,
            output_dim=output_dim,
            seq_names=None,
            shared_item_id_embed=self.item_id_embed,
        )

    def forward(self, user_in, item_in):
        u = self.user_tower(user_in["cat"], user_in["cont"], user_in.get("seqs"))
        v = self.item_tower(item_in["cat"], item_in["cont"])
        return (u * v).sum(dim=-1)

    def encode_user(self, user_in) -> torch.Tensor:
        return self.user_tower(user_in["cat"], user_in["cont"], user_in.get("seqs"))

    def encode_item(self, item_in) -> torch.Tensor:
        return self.item_tower(item_in["cat"], item_in["cont"])

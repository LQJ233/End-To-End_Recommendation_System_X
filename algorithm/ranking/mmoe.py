"""MMoE 多任务排序模型.

该模型同时预测 CTR 与 CVR. 训练规范文档(docs/07_开发规范.md 5.2)要求
排序模型每一处张量变换、损失函数与防泄露逻辑都附有详细注释; 该文件
严格遵守该规范.

输入约定:
    user_in["cat"]   : Dict[str, LongTensor(B,)]   -> 用户离散特征
    user_in["cont"]  : FloatTensor(B, U_C)         -> 用户连续特征
    item_in["cat"]   : Dict[str, LongTensor(B,)]   -> 商品离散特征
    item_in["cont"]  : FloatTensor(B, I_C)         -> 商品连续特征
    cross_in         : FloatTensor(B, X)           -> 交叉连续特征(用户-标签偏好)

输出:
    ctr_logits : FloatTensor(B,)
    cvr_logits : FloatTensor(B,)

时间边界(Time Split):
    所有进入该网络的特征都必须满足 feature_time < label_time,
    否则训练阶段会丢弃该样本.
"""
from __future__ import annotations

from typing import Dict, List

import torch
import torch.nn as nn
import torch.nn.functional as F


# 一个用于专家的 DCN(Deep & Cross Network) 子结构.
# Cross 层显式建模特征二阶交互, Deep 层捕捉高阶非线性.
class _CrossLayer(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        # 形状 (dim, 1): 把 (B, dim) 投影到 (B, 1) 作为交叉权重.
        self.w = nn.Linear(dim, 1, bias=False)
        # 形状 (dim,): 残差偏置项.
        self.b = nn.Parameter(torch.zeros(dim))

    def forward(self, x0: torch.Tensor, xl: torch.Tensor) -> torch.Tensor:
        # x0  : (B, dim) - 输入层(防止信息丢失保留初值)
        # xl  : (B, dim) - 上一层 cross 输出
        # 返回: (B, dim) = x0 * (xl @ w) + b + xl
        scale = self.w(xl)                        # (B, 1)
        return x0 * scale + self.b + xl           # 广播相乘+残差


class _Expert(nn.Module):
    """单个专家: 两层 DCN-Cross + 一层全连接, 输出维度 hidden."""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        # 两层 cross, 维度都和输入对齐.
        self.cross1 = _CrossLayer(input_dim)
        self.cross2 = _CrossLayer(input_dim)
        # 全连接降到 hidden_dim, 后续作为 MMoE gate 的"专家张量".
        self.fc = nn.Linear(input_dim, hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x  : (B, input_dim)
        x1 = self.cross1(x, x)                    # (B, input_dim)
        x2 = self.cross2(x, x1)                   # (B, input_dim)
        return F.relu(self.fc(x2))                # (B, hidden_dim)


class _TaskTower(nn.Module):
    """单个任务塔: 3 层 MLP, 输出 logit (无 sigmoid, BCEWithLogits 内部完成)."""

    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x : (B, input_dim) -> (B,)
        return self.layers(x).squeeze(-1)


class MMoERanking(nn.Module):
    """MMoE 排序模型: 4 个专家 + 每任务一个 gate + 每任务独立塔."""

    NUM_EXPERTS = 4
    NUM_TASKS = 2  # 0: CTR, 1: CVR

    def __init__(self, user_cat_vocabs: Dict[str, int], item_cat_vocabs: Dict[str, int],
                 user_cont_dim: int, item_cont_dim: int, cross_cont_dim: int,
                 emb_dim: int = 16, expert_hidden: int = 128,
                 drop_expert_prob_train: float = 0.1):
        super().__init__()
        # 离散特征 embedding 表; 用 max(2, ...) 防止训练期 vocab=1 导致退化.
        self.user_cat_embeds = nn.ModuleDict({
            n: nn.Embedding(max(2, v), emb_dim) for n, v in user_cat_vocabs.items()
        })
        self.item_cat_embeds = nn.ModuleDict({
            n: nn.Embedding(max(2, v), emb_dim) for n, v in item_cat_vocabs.items()
        })
        # 输入维度 = 全部 cat embedding 拼接 + 连续特征拼接.
        self.input_dim = (
            emb_dim * (len(user_cat_vocabs) + len(item_cat_vocabs))
            + user_cont_dim + item_cont_dim + cross_cont_dim
        )

        # 4 个专家结构相同, 参数独立.
        self.experts = nn.ModuleList([_Expert(self.input_dim, expert_hidden)
                                      for _ in range(self.NUM_EXPERTS)])

        # 每个任务一个 gate: 输入 -> NUM_EXPERTS, softmax 后作为专家加权.
        self.gates = nn.ModuleList([nn.Linear(self.input_dim, self.NUM_EXPERTS)
                                    for _ in range(self.NUM_TASKS)])

        # 每个任务一个独立塔, 输入维度即 expert hidden.
        self.task_towers = nn.ModuleList([_TaskTower(expert_hidden) for _ in range(self.NUM_TASKS)])

        # 训练期专家随机失活概率(文档要求, 缓解专家极化).
        self.drop_expert_prob_train = drop_expert_prob_train

    # ------------------------------------------------------------------
    def _flatten_cat(self, embeds: nn.ModuleDict, cat: Dict[str, torch.Tensor]) -> torch.Tensor:
        # 把字典里的每个 (B,) LongTensor 经过对应 embedding 拼到 (B, K*emb_dim).
        return torch.cat([embeds[k](v) for k, v in cat.items()], dim=-1)

    def _stack_input(self, user_in: Dict, item_in: Dict, cross_cont: torch.Tensor) -> torch.Tensor:
        # 用户离散 -> (B, U_K*emb_dim)
        u_cat = self._flatten_cat(self.user_cat_embeds, user_in["cat"])
        # 商品离散 -> (B, I_K*emb_dim)
        i_cat = self._flatten_cat(self.item_cat_embeds, item_in["cat"])
        # 拼接所有: (B, self.input_dim)
        return torch.cat([u_cat, i_cat, user_in["cont"], item_in["cont"], cross_cont], dim=-1)

    # ------------------------------------------------------------------
    def forward(self, user_in: Dict, item_in: Dict, cross_cont: torch.Tensor):
        # x : (B, input_dim)
        x = self._stack_input(user_in, item_in, cross_cont)

        # 计算专家输出 (NUM_EXPERTS, B, expert_hidden).
        expert_outs = torch.stack([e(x) for e in self.experts], dim=0)

        # 训练时按 drop_expert_prob_train 随机关闭一个专家, 缓解极化.
        if self.training and self.drop_expert_prob_train > 0:
            if torch.rand(1).item() < self.drop_expert_prob_train:
                idx = torch.randint(0, self.NUM_EXPERTS, (1,)).item()
                mask = torch.ones(self.NUM_EXPERTS, device=x.device)
                mask[idx] = 0.0
                expert_outs = expert_outs * mask.view(-1, 1, 1)

        task_outputs: List[torch.Tensor] = []
        for task_idx in range(self.NUM_TASKS):
            # gate_logits : (B, NUM_EXPERTS) -> softmax -> 每个样本对每个专家的权重.
            gate_w = F.softmax(self.gates[task_idx](x), dim=-1)
            # 加权求和: (B, expert_hidden) = sum_e gate_w[:, e:e+1] * expert_outs[e]
            weighted = (gate_w.transpose(0, 1).unsqueeze(-1) * expert_outs).sum(dim=0)
            # 任务塔 -> logit (B,)
            task_outputs.append(self.task_towers[task_idx](weighted))

        ctr_logits, cvr_logits = task_outputs[0], task_outputs[1]
        return ctr_logits, cvr_logits

    # ------------------------------------------------------------------
    @staticmethod
    def loss(ctr_logits: torch.Tensor, cvr_logits: torch.Tensor,
             ctr_label: torch.Tensor, cvr_label: torch.Tensor) -> torch.Tensor:
        # CTR 标签: 点击=1, 曝光未点=0 (来自同一曝光窗口, 防止跨窗误判).
        ctr_loss = F.binary_cross_entropy_with_logits(ctr_logits, ctr_label.float())
        # CVR 标签: 购买=1, 其他=0; 只在 ctr_label=1 的样本上计算 (经典 ESMM 变体).
        clicked = (ctr_label > 0).float()
        cvr_raw = F.binary_cross_entropy_with_logits(cvr_logits, cvr_label.float(), reduction="none")
        cvr_loss = (cvr_raw * clicked).sum() / clicked.sum().clamp_min(1.0)
        # 两路任务等权; 后续可通过 GradNorm/PCGrad 改进.
        return ctr_loss + cvr_loss

    # ------------------------------------------------------------------
    @staticmethod
    def rank_score(ctr_logits: torch.Tensor, cvr_logits: torch.Tensor,
                   ctr_weight: float = 0.7, cvr_weight: float = 0.3) -> torch.Tensor:
        # 排序分 = w_ctr * CTR + w_cvr * CVR (Sigmoid 概率).
        ctr_p = torch.sigmoid(ctr_logits)
        cvr_p = torch.sigmoid(cvr_logits)
        return ctr_weight * ctr_p + cvr_weight * cvr_p

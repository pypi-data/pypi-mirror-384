from __future__ import annotations

from typing import List
import torch
import torch.nn as nn
import torch.nn.functional as F


class CharCNNEncoder(nn.Module):
	def __init__(
		self,
		vocab_size: int,
		embedding_dim: int,
		conv_channels: int,
		kernel_sizes: List[int],
		projection_dim: int,
		layer_norm: bool = True,
	):
		super().__init__()
		self.char_embed = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
		self.convs = nn.ModuleList([
			nn.Conv1d(in_channels=embedding_dim, out_channels=conv_channels, kernel_size=k)
			for k in kernel_sizes
		])
		self.proj = nn.Linear(conv_channels * len(kernel_sizes), projection_dim)
		self.use_ln = layer_norm
		self.ln = nn.LayerNorm(projection_dim) if layer_norm else nn.Identity()

	def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None) -> torch.Tensor:
		# input_ids: [B, T]
		emb = self.char_embed(input_ids)  # [B, T, E]
		# Conv1d expects [B, E, T]
		x = emb.transpose(1, 2)
		conv_outs = []
		for conv in self.convs:
			c = conv(x)  # [B, C, T']
			c = F.relu(c)
			c = F.max_pool1d(c, kernel_size=c.size(2)).squeeze(2)  # [B, C]
			conv_outs.append(c)
		feat = torch.cat(conv_outs, dim=1)  # [B, C * K]
		proj = self.proj(feat)  # [B, D]
		proj = self.ln(proj)
		proj = F.normalize(proj, p=2, dim=-1)
		return proj

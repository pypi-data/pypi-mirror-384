from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class NTXentLoss(nn.Module):
	def __init__(self, temperature: float = 0.07):
		super().__init__()
		self.temperature = temperature

	def forward(self, z1: torch.Tensor, z2: torch.Tensor) -> torch.Tensor:
		# z1, z2: [B, D], assumed L2-normalized
		b = z1.size(0)
		z = torch.cat([z1, z2], dim=0)  # [2B, D]
		sim = torch.matmul(z, z.t()) / self.temperature  # [2B, 2B]
		mask = torch.eye(2 * b, dtype=torch.bool, device=z.device)
		sim.masked_fill_(mask, -1e9)

		targets = torch.arange(b, device=z.device)
		targets = torch.cat([targets + b, targets], dim=0)  # positives across views

		loss = F.cross_entropy(sim, targets)
		return loss

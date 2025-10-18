from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List
import os
import math
import random
import numpy as np
import torch
from torch.utils.data import DataLoader

from embedding_model.config import Config
from embedding_model.tokenizer import CharVocab
from embedding_model.model.charcnn import CharCNNEncoder
from embedding_model.losses.ntxent import NTXentLoss


@dataclass
class TrainState:
	step: int = 0
	best_loss: float = float("inf")


def set_seed(seed: int) -> None:
	random.seed(seed)
	np.random.seed(seed)
	torch.manual_seed(seed)
	torch.cuda.manual_seed_all(seed)


def train(
	cfg: Config,
	train_loader: DataLoader,
	vocab: CharVocab,
	output_dir: str,
	) -> None:
	device = torch.device(cfg.device if torch.cuda.is_available() or cfg.device == "cpu" else "cpu")
	set_seed(cfg.seed)
	os.makedirs(output_dir, exist_ok=True)

	model = CharCNNEncoder(
		vocab_size=len(vocab.itos),
		embedding_dim=cfg.char_embed_dim,
		conv_channels=cfg.conv_channels,
		kernel_sizes=cfg.kernel_sizes,
		projection_dim=cfg.projection_dim,
		layer_norm=cfg.layer_norm,
	).to(device)

	optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
	criterion = NTXentLoss(temperature=cfg.temperature)

	state = TrainState()

	for epoch in range(cfg.epochs):
		model.train()
		running_loss = 0.0
		for i, batch in enumerate(train_loader):
			# batch: ((ids1, mask1), (ids2, mask2))
			(ids1, mask1), (ids2, mask2) = batch
			ids1 = ids1.to(device)
			ids2 = ids2.to(device)
			mask1 = mask1.to(device)
			mask2 = mask2.to(device)

			z1 = model(ids1, mask1)
			z2 = model(ids2, mask2)
			loss = criterion(z1, z2)

			optimizer.zero_grad(set_to_none=True)
			loss.backward()
			optimizer.step()

			state.step += 1
			running_loss += loss.item()

			if state.step % cfg.log_every == 0:
				avg = running_loss / cfg.log_every
				print(f"epoch={epoch} step={state.step} loss={avg:.4f}")
				running_loss = 0.0

			if state.step % cfg.save_every == 0:
				ckpt = os.path.join(output_dir, f"step_{state.step}.pt")
				torch.save({"model": model.state_dict(), "vocab": vocab.itos}, ckpt)

		# end epoch
		ckpt_last = os.path.join(output_dir, "last.pt")
		torch.save({"model": model.state_dict(), "vocab": vocab.itos}, ckpt_last)

from __future__ import annotations

from typing import Callable, List, Tuple
import torch

from embedding_model.tokenizer import CharVocab


def make_char_collate(vocab: CharVocab, max_len: int) -> Callable[[List[str]], Tuple[torch.Tensor, torch.Tensor]]:
	pad_id = vocab.pad_id

	def _collate(batch: List[str]) -> Tuple[torch.Tensor, torch.Tensor]:
		ids = [vocab.encode(text, max_len) for text in batch]
		tensor = torch.tensor(ids, dtype=torch.long)
		mask = (tensor != pad_id).to(torch.bool)
		return tensor, mask

	return _collate

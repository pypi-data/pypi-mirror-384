from __future__ import annotations

from typing import Callable, List, Tuple
from torch.utils.data import Dataset


class ContrastiveTextDataset(Dataset):
	def __init__(self, texts: List[str], view_fn: Callable[[str], str]):
		self._texts = texts
		self._view_fn = view_fn

	def __len__(self) -> int:
		return len(self._texts)

	def __getitem__(self, idx: int) -> Tuple[str, str]:
		text = self._texts[idx]
		return self._view_fn(text), self._view_fn(text)

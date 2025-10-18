from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
import json


PAD_TOKEN = "<pad>"


@dataclass
class CharVocab:
	stoi: Dict[str, int]
	itos: List[str]
	unk_token: str

	@staticmethod
	def build(initial_charset: str, unk_token: str, extra_chars: Iterable[str] = ()) -> "CharVocab":
		unique_chars = []
		seen = set()
		for ch in [PAD_TOKEN, unk_token] + list(initial_charset):
			if ch not in seen:
				seen.add(ch)
				unique_chars.append(ch)
		for ch in extra_chars:
			if ch not in seen:
				seen.add(ch)
				unique_chars.append(ch)
		stoi = {ch: i for i, ch in enumerate(unique_chars)}
		return CharVocab(stoi=stoi, itos=unique_chars, unk_token=unk_token)

	def save(self, path: str) -> None:
		with open(path, "w", encoding="utf-8") as f:
			json.dump({"itos": self.itos, "unk_token": self.unk_token}, f, ensure_ascii=False)

	@staticmethod
	def load(path: str) -> "CharVocab":
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		itos = data["itos"]
		unk = data.get("unk_token", "?")
		stoi = {ch: i for i, ch in enumerate(itos)}
		return CharVocab(stoi=stoi, itos=itos, unk_token=unk)

	@property
	def pad_id(self) -> int:
		return self.stoi[PAD_TOKEN]

	@property
	def unk_id(self) -> int:
		return self.stoi.get(self.unk_token, self.pad_id)

	def encode(self, text: str, max_len: int) -> List[int]:
		ids = [self.stoi.get(ch, self.unk_id) for ch in text[:max_len]]
		if len(ids) < max_len:
			ids.extend([self.pad_id] * (max_len - len(ids)))
		return ids

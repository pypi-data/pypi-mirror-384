from __future__ import annotations

from typing import Any, Dict, Iterable, List
from torch.utils.data import Dataset

from embedding_model.data.flatten import flatten_to_text
from embedding_model.conversation import RoleTokenMap, format_messages


class JsonDataset(Dataset):
	"""Dataset for JSON records converted to text."""
	
	def __init__(
		self,
		records: Iterable[Dict[str, Any]],
		text_separator: str = " \n ",
		field_kv_sep: str = ": ",
		field_pair_sep: str = " | ",
	):
		"""
		Initialize dataset with JSON records.
		
		Args:
			records: Iterable of JSON objects (dictionaries)
			text_separator: Separator between major text blocks
			field_kv_sep: Separator between field names and values
			field_pair_sep: Separator between field pairs
		"""
		self._texts: List[str] = []
		for obj in records:
			text = flatten_to_text(
				obj,
				text_separator=text_separator,
				field_kv_sep=field_kv_sep,
				field_pair_sep=field_pair_sep,
			)
			self._texts.append(text)

	def __len__(self) -> int:
		return len(self._texts)

	def __getitem__(self, idx: int) -> str:
		return self._texts[idx]


class MixedJsonConversationDataset(Dataset):
	"""Legacy dataset class that handles both JSON and conversation data."""
	
	def __init__(
		self,
		records: Iterable[Dict[str, Any]],
		text_separator: str,
		field_kv_sep: str,
		field_pair_sep: str,
		role_tokens: RoleTokenMap = None,
	):
		self._texts: List[str] = []
		for obj in records:
			if isinstance(obj, dict) and isinstance(obj.get("messages"), list) and role_tokens:
				msgs = obj["messages"]
				text = format_messages(msgs, role_tokens, separator=text_separator)
			else:
				text = flatten_to_text(
					obj,
					text_separator=text_separator,
					field_kv_sep=field_kv_sep,
					field_pair_sep=field_pair_sep,
				)
			self._texts.append(text)

	def __len__(self) -> int:
		return len(self._texts)

	def __getitem__(self, idx: int) -> str:
		return self._texts[idx]

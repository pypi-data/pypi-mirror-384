from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _flatten_json(obj: Any, parent_key: str = "", sep: str = ".") -> List[Tuple[str, str]]:
	items: List[Tuple[str, str]] = []
	if isinstance(obj, dict):
		for k, v in obj.items():
			new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
			items.extend(_flatten_json(v, new_key, sep=sep))
	elif isinstance(obj, list):
		for i, v in enumerate(obj):
			new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
			items.extend(_flatten_json(v, new_key, sep=sep))
	else:
		items.append((parent_key, _to_str(obj)))
	return items


def _to_str(v: Any) -> str:
	if v is None:
		return "null"
	return str(v)


def flatten_pairs(obj: Dict[str, Any], key_sep: str = ".") -> List[Tuple[str, str]]:
	pairs = _flatten_json(obj, parent_key="", sep=key_sep)
	pairs.sort(key=lambda x: x[0])
	return pairs


def flatten_to_text(
	obj: Dict[str, Any],
	text_separator: str = " \n ",
	field_kv_sep: str = ": ",
	field_pair_sep: str = " | ",
	key_sep: str = ".",
	) -> str:
	pairs = flatten_pairs(obj, key_sep=key_sep)
	parts = [f"{k}{field_kv_sep}{val}" for k, val in pairs]
	return field_pair_sep.join(parts)
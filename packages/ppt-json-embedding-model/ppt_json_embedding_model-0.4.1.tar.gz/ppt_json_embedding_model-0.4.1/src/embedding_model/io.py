from __future__ import annotations

from typing import Dict, Iterable, Iterator, Set
import ujson as json


def read_jsonl(path: str) -> Iterator[Dict]:
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			yield json.loads(line)


def prescan_charset(records: Iterable[str]) -> Set[str]:
	charset: Set[str] = set()
	for text in records:
		for ch in text:
			charset.add(ch)
	return charset

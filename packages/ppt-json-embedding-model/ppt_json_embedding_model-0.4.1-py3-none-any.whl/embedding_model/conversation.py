from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class RoleTokenMap:
	system: str
	user: str
	assistant: str


def format_messages(
	messages: Iterable[Mapping[str, str]],
	role_tokens: RoleTokenMap,
	separator: str = " \n ",
	) -> str:
	parts: List[str] = []
	for msg in messages:
		role = msg.get("role", "user")
		content = msg.get("content", "")
		if role == "system":
			prefix = role_tokens.system
		elif role == "assistant":
			prefix = role_tokens.assistant
		else:
			prefix = role_tokens.user
		parts.append(f"{prefix} {content}" if content else prefix)
	return separator.join(parts)


def format_query(system: str, user: str, role_tokens: RoleTokenMap, separator: str = " \n ") -> str:
	msgs = [
		{"role": "system", "content": system},
		{"role": "user", "content": user},
	]
	return format_messages(msgs, role_tokens, separator)


def format_qa(system: str, user: str, assistant: str, role_tokens: RoleTokenMap, separator: str = " \n ") -> str:
	msgs = [
		{"role": "system", "content": system},
		{"role": "user", "content": user},
		{"role": "assistant", "content": assistant},
	]
	return format_messages(msgs, role_tokens, separator)

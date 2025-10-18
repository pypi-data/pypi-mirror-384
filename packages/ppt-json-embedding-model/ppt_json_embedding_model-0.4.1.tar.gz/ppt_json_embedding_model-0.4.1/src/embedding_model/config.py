from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import yaml


@dataclass
class AugmentConfig:
	drop_field_prob: float = 0.1
	shuffle_fields: bool = True
	mask_digits_prob: float = 0.0


@dataclass
class VocabConfig:
	initial: str
	unk_token: str = "?"


@dataclass
class RoleTokens:
	system: str = "<|system|>"
	user: str = "<|user|>"
	assistant: str = "<|assistant|>"


@dataclass
class Config:
	seed: int = 42

	# data
	max_chars: int = 2048
	text_separator: str = " \n "
	field_kv_sep: str = ": "
	field_pair_sep: str = " | "
	augment: AugmentConfig = field(default_factory=AugmentConfig)

	# model
	vocab: VocabConfig = field(default_factory=lambda: VocabConfig(initial=""))
	char_embed_dim: int = 32
	conv_channels: int = 256
	kernel_sizes: List[int] = None
	projection_dim: int = 256
	layer_norm: bool = True

	# conversation
	role_tokens: RoleTokens = field(default_factory=RoleTokens)

	# train
	batch_size: int = 128
	epochs: int = 10
	lr: float = 3e-4
	weight_decay: float = 1e-4
	temperature: float = 0.07
	warmup_steps: int = 500
	max_steps: Optional[int] = None
	num_workers: int = 0
	device: str = "cuda"
	log_every: int = 50
	save_every: int = 1000

	def __post_init__(self):
		if self.kernel_sizes is None:
			self.kernel_sizes = [3, 5, 7]


def _as_float(x, default: float) -> float:
	if x is None:
		return default
	if isinstance(x, (int, float)):
		return float(x)
	if isinstance(x, str):
		try:
			return float(x)
		except ValueError:
			return default
	return default


def _as_int(x, default: Optional[int]) -> Optional[int]:
	if x is None:
		return default
	if isinstance(x, (int, float)):
		return int(x)
	if isinstance(x, str):
		try:
			return int(float(x))
		except ValueError:
			return default
	return default


def _as_int_list(x, default: List[int]) -> List[int]:
	if x is None:
		return list(default)
	if isinstance(x, list):
		res: List[int] = []
		for v in x:
			res.append(_as_int(v, None) if _as_int(v, None) is not None else 0)
		return res if res else list(default)
	if isinstance(x, str):
		parts = [p.strip() for p in x.split(",")]
		res = []
		for p in parts:
			val = _as_int(p, None)
			if val is not None:
				res.append(val)
		return res if res else list(default)
	return list(default)


def _dict_to_dataclass(cfg_dict: dict) -> Config:
	augment = cfg_dict.get("augment", {})
	vocab = cfg_dict.get("vocab", {})
	roles = cfg_dict.get("role_tokens", {})
	return Config(
		seed=_as_int(cfg_dict.get("seed", 42), 42) or 42,
		max_chars=_as_int(cfg_dict.get("max_chars", 2048), 2048) or 2048,
		text_separator=cfg_dict.get("text_separator", " \n "),
		field_kv_sep=cfg_dict.get("field_kv_sep", ": "),
		field_pair_sep=cfg_dict.get("field_pair_sep", " | "),
		augment=AugmentConfig(
			drop_field_prob=_as_float(augment.get("drop_field_prob", 0.1), 0.1),
			shuffle_fields=bool(augment.get("shuffle_fields", True)),
			mask_digits_prob=_as_float(augment.get("mask_digits_prob", 0.0), 0.0),
		),
		vocab=VocabConfig(
			initial=vocab.get("initial", ""),
			unk_token=vocab.get("unk_token", "?"),
		),
		char_embed_dim=_as_int(cfg_dict.get("char_embed_dim", 32), 32) or 32,
		conv_channels=_as_int(cfg_dict.get("conv_channels", 256), 256) or 256,
		kernel_sizes=_as_int_list(cfg_dict.get("kernel_sizes", [3, 5, 7]), [3, 5, 7]),
		projection_dim=_as_int(cfg_dict.get("projection_dim", 256), 256) or 256,
		layer_norm=bool(cfg_dict.get("layer_norm", True)),
		role_tokens=RoleTokens(
			system=roles.get("system", "<|system|>"),
			user=roles.get("user", "<|user|>"),
			assistant=roles.get("assistant", "<|assistant|>"),
		),
		batch_size=_as_int(cfg_dict.get("batch_size", 128), 128) or 128,
		epochs=_as_int(cfg_dict.get("epochs", 10), 10) or 10,
		lr=_as_float(cfg_dict.get("lr", 3e-4), 3e-4),
		weight_decay=_as_float(cfg_dict.get("weight_decay", 1e-4), 1e-4),
		temperature=_as_float(cfg_dict.get("temperature", 0.07), 0.07),
		warmup_steps=_as_int(cfg_dict.get("warmup_steps", 500), 500) or 500,
		max_steps=_as_int(cfg_dict.get("max_steps", None), None),
		num_workers=_as_int(cfg_dict.get("num_workers", 0), 0) or 0,
		device=str(cfg_dict.get("device", "cuda")),
		log_every=_as_int(cfg_dict.get("log_every", 50), 50) or 50,
		save_every=_as_int(cfg_dict.get("save_every", 1000), 1000) or 1000,
	)


def load_config(path: str) -> Config:
	with open(path, "r", encoding="utf-8") as f:
		data = yaml.safe_load(f)
	return _dict_to_dataclass(data or {})

from __future__ import annotations

import argparse
import json
import numpy as np
import torch
import logging
from typing import List, Tuple

from embedding_model.config import load_config
from embedding_model.tokenizer import CharVocab
from embedding_model.model.charcnn import CharCNNEncoder
from embedding_model.datasets.collate import make_char_collate
from embedding_model.download import get_default_model_path


def _load_pairs(pairs: List[str]) -> Tuple[np.ndarray, list]:
	all_vecs: List[np.ndarray] = []
	meta: list = []
	for p in pairs:
		if "=" not in p:
			raise ValueError(f"--pairs item must be JSONL=NPY, got: {p}")
		jl, npy = p.split("=", 1)
		X = np.load(npy).astype("float32")
		# build metadata and ensure alignment (truncate to min length if mismatch)
		records = []
		with open(jl, "r", encoding="utf-8") as f:
			for i, line in enumerate(f):
				line = line.strip()
				if not line:
					continue
				records.append((jl, i, json.loads(line)))
		m = min(len(records), X.shape[0])
		if m == 0:
			continue
		all_vecs.append(X[:m])
		meta.extend(records[:m])
	E = np.ascontiguousarray(np.concatenate(all_vecs, axis=0), dtype="float32") if all_vecs else np.zeros((0, 1), dtype="float32")
	return E, meta


def _load_model(cfg_path: str, ckpt_path: str):
	cfg = load_config(cfg_path) if cfg_path else None
	ckpt = torch.load(ckpt_path, map_location="cpu")
	itos = ckpt["vocab"]
	vocab = CharVocab(stoi={ch: i for i, ch in enumerate(itos)}, itos=itos, unk_token="?")
	model = CharCNNEncoder(
		vocab_size=len(vocab.itos),
		embedding_dim=cfg.char_embed_dim if cfg else 32,
		conv_channels=cfg.conv_channels if cfg else 256,
		kernel_sizes=cfg.kernel_sizes if cfg else [3, 5, 7],
		projection_dim=cfg.projection_dim if cfg else 256,
		layer_norm=cfg.layer_norm if cfg else True,
	)
	model.load_state_dict(ckpt["model"]) 
	model.eval()
	collate = make_char_collate(vocab, cfg.max_chars if cfg else 2048)
	return model, collate


def _parse_where(where: List[str]) -> List[Tuple[str, str]]:
	conds: List[Tuple[str, str]] = []
	for w in where:
		if "=" not in w:
			raise ValueError(f"--where must be key=value, got: {w}")
		k, v = w.split("=", 1)
		conds.append((k.strip(), v.strip()))
	return conds


def _apply_filters(meta: list, E: np.ndarray, conds: List[Tuple[str, str]], ignore_case: bool) -> Tuple[np.ndarray, list]:
	if not conds:
		return E, meta
	keep_idx: List[int] = []
	for i, (_, _, obj) in enumerate(meta):
		ok = True
		for k, v in conds:
			ov = obj.get(k)
			if ignore_case:
				match = (str(ov).lower() == v.lower())
			else:
				match = (str(ov) == v)
			if not match:
				ok = False
				break
		if ok:
			keep_idx.append(i)
	if not keep_idx:
		return np.zeros((0, E.shape[1]), dtype=E.dtype), []
	E_sub = E[np.array(keep_idx, dtype=np.int64)]
	meta_sub = [meta[i] for i in keep_idx]
	return E_sub, meta_sub


def main():
	# Set up logging
	logging.basicConfig(level=logging.INFO, format='%(message)s')
	
	parser = argparse.ArgumentParser(description="Local cosine search over precomputed embeddings")
	parser.add_argument("--pairs", nargs='+', required=True, help="One or more JSONL=NPY pairs")
	parser.add_argument("--checkpoint", "--model", help="Model checkpoint to embed query. If not provided, auto-downloads latest")
	parser.add_argument("--config", help="Config YAML for model dims. Defaults to included config if not provided")
	parser.add_argument("--query", required=True, help="Query text")
	parser.add_argument("--topk", type=int, default=5)
	parser.add_argument("--where", nargs='*', default=[], help="Optional prefilters key=value (AND)")
	parser.add_argument("--ignore-case", action='store_true', help="Case-insensitive filter compare")
	args = parser.parse_args()

	E, meta = _load_pairs(args.pairs)
	if E.shape[0] == 0:
		print("no vectors loaded")
		return

	# apply prefilters
	conds = _parse_where(args.where) if args.where else []
	E, meta = _apply_filters(meta, E, conds, args.ignore_case)
	if E.shape[0] == 0:
		print("no records matched filters")
		return

	# Auto-download model if not provided
	if args.checkpoint:
		checkpoint_path = args.checkpoint
		logging.info(f"Using provided model: {checkpoint_path}")
	else:
		checkpoint_path = str(get_default_model_path())
	
	# Use default config if not provided
	if args.config:
		config_path = args.config
	else:
		# Use the default config from the package
		import embedding_model
		import os
		config_path = os.path.join(os.path.dirname(embedding_model.__file__), "config", "default.yaml")
		if not os.path.exists(config_path):
			# Fallback if config not found
			logging.warning("WARNING Default config not found, using minimal defaults")
			config_path = None

	model, collate = _load_model(config_path, checkpoint_path)

	# embed query
	ids, mask = collate([args.query])
	with torch.no_grad():
		q = model(ids, mask).cpu().numpy()[0].astype("float32")

	scores = E @ q
	idx = np.argsort(scores)[::-1][: args.topk]

	for rank, i in enumerate(idx, 1):
		jl, line_num, obj = meta[i]
		key_fields = {k: obj.get(k) for k in ("Id","Name","SerialNumber","Status","device_id","ticket_id","customer_id") if k in obj}
		print(f"{rank}. {scores[i]:.4f}  {jl}:{line_num}  {key_fields}")


if __name__ == "__main__":
	main()

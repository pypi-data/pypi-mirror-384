from __future__ import annotations

import argparse
import os
import json
import numpy as np
import torch
import logging

from embedding_model.config import load_config
from embedding_model.tokenizer import CharVocab
from embedding_model.model.charcnn import CharCNNEncoder
from embedding_model.datasets.collate import make_char_collate
from embedding_model.conversation import RoleTokenMap
from embedding_model.data.flatten import flatten_to_text
from embedding_model.download import get_default_model_path


def record_to_text(obj, cfg, role_tokens: RoleTokenMap) -> str:
	"""Convert a JSON record to text representation."""
	if isinstance(obj, dict) and isinstance(obj.get("messages"), list) and cfg and role_tokens:
		parts = []
		for m in obj["messages"]:
			role = m.get("role", "user")
			content = m.get("content", "")
			prefix = getattr(role_tokens, role, role_tokens.user) if hasattr(role_tokens, role) else role_tokens.user
			parts.append(f"{prefix} {content}" if content else prefix)
		return (cfg.text_separator or " \n ").join(parts)
	else:
		return flatten_to_text(
			obj,
			text_separator=(cfg.text_separator if cfg else " \n "),
			field_kv_sep=(cfg.field_kv_sep if cfg else ": "),
			field_pair_sep=(cfg.field_pair_sep if cfg else " | "),
		)


def main():
	# Set up logging
	logging.basicConfig(level=logging.INFO, format='%(message)s')
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--checkpoint", "--model", help="Model checkpoint (.pt file). If not provided, auto-downloads latest")
	parser.add_argument("--input", required=True, help="JSONL input")
	parser.add_argument("--output", required=True, help=".npy output file")
	parser.add_argument("--config", required=False, help="Optional config for separators and model dims")
	parser.add_argument("--batch-size", type=int, default=256, help="Embedding batch size")
	parser.add_argument("--limit", type=int, default=None, help="Optional record cap for quick runs")
	args = parser.parse_args()

	cfg = load_config(args.config) if args.config else None

	# Auto-download model if not provided
	if args.checkpoint:
		checkpoint_path = args.checkpoint
		logging.info(f"Using provided model: {checkpoint_path}")
	else:
		checkpoint_path = str(get_default_model_path())

	ckpt = torch.load(checkpoint_path, map_location="cpu")
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
	role_tokens = None
	if cfg:
		role_tokens = RoleTokenMap(cfg.role_tokens.system, cfg.role_tokens.user, cfg.role_tokens.assistant)

	embs: list[np.ndarray] = []
	batch_texts: list[str] = []
	count = 0

	with open(args.input, "r", encoding="utf-8") as f:
		for line in f:
			if not line.strip():
				continue
			obj = json.loads(line)
			text = record_to_text(obj, cfg, role_tokens) if cfg else flatten_to_text(obj)
			batch_texts.append(text)
			count += 1
			if args.limit is not None and count >= args.limit:
				# flush remaining below
				pass
			if len(batch_texts) >= args.batch_size or (args.limit is not None and count >= args.limit):
				ids, mask = collate(batch_texts)
				with torch.no_grad():
					z = model(ids, mask).cpu().numpy()
				embs.append(z)
				batch_texts.clear()
				if args.limit is not None and count >= args.limit:
					break

	# flush any tail
	if batch_texts:
		ids, mask = collate(batch_texts)
		with torch.no_grad():
			z = model(ids, mask).cpu().numpy()
		embs.append(z)

	E = np.concatenate(embs, axis=0) if embs else np.zeros((0, cfg.projection_dim if cfg else 256), dtype=np.float32)
	os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
	np.save(args.output, E)
	print(f"wrote {E.shape} to {args.output}")


if __name__ == "__main__":
	main()

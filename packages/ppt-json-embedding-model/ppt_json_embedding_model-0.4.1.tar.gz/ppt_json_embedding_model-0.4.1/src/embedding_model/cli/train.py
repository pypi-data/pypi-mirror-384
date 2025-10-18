from __future__ import annotations

import argparse
import os
from typing import List

import torch

from embedding_model.config import load_config
from embedding_model.io import read_jsonl, prescan_charset
from embedding_model.tokenizer import CharVocab
from embedding_model.datasets.mixed import MixedJsonConversationDataset
from embedding_model.datasets.collate import make_char_collate
from embedding_model.datasets.contrastive_text import ContrastiveTextDataset
from embedding_model.conversation import RoleTokenMap
from embedding_model.train.trainer import train


def _build_vocab(cfg, texts):
	charset = prescan_charset(texts)
	vocab = CharVocab.build(cfg.vocab.initial, cfg.vocab.unk_token, extra_chars=charset)
	return vocab


def _make_view_fn():
	# Simple identity view for now; augmentations can be added here
	return lambda s: s


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--config", required=True)
	parser.add_argument("--data", nargs='+', required=True, help="JSONL files")
	parser.add_argument("--out", required=True, help="Output directory")
	args = parser.parse_args()

	cfg = load_config(args.config)

	# Load and gather texts
	role_tokens = RoleTokenMap(
		system=cfg.role_tokens.system,
		user=cfg.role_tokens.user,
		assistant=cfg.role_tokens.assistant,
	)
	all_texts: List[str] = []
	for path in args.data:
		ds = MixedJsonConversationDataset(
			records=read_jsonl(path),
			text_separator=cfg.text_separator,
			field_kv_sep=cfg.field_kv_sep,
			field_pair_sep=cfg.field_pair_sep,
			role_tokens=role_tokens,
		)
		all_texts.extend([ds[i] for i in range(len(ds))])

	vocab = _build_vocab(cfg, all_texts)

	contrastive = ContrastiveTextDataset(all_texts, view_fn=_make_view_fn())

	collate_text = make_char_collate(vocab, cfg.max_chars)
	def _contrastive_collate(batch):
		texts1, texts2 = zip(*batch)
		ids1, mask1 = collate_text(list(texts1))
		ids2, mask2 = collate_text(list(texts2))
		return (ids1, mask1), (ids2, mask2)

	loader = torch.utils.data.DataLoader(
		contrastive,
		batch_size=cfg.batch_size,
		shuffle=True,
		num_workers=cfg.num_workers,
		collate_fn=_contrastive_collate,
	)

	train(cfg, loader, vocab, args.out)


if __name__ == "__main__":
	main()

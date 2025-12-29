#!/bin/bash
# Run evaluation script with both golden query files
python eval/run_eval.py --k 5 --gold eval/golden_queries.jsonl --gold eval/golden_queries_hard.jsonl


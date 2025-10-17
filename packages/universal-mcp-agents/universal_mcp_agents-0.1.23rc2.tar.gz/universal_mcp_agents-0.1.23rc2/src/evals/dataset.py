import csv
import json
from typing import Any


def load_dataset(file_path: str, difficulty_split: str | None = None) -> list[dict[str, Any]]:
    """
    Loads a dataset from a CSV or JSONL file.

    Args:
        file_path: The path to the dataset file.
        difficulty_split: Optional difficulty split to apply.
            Can be "easy", "medium", "hard".

    Returns:
        A list of dictionaries, where each dictionary represents an example.
    """
    if file_path.endswith(".csv"):
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            examples = list(reader)
    elif file_path.endswith(".jsonl"):
        with open(file_path, encoding="utf-8") as f:
            examples = [json.loads(line) for line in f]
    else:
        raise ValueError("Unsupported file format. Please use CSV or JSONL.")

    if difficulty_split:
        if difficulty_split == "easy":
            difficulty_range = {1, 2}
        elif difficulty_split == "medium":
            difficulty_range = {3}
        elif difficulty_split == "hard":
            difficulty_range = {4, 5}
        else:
            raise ValueError("Invalid difficulty split. Please use 'easy', 'medium', or 'hard'.")

        return [ex for ex in examples if "difficulty" in ex and ex["difficulty"] in difficulty_range]

    return examples

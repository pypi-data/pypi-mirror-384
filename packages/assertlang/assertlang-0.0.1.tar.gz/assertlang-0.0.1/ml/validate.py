#!/usr/bin/env python3
"""
Validation script for CharCNN model.

Analyzes:
- Per-operation accuracy
- Confusion matrix
- Failed predictions
- Similar operations that are confused
"""

import json
import torch
import torch.nn.functional as F
from collections import defaultdict
import numpy as np

from ml.tokenizer import CharTokenizer
from ml.encoders import CharCNN
from ml.losses import OperationEmbedding


def load_model(model_path: str, device: torch.device):
    """Load trained model."""
    checkpoint = torch.load(model_path, map_location=device)

    # Get config from checkpoint
    operation_to_id = checkpoint['operation_to_id']
    id_to_operation = checkpoint['id_to_operation']
    num_operations = len(operation_to_id)

    # Create model
    model = CharCNN(
        vocab_size=128,
        embed_dim=64,
        hidden_dim=256,
        output_dim=256,
        kernel_sizes=[3, 5, 7],
        num_filters=64,
        dropout=0.1
    ).to(device)

    operation_emb = OperationEmbedding(
        num_operations=num_operations,
        embed_dim=256
    ).to(device)

    # Load weights
    model.load_state_dict(checkpoint['model_state_dict'])
    operation_emb.load_state_dict(checkpoint['operation_emb_state_dict'])

    model.eval()
    operation_emb.eval()

    return model, operation_emb, operation_to_id, id_to_operation


def predict_operation(
    model: CharCNN,
    operation_emb: OperationEmbedding,
    tokenizer: CharTokenizer,
    pw_code: str,
    operation_to_id: dict,
    id_to_operation: dict,
    top_k: int = 5
) -> list:
    """
    Predict operation from PW code.

    Returns:
        List of (operation_id, similarity_score) tuples
    """
    # Tokenize
    char_ids = tokenizer.encode(pw_code)
    char_ids_tensor = torch.tensor(char_ids, dtype=torch.long).unsqueeze(0)

    # Encode code
    with torch.no_grad():
        code_embedding = model(char_ids_tensor)  # [1, 256]

        # Get all operation embeddings
        all_operation_ids = torch.arange(len(operation_to_id))
        all_operation_embeddings = operation_emb(all_operation_ids)  # [num_ops, 256]

        # Compute similarities
        similarities = torch.matmul(code_embedding, all_operation_embeddings.t())  # [1, num_ops]
        similarities = similarities.squeeze(0)  # [num_ops]

        # Get top-k predictions
        top_k_similarities, top_k_indices = torch.topk(similarities, k=min(top_k, len(operation_to_id)))

        predictions = []
        for sim, idx in zip(top_k_similarities, top_k_indices):
            op_id = id_to_operation[int(idx)]
            predictions.append((op_id, float(sim)))

    return predictions


def validate_dataset(
    model: CharCNN,
    operation_emb: OperationEmbedding,
    tokenizer: CharTokenizer,
    data_path: str,
    operation_to_id: dict,
    id_to_operation: dict
):
    """Validate model on entire dataset."""
    # Load data
    with open(data_path) as f:
        examples = json.load(f)

    # Track results
    correct = 0
    total = len(examples)
    errors = []
    operation_stats = defaultdict(lambda: {'correct': 0, 'total': 0})

    print(f"Validating on {total} examples...")
    print()

    for i, example in enumerate(examples):
        pw_code = example['pw_code']
        true_operation = example['operation_id']

        # Predict
        predictions = predict_operation(
            model, operation_emb, tokenizer, pw_code,
            operation_to_id, id_to_operation, top_k=5
        )

        predicted_operation = predictions[0][0]
        is_correct = predicted_operation == true_operation

        # Update stats
        if is_correct:
            correct += 1
        else:
            errors.append({
                'example_id': i,
                'pw_code': pw_code,
                'true_operation': true_operation,
                'predicted_operation': predicted_operation,
                'top_5': predictions
            })

        # Per-operation stats
        operation_stats[true_operation]['total'] += 1
        if is_correct:
            operation_stats[true_operation]['correct'] += 1

    accuracy = correct / total

    print(f"Overall Accuracy: {accuracy:.2%} ({correct}/{total})")
    print()

    # Print per-operation accuracy
    print("Per-Operation Accuracy:")
    print("-" * 80)
    for op_id in sorted(operation_stats.keys()):
        stats = operation_stats[op_id]
        op_accuracy = stats['correct'] / stats['total']
        status = "✅" if op_accuracy == 1.0 else "❌" if op_accuracy < 0.5 else "⚠️ "
        print(f"{status} {op_id:35} {stats['correct']:2}/{stats['total']:2} ({op_accuracy:.0%})")
    print()

    # Print errors
    if errors:
        print(f"Failed Predictions ({len(errors)} errors):")
        print("-" * 80)
        for error in errors[:20]:  # Show first 20 errors
            print(f"\nExample {error['example_id']}:")
            print(f"  Code:      {error['pw_code']}")
            print(f"  True:      {error['true_operation']}")
            print(f"  Predicted: {error['predicted_operation']}")
            print(f"  Top 5:")
            for op_id, sim in error['top_5']:
                print(f"    {sim:6.3f}  {op_id}")
    else:
        print("🎉 No errors! 100% accuracy achieved!")

    return accuracy, operation_stats, errors


def main():
    print("=" * 80)
    print("CharCNN Model Validation")
    print("=" * 80)
    print()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Device: {device}")
    print()

    # Load model
    model_path = "ml/charcnn_best.pt"
    data_path = "training_dataset_full.json"

    print(f"Loading model from {model_path}...")
    model, operation_emb, operation_to_id, id_to_operation = load_model(model_path, device)
    print(f"Loaded {len(operation_to_id)} operations")
    print()

    # Create tokenizer
    tokenizer = CharTokenizer(vocab_size=128, max_length=256)

    # Validate
    accuracy, operation_stats, errors = validate_dataset(
        model, operation_emb, tokenizer, data_path,
        operation_to_id, id_to_operation
    )

    # Summary
    print()
    print("=" * 80)
    print("Validation Summary")
    print("=" * 80)
    print(f"Overall Accuracy: {accuracy:.2%}")
    print(f"Operations with 100% accuracy: {sum(1 for stats in operation_stats.values() if stats['correct'] == stats['total'])}/{len(operation_stats)}")
    print(f"Operations with <100% accuracy: {sum(1 for stats in operation_stats.values() if stats['correct'] < stats['total'])}/{len(operation_stats)}")
    print()

    # Test live predictions
    print("=" * 80)
    print("Live Prediction Test")
    print("=" * 80)
    print()

    test_cases = [
        'let content = file.read("data.txt")',
        'if file.exists(path)',
        'let parts = str.split(text, ",")',
        'let data = http.get_json("https://api.example.com")',
        'for item in items',
        'let count = len(array)',
    ]

    for pw_code in test_cases:
        predictions = predict_operation(
            model, operation_emb, tokenizer, pw_code,
            operation_to_id, id_to_operation, top_k=3
        )
        print(f"Code: {pw_code}")
        print(f"Top 3 predictions:")
        for op_id, sim in predictions:
            print(f"  {sim:6.3f}  {op_id}")
        print()


if __name__ == "__main__":
    main()

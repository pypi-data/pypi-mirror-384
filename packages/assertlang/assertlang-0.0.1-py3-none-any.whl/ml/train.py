#!/usr/bin/env python3
"""
Training script for CharCNN operation lookup model.

Training parameters (from research):
- Epochs: 50
- Batch size: 32
- Learning rate: 1e-3
- Optimizer: Adam
- Target: 100% recall@1

Dataset: training_dataset_full.json (193 examples, 84 operations)
"""

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import time
from typing import Dict, List, Tuple
import numpy as np

from ml.tokenizer import CharTokenizer
from ml.encoders import CharCNN
from ml.losses import InfoNCE, OperationEmbedding


class OperationDataset(Dataset):
    """Dataset for PW code → operation_id pairs."""

    def __init__(self, data_path: str, tokenizer: CharTokenizer, operation_to_id: Dict[str, int]):
        """
        Initialize dataset.

        Args:
            data_path: Path to training_dataset_full.json
            tokenizer: Character tokenizer
            operation_to_id: Mapping from operation_id to integer index
        """
        self.tokenizer = tokenizer
        self.operation_to_id = operation_to_id

        # Load training data
        with open(data_path) as f:
            self.examples = json.load(f)

        print(f"Loaded {len(self.examples)} training examples")

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get training example."""
        example = self.examples[idx]

        # Tokenize PW code
        pw_code = example['pw_code']
        char_ids = self.tokenizer.encode(pw_code)

        # Get operation ID
        operation_id = example['operation_id']
        operation_idx = self.operation_to_id[operation_id]

        return torch.tensor(char_ids, dtype=torch.long), torch.tensor(operation_idx, dtype=torch.long)


def build_operation_vocab(data_path: str) -> Tuple[Dict[str, int], Dict[int, str]]:
    """
    Build operation vocabulary from dataset.

    Args:
        data_path: Path to training_dataset_full.json

    Returns:
        operation_to_id: Mapping from operation_id to integer index
        id_to_operation: Reverse mapping
    """
    with open(data_path) as f:
        examples = json.load(f)

    # Get unique operation IDs
    operation_ids = sorted(set(ex['operation_id'] for ex in examples))

    # Build mappings
    operation_to_id = {op_id: idx for idx, op_id in enumerate(operation_ids)}
    id_to_operation = {idx: op_id for op_id, idx in operation_to_id.items()}

    print(f"Found {len(operation_ids)} unique operations")

    return operation_to_id, id_to_operation


def train_epoch(
    model: CharCNN,
    operation_emb: OperationEmbedding,
    dataloader: DataLoader,
    loss_fn: InfoNCE,
    optimizer: optim.Optimizer,
    device: torch.device
) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    operation_emb.train()

    total_loss = 0.0
    total_accuracy = 0.0
    num_batches = 0

    for char_ids, operation_ids in dataloader:
        char_ids = char_ids.to(device)
        operation_ids = operation_ids.to(device)

        # Forward pass
        code_embeddings = model(char_ids)
        operation_embeddings = operation_emb(operation_ids)

        # Compute loss
        loss, metrics = loss_fn(code_embeddings, operation_embeddings)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Accumulate metrics
        total_loss += metrics['loss']
        total_accuracy += metrics['accuracy']
        num_batches += 1

    return {
        'loss': total_loss / num_batches,
        'accuracy': total_accuracy / num_batches
    }


def evaluate(
    model: CharCNN,
    operation_emb: OperationEmbedding,
    dataloader: DataLoader,
    loss_fn: InfoNCE,
    device: torch.device
) -> Dict[str, float]:
    """Evaluate model."""
    model.eval()
    operation_emb.eval()

    total_loss = 0.0
    total_accuracy = 0.0
    num_batches = 0

    with torch.no_grad():
        for char_ids, operation_ids in dataloader:
            char_ids = char_ids.to(device)
            operation_ids = operation_ids.to(device)

            # Forward pass
            code_embeddings = model(char_ids)
            operation_embeddings = operation_emb(operation_ids)

            # Compute loss
            loss, metrics = loss_fn(code_embeddings, operation_embeddings)

            # Accumulate metrics
            total_loss += metrics['loss']
            total_accuracy += metrics['accuracy']
            num_batches += 1

    return {
        'loss': total_loss / num_batches,
        'accuracy': total_accuracy / num_batches
    }


def main():
    print("=" * 80)
    print("CharCNN Training - Operation Lookup")
    print("=" * 80)
    print()

    # Configuration
    data_path = "training_dataset_full.json"
    vocab_size = 128
    max_length = 256
    embed_dim = 64
    hidden_dim = 256
    output_dim = 256
    batch_size = 32
    num_epochs = 50
    learning_rate = 1e-3
    temperature = 0.07
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print(f"Device: {device}")
    print(f"Dataset: {data_path}")
    print(f"Batch size: {batch_size}")
    print(f"Epochs: {num_epochs}")
    print(f"Learning rate: {learning_rate}")
    print(f"Temperature: {temperature}")
    print()

    # Check if dataset exists
    if not Path(data_path).exists():
        print(f"ERROR: Dataset not found at {data_path}")
        print("Please run expand_training_dataset.py first")
        return

    # Build operation vocabulary
    operation_to_id, id_to_operation = build_operation_vocab(data_path)
    num_operations = len(operation_to_id)
    print(f"Operations: {num_operations}")
    print()

    # Create tokenizer
    tokenizer = CharTokenizer(vocab_size=vocab_size, max_length=max_length)

    # Create dataset and dataloader
    dataset = OperationDataset(data_path, tokenizer, operation_to_id)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    print(f"Batches per epoch: {len(dataloader)}")
    print()

    # Create model
    model = CharCNN(
        vocab_size=vocab_size,
        embed_dim=embed_dim,
        hidden_dim=hidden_dim,
        output_dim=output_dim,
        kernel_sizes=[3, 5, 7],
        num_filters=64,
        dropout=0.1
    ).to(device)

    operation_emb = OperationEmbedding(
        num_operations=num_operations,
        embed_dim=output_dim
    ).to(device)

    print(f"Model parameters: {model.count_parameters():,}")
    print()

    # Create loss and optimizer
    loss_fn = InfoNCE(temperature=temperature)
    optimizer = optim.Adam(
        list(model.parameters()) + list(operation_emb.parameters()),
        lr=learning_rate
    )

    # Training loop
    print("=" * 80)
    print("Training")
    print("=" * 80)
    print()

    best_accuracy = 0.0
    start_time = time.time()

    for epoch in range(num_epochs):
        epoch_start = time.time()

        # Train
        train_metrics = train_epoch(model, operation_emb, dataloader, loss_fn, optimizer, device)

        # Evaluate
        eval_metrics = evaluate(model, operation_emb, dataloader, loss_fn, device)

        epoch_time = time.time() - epoch_start

        # Log progress
        print(f"Epoch {epoch+1:2d}/{num_epochs} ({epoch_time:.1f}s) | "
              f"Train Loss: {train_metrics['loss']:.4f} | "
              f"Train Acc: {train_metrics['accuracy']:.2%} | "
              f"Eval Loss: {eval_metrics['loss']:.4f} | "
              f"Eval Acc: {eval_metrics['accuracy']:.2%}")

        # Save best model
        if eval_metrics['accuracy'] > best_accuracy:
            best_accuracy = eval_metrics['accuracy']
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'operation_emb_state_dict': operation_emb.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'accuracy': best_accuracy,
                'operation_to_id': operation_to_id,
                'id_to_operation': id_to_operation,
            }, 'ml/charcnn_best.pt')

        # Check if we hit 100% accuracy
        if eval_metrics['accuracy'] >= 1.0:
            print()
            print(f"✅ Achieved 100% accuracy at epoch {epoch+1}!")
            break

    total_time = time.time() - start_time

    print()
    print("=" * 80)
    print("Training Complete")
    print("=" * 80)
    print(f"Best accuracy: {best_accuracy:.2%}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Model saved: ml/charcnn_best.pt")
    print()


if __name__ == "__main__":
    main()

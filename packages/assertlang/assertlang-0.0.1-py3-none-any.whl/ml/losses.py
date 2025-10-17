#!/usr/bin/env python3
"""
InfoNCE contrastive loss for CharCNN training.

Loss function:
- Symmetric contrastive loss (code→operation + operation→code)
- Temperature: 0.07
- In-batch negatives (all other pairs in batch)
- Cross-entropy on similarity matrix

Reference: SimCLR, CLIP contrastive learning
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class InfoNCE(nn.Module):
    """InfoNCE contrastive loss with temperature scaling."""

    def __init__(self, temperature: float = 0.07):
        """
        Initialize InfoNCE loss.

        Args:
            temperature: Temperature parameter for scaling (default 0.07)
        """
        super().__init__()
        self.temperature = temperature
        self.criterion = nn.CrossEntropyLoss()

    def forward(
        self,
        code_embeddings: torch.Tensor,
        operation_embeddings: torch.Tensor
    ) -> tuple[torch.Tensor, dict]:
        """
        Compute InfoNCE loss.

        Args:
            code_embeddings: Code embeddings [batch_size, embed_dim]
            operation_embeddings: Operation embeddings [batch_size, embed_dim]

        Returns:
            loss: Scalar loss value
            metrics: Dictionary with accuracy and temperature
        """
        batch_size = code_embeddings.shape[0]

        # Normalize embeddings (should already be normalized, but ensure)
        code_embeddings = F.normalize(code_embeddings, p=2, dim=1)
        operation_embeddings = F.normalize(operation_embeddings, p=2, dim=1)

        # Compute similarity matrix: [batch_size, batch_size]
        # logits[i, j] = similarity between code[i] and operation[j]
        logits = torch.matmul(code_embeddings, operation_embeddings.t()) / self.temperature

        # Labels: diagonal entries are positive pairs
        labels = torch.arange(batch_size, device=logits.device)

        # Symmetric loss: code→operation + operation→code
        loss_code_to_op = self.criterion(logits, labels)
        loss_op_to_code = self.criterion(logits.t(), labels)
        loss = (loss_code_to_op + loss_op_to_code) / 2

        # Compute accuracy (recall@1)
        with torch.no_grad():
            # Code→Operation accuracy
            pred_code_to_op = torch.argmax(logits, dim=1)
            acc_code_to_op = (pred_code_to_op == labels).float().mean()

            # Operation→Code accuracy
            pred_op_to_code = torch.argmax(logits.t(), dim=1)
            acc_op_to_code = (pred_op_to_code == labels).float().mean()

            # Average accuracy
            accuracy = (acc_code_to_op + acc_op_to_code) / 2

        metrics = {
            'loss': loss.item(),
            'accuracy': accuracy.item(),
            'acc_code_to_op': acc_code_to_op.item(),
            'acc_op_to_code': acc_op_to_code.item(),
            'temperature': self.temperature
        }

        return loss, metrics


class OperationEmbedding(nn.Module):
    """Learnable embeddings for operation IDs."""

    def __init__(self, num_operations: int, embed_dim: int = 256):
        """
        Initialize operation embeddings.

        Args:
            num_operations: Number of unique operations
            embed_dim: Embedding dimension (must match CharCNN output)
        """
        super().__init__()
        self.num_operations = num_operations
        self.embed_dim = embed_dim

        # Learnable operation embeddings
        self.embeddings = nn.Embedding(num_operations, embed_dim)

        # Initialize embeddings
        nn.init.xavier_uniform_(self.embeddings.weight)

    def forward(self, operation_ids: torch.Tensor) -> torch.Tensor:
        """
        Get operation embeddings.

        Args:
            operation_ids: Operation indices [batch_size]

        Returns:
            L2-normalized embeddings [batch_size, embed_dim]
        """
        embeddings = self.embeddings(operation_ids)
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings


if __name__ == "__main__":
    # Test InfoNCE loss
    print("=" * 80)
    print("InfoNCE Loss Test")
    print("=" * 80)
    print()

    # Create loss function
    loss_fn = InfoNCE(temperature=0.07)

    # Create operation embeddings
    num_operations = 84
    operation_emb = OperationEmbedding(num_operations=num_operations, embed_dim=256)

    # Test case 1: Perfect alignment (should have low loss, high accuracy)
    batch_size = 8
    embed_dim = 256

    # Same embeddings for code and operations (perfect match)
    embeddings = F.normalize(torch.randn(batch_size, embed_dim), p=2, dim=1)
    code_embeddings = embeddings
    operation_embeddings = embeddings

    loss, metrics = loss_fn(code_embeddings, operation_embeddings)
    print("Test 1: Perfect alignment")
    print(f"  Loss:               {metrics['loss']:.4f}")
    print(f"  Accuracy:           {metrics['accuracy']:.2%}")
    print(f"  Acc (code→op):      {metrics['acc_code_to_op']:.2%}")
    print(f"  Acc (op→code):      {metrics['acc_op_to_code']:.2%}")
    print()

    # Test case 2: Random embeddings (should have high loss, low accuracy)
    code_embeddings = F.normalize(torch.randn(batch_size, embed_dim), p=2, dim=1)
    operation_embeddings = F.normalize(torch.randn(batch_size, embed_dim), p=2, dim=1)

    loss, metrics = loss_fn(code_embeddings, operation_embeddings)
    print("Test 2: Random embeddings")
    print(f"  Loss:               {metrics['loss']:.4f}")
    print(f"  Accuracy:           {metrics['accuracy']:.2%}")
    print(f"  Acc (code→op):      {metrics['acc_code_to_op']:.2%}")
    print(f"  Acc (op→code):      {metrics['acc_op_to_code']:.2%}")
    print()

    # Test case 3: Learnable operation embeddings
    operation_ids = torch.arange(batch_size) % num_operations
    code_embeddings = F.normalize(torch.randn(batch_size, embed_dim), p=2, dim=1)
    operation_embeddings = operation_emb(operation_ids)

    loss, metrics = loss_fn(code_embeddings, operation_embeddings)
    print("Test 3: Learnable operation embeddings")
    print(f"  Loss:               {metrics['loss']:.4f}")
    print(f"  Accuracy:           {metrics['accuracy']:.2%}")
    print(f"  Num operations:     {num_operations}")
    print()

    print("=" * 80)

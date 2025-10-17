#!/usr/bin/env python3
"""
CharCNN encoder for semantic code lookup.

Architecture:
- Character embedding (128 vocab → 64 dims)
- Multi-scale convolutions (kernel sizes: 3, 5, 7)
- Global max pooling
- Dense projection to embedding space (256 dims)
- L2 normalization

Total parameters: ~263K (matching research baseline)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class CharCNN(nn.Module):
    """Character-level CNN encoder."""

    def __init__(
        self,
        vocab_size: int = 128,
        embed_dim: int = 64,
        hidden_dim: int = 256,
        output_dim: int = 256,
        kernel_sizes: list = [3, 5, 7],
        num_filters: int = 64,
        dropout: float = 0.1
    ):
        """
        Initialize CharCNN encoder.

        Args:
            vocab_size: Character vocabulary size (128 for ASCII)
            embed_dim: Character embedding dimension (64)
            hidden_dim: Hidden layer dimension (256)
            output_dim: Output embedding dimension (256)
            kernel_sizes: Convolutional kernel sizes [3, 5, 7]
            num_filters: Number of filters per kernel size (64)
            dropout: Dropout rate (0.1)
        """
        super().__init__()

        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.output_dim = output_dim

        # Character embedding
        self.char_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # Multi-scale convolutions
        self.convolutions = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, kernel_size=k, padding=k//2)
            for k in kernel_sizes
        ])

        # Projection to output dimension
        conv_output_dim = num_filters * len(kernel_sizes)
        self.projection = nn.Sequential(
            nn.Linear(conv_output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize model weights."""
        # Embedding initialization
        nn.init.uniform_(self.char_embedding.weight, -0.1, 0.1)

        # Convolution initialization
        for conv in self.convolutions:
            nn.init.kaiming_normal_(conv.weight, mode='fan_out', nonlinearity='relu')
            nn.init.zeros_(conv.bias)

        # Linear layers initialization
        for module in self.projection.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, char_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            char_ids: Character indices [batch_size, seq_len]

        Returns:
            L2-normalized embeddings [batch_size, output_dim]
        """
        # Character embedding: [batch_size, seq_len, embed_dim]
        embedded = self.char_embedding(char_ids)

        # Transpose for conv1d: [batch_size, embed_dim, seq_len]
        embedded = embedded.transpose(1, 2)

        # Multi-scale convolutions + max pooling
        conv_outputs = []
        for conv in self.convolutions:
            # Convolution: [batch_size, num_filters, seq_len]
            conv_out = F.relu(conv(embedded))
            # Global max pooling: [batch_size, num_filters]
            pooled = torch.max(conv_out, dim=2)[0]
            conv_outputs.append(pooled)

        # Concatenate multi-scale features: [batch_size, conv_output_dim]
        concatenated = torch.cat(conv_outputs, dim=1)

        # Project to output dimension: [batch_size, output_dim]
        output = self.projection(concatenated)

        # L2 normalization
        output = F.normalize(output, p=2, dim=1)

        return output

    def count_parameters(self) -> int:
        """Count total trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test CharCNN
    print("=" * 80)
    print("CharCNN Encoder Test")
    print("=" * 80)
    print()

    # Create model
    model = CharCNN(
        vocab_size=128,
        embed_dim=64,
        hidden_dim=256,
        output_dim=256,
        kernel_sizes=[3, 5, 7],
        num_filters=64,
        dropout=0.1
    )

    # Count parameters
    total_params = model.count_parameters()
    print(f"Total parameters: {total_params:,}")
    print()

    # Test forward pass
    batch_size = 4
    seq_len = 256
    char_ids = torch.randint(0, 128, (batch_size, seq_len))

    print(f"Input shape:  {char_ids.shape}")

    # Forward pass
    embeddings = model(char_ids)
    print(f"Output shape: {embeddings.shape}")

    # Check L2 normalization
    norms = torch.norm(embeddings, p=2, dim=1)
    print(f"L2 norms:     {norms}")
    print()

    # Test batch independence
    single_out = model(char_ids[0:1])
    batch_first = embeddings[0]
    print(f"Batch independence check: {torch.allclose(single_out[0], batch_first, atol=1e-6)}")
    print()

    print("=" * 80)

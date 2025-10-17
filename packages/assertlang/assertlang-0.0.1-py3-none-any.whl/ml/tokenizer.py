#!/usr/bin/env python3
"""
Character-level tokenizer for CharCNN.

ASCII vocabulary (128 characters):
- Printable ASCII: 32-126 (95 chars)
- Newline: 10
- Tab: 9
- Others mapped to 0 (unknown)
"""

import numpy as np
from typing import List


class CharTokenizer:
    """Character-level tokenizer with ASCII vocabulary."""

    def __init__(self, vocab_size: int = 128, max_length: int = 256):
        """
        Initialize tokenizer.

        Args:
            vocab_size: Vocabulary size (default 128 for ASCII)
            max_length: Maximum sequence length (default 256)
        """
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.pad_token = 0
        self.unk_token = 0

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text to character indices.

        Args:
            text: Input text string

        Returns:
            Array of character indices (shape: [max_length])
        """
        # Convert to ASCII codes
        char_ids = [ord(c) if ord(c) < self.vocab_size else self.unk_token
                   for c in text[:self.max_length]]

        # Pad to max_length
        if len(char_ids) < self.max_length:
            char_ids += [self.pad_token] * (self.max_length - len(char_ids))

        return np.array(char_ids, dtype=np.int32)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode batch of texts.

        Args:
            texts: List of text strings

        Returns:
            Array of character indices (shape: [batch_size, max_length])
        """
        return np.array([self.encode(text) for text in texts])

    def decode(self, char_ids: np.ndarray) -> str:
        """
        Decode character indices to text.

        Args:
            char_ids: Array of character indices

        Returns:
            Decoded text string
        """
        chars = [chr(int(idx)) for idx in char_ids if idx > 0 and idx < self.vocab_size]
        return ''.join(chars)


if __name__ == "__main__":
    # Test tokenizer
    tokenizer = CharTokenizer(vocab_size=128, max_length=256)

    test_cases = [
        'let content = file.read("data.txt")',
        'if file.exists(path)',
        'let parts = str.split(text, ",")',
        'for item in items',
    ]

    print("=" * 80)
    print("Character Tokenizer Test")
    print("=" * 80)
    print()

    for text in test_cases:
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        print(f"Original:  {text}")
        print(f"Shape:     {encoded.shape}")
        print(f"First 20:  {encoded[:20]}")
        print(f"Decoded:   {decoded}")
        print()

    # Batch encoding test
    batch = tokenizer.encode_batch(test_cases)
    print(f"Batch shape: {batch.shape}")
    print("=" * 80)

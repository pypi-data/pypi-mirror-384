#!/usr/bin/env python3
"""
Inference API for CharCNN operation lookup.

Provides fast, cached operation lookup for PW compiler integration.

Usage:
    from ml.inference import OperationLookup

    lookup = OperationLookup()
    predictions = lookup.predict("file.read(path)", top_k=3)

    # Returns: [('file.read', 0.95), ('file.read_text', 0.03), ...]
"""

import torch
import torch.nn.functional as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import time

from ml.tokenizer import CharTokenizer
from ml.encoders import CharCNN
from ml.losses import OperationEmbedding


class OperationLookup:
    """Fast operation lookup with CharCNN."""

    def __init__(
        self,
        model_path: str = "ml/charcnn_best.pt",
        device: Optional[str] = None,
        cache_embeddings: bool = True
    ):
        """
        Initialize operation lookup.

        Args:
            model_path: Path to trained model checkpoint
            device: Device to run on ('cpu', 'cuda', or None for auto)
            cache_embeddings: Pre-compute all operation embeddings (faster lookup)
        """
        self.model_path = model_path
        self.cache_embeddings = cache_embeddings

        # Setup device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        # Load checkpoint
        print(f"Loading model from {model_path}...")
        checkpoint = torch.load(model_path, map_location=self.device)

        # Get operation mappings
        self.operation_to_id = checkpoint['operation_to_id']
        self.id_to_operation = checkpoint['id_to_operation']
        self.num_operations = len(self.operation_to_id)

        print(f"Loaded {self.num_operations} operations")

        # Initialize tokenizer
        self.tokenizer = CharTokenizer(vocab_size=128, max_length=256)

        # Initialize CharCNN encoder
        self.model = CharCNN(
            vocab_size=128,
            embed_dim=64,
            hidden_dim=256,
            output_dim=256,
            kernel_sizes=[3, 5, 7],
            num_filters=64,
            dropout=0.1
        ).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        # Initialize operation embedding
        self.operation_emb = OperationEmbedding(
            num_operations=self.num_operations,
            embed_dim=256
        ).to(self.device)
        self.operation_emb.load_state_dict(checkpoint['operation_emb_state_dict'])
        self.operation_emb.eval()

        # Pre-compute operation embeddings for fast lookup
        self._operation_embeddings_cache = None
        if cache_embeddings:
            self._precompute_operation_embeddings()

        print(f"Model loaded on {self.device}")
        print(f"Ready for inference")

    def _precompute_operation_embeddings(self):
        """Pre-compute all operation embeddings for faster lookup."""
        print("Pre-computing operation embeddings...")
        with torch.no_grad():
            # All operation indices [0, 1, 2, ..., num_operations-1]
            operation_ids = torch.arange(self.num_operations, device=self.device)
            # Get embeddings: [num_operations, 256]
            self._operation_embeddings_cache = self.operation_emb(operation_ids)
        print(f"Cached {self.num_operations} operation embeddings")

    def predict(
        self,
        pw_code: str,
        top_k: int = 3,
        return_scores: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Predict operation from PW code snippet.

        Args:
            pw_code: PW code snippet (e.g., "file.read(path)")
            top_k: Number of predictions to return
            return_scores: Include confidence scores

        Returns:
            List of (operation_id, confidence) tuples sorted by confidence

        Example:
            >>> lookup.predict("file.read(path)", top_k=3)
            [('file.read', 0.95), ('file.read_text', 0.03), ('file.read_bytes', 0.01)]
        """
        # Tokenize input
        char_ids = self.tokenizer.encode(pw_code)
        char_ids_tensor = torch.tensor(char_ids, dtype=torch.long, device=self.device).unsqueeze(0)

        # Encode with CharCNN
        with torch.no_grad():
            code_embedding = self.model(char_ids_tensor)  # [1, 256]

            # Compute similarity to all operations
            if self._operation_embeddings_cache is not None:
                # Fast path: use cached embeddings
                operation_embeddings = self._operation_embeddings_cache  # [num_operations, 256]
            else:
                # Slow path: compute on demand
                operation_ids = torch.arange(self.num_operations, device=self.device)
                operation_embeddings = self.operation_emb(operation_ids)  # [num_operations, 256]

            # Cosine similarity: [1, num_operations]
            similarities = F.cosine_similarity(
                code_embedding.unsqueeze(1),  # [1, 1, 256]
                operation_embeddings.unsqueeze(0),  # [1, num_operations, 256]
                dim=2
            ).squeeze(0)  # [num_operations]

            # Get top-k predictions
            top_scores, top_indices = torch.topk(similarities, k=min(top_k, self.num_operations))

            # Convert to list
            results = []
            for idx, score in zip(top_indices.cpu().numpy(), top_scores.cpu().numpy()):
                operation_id = self.id_to_operation[int(idx)]
                confidence = float(score)
                results.append((operation_id, confidence))

            return results

    def predict_batch(
        self,
        pw_codes: List[str],
        top_k: int = 3
    ) -> List[List[Tuple[str, float]]]:
        """
        Predict operations for batch of PW code snippets.

        Args:
            pw_codes: List of PW code snippets
            top_k: Number of predictions per snippet

        Returns:
            List of prediction lists, one per input
        """
        # Tokenize batch
        char_ids_batch = self.tokenizer.encode_batch(pw_codes)
        char_ids_tensor = torch.tensor(char_ids_batch, dtype=torch.long, device=self.device)

        # Encode with CharCNN
        with torch.no_grad():
            code_embeddings = self.model(char_ids_tensor)  # [batch_size, 256]

            # Get operation embeddings
            if self._operation_embeddings_cache is not None:
                operation_embeddings = self._operation_embeddings_cache  # [num_operations, 256]
            else:
                operation_ids = torch.arange(self.num_operations, device=self.device)
                operation_embeddings = self.operation_emb(operation_ids)

            # Compute similarities: [batch_size, num_operations]
            similarities = F.cosine_similarity(
                code_embeddings.unsqueeze(1),  # [batch_size, 1, 256]
                operation_embeddings.unsqueeze(0),  # [1, num_operations, 256]
                dim=2
            )

            # Get top-k for each input
            top_scores, top_indices = torch.topk(similarities, k=min(top_k, self.num_operations), dim=1)

            # Convert to list of lists
            results = []
            for scores, indices in zip(top_scores.cpu().numpy(), top_indices.cpu().numpy()):
                predictions = []
                for idx, score in zip(indices, scores):
                    operation_id = self.id_to_operation[int(idx)]
                    confidence = float(score)
                    predictions.append((operation_id, confidence))
                results.append(predictions)

            return results

    def get_operation_list(self) -> List[str]:
        """Get list of all known operations."""
        return sorted(self.id_to_operation.values())

    def benchmark(self, num_iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark inference performance.

        Args:
            num_iterations: Number of iterations to run

        Returns:
            Dictionary with performance metrics
        """
        test_code = 'let content = file.read("data.txt")'

        # Warmup
        for _ in range(10):
            self.predict(test_code, top_k=1)

        # Benchmark single predictions
        start_time = time.time()
        for _ in range(num_iterations):
            self.predict(test_code, top_k=1)
        single_time = (time.time() - start_time) / num_iterations

        # Benchmark batch predictions
        batch_size = 32
        batch = [test_code] * batch_size

        start_time = time.time()
        for _ in range(num_iterations // batch_size):
            self.predict_batch(batch, top_k=1)
        batch_time = (time.time() - start_time) / num_iterations

        return {
            'single_latency_ms': single_time * 1000,
            'batch_latency_ms': batch_time * 1000,
            'throughput_ops_per_sec': 1.0 / single_time,
        }


# Global instance for quick imports
_global_lookup = None

def get_lookup() -> OperationLookup:
    """Get or create global OperationLookup instance."""
    global _global_lookup
    if _global_lookup is None:
        _global_lookup = OperationLookup()
    return _global_lookup


def lookup_operation(pw_code: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Convenience function for operation lookup.

    Args:
        pw_code: PW code snippet
        top_k: Number of predictions to return

    Returns:
        List of (operation_id, confidence) tuples
    """
    return get_lookup().predict(pw_code, top_k=top_k)


if __name__ == "__main__":
    print("=" * 80)
    print("CharCNN Inference API Test")
    print("=" * 80)
    print()

    # Initialize lookup
    lookup = OperationLookup()
    print()

    # Test cases
    test_cases = [
        'let content = file.read("data.txt")',
        'if file.exists(path)',
        'let parts = str.split(text, ",")',
        'let upper = str.upper(text)',
        'let data = http.get("https://api.example.com")',
        'let parsed = json.parse(text)',
        'array.push(items, item)',
        'for item in items',
    ]

    print("=" * 80)
    print("Single Predictions")
    print("=" * 80)
    print()

    for code in test_cases:
        predictions = lookup.predict(code, top_k=3)
        print(f"Code: {code}")
        print(f"Predictions:")
        for op_id, confidence in predictions:
            print(f"  {op_id:30s} {confidence:.4f}")
        print()

    # Batch prediction test
    print("=" * 80)
    print("Batch Predictions")
    print("=" * 80)
    print()

    batch_results = lookup.predict_batch(test_cases[:4], top_k=1)
    for code, predictions in zip(test_cases[:4], batch_results):
        top_op, confidence = predictions[0]
        print(f"{code:50s} → {top_op:20s} ({confidence:.4f})")
    print()

    # Benchmark
    print("=" * 80)
    print("Performance Benchmark")
    print("=" * 80)
    print()

    metrics = lookup.benchmark(num_iterations=1000)
    print(f"Single prediction latency: {metrics['single_latency_ms']:.3f} ms")
    print(f"Batch prediction latency:  {metrics['batch_latency_ms']:.3f} ms")
    print(f"Throughput:                {metrics['throughput_ops_per_sec']:.0f} ops/sec")
    print()

    # List all operations
    print("=" * 80)
    print(f"All Operations ({lookup.num_operations} total)")
    print("=" * 80)
    print()

    operations = lookup.get_operation_list()
    for i, op in enumerate(operations, 1):
        print(f"{i:3d}. {op}")

    print()
    print("=" * 80)

#!/usr/bin/env python3
"""
Test retrained CharCNN (large model) on realistic variations.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the realistic test generator
from validation.test_charcnn_realistic import generate_realistic_variations

# Import inference with large model
from ml.inference import OperationLookup

def main():
    print("=" * 80)
    print("CharCNN Validation - Large Model (9,760 training examples)")
    print("=" * 80)
    print()

    # Load large model
    lookup = OperationLookup(model_path='ml/charcnn_large.pt')
    print()

    # Load operations
    with open('training_dataset_large.json') as f:
        data = json.load(f)

    operations = sorted(set(ex['operation_id'] for ex in data))
    training_patterns = set(ex['pw_code'] for ex in data)

    print(f"Testing {len(operations)} operations")
    print(f"Generating realistic variations...")
    print()

    # Generate and test
    total_tests = 0
    total_correct = 0
    results_by_op = []

    for operation_id in operations:
        # Generate realistic variations
        variations = generate_realistic_variations(operation_id, count=10)

        # Filter out training patterns
        unseen = [v for v in variations if v not in training_patterns]

        if not unseen:
            continue

        # Test each variation
        correct = 0
        for pattern in unseen:
            try:
                preds = lookup.predict(pattern, top_k=1)
                if preds and preds[0][0] == operation_id:
                    correct += 1
            except:
                pass

        accuracy = correct / len(unseen) if unseen else 0
        results_by_op.append({
            'operation': operation_id,
            'tested': len(unseen),
            'correct': correct,
            'accuracy': accuracy
        })

        total_tests += len(unseen)
        total_correct += correct

    overall_accuracy = total_correct / total_tests if total_tests > 0 else 0

    # Results
    print("=" * 80)
    print("Results")
    print("=" * 80)
    print()
    print(f"Total tests: {total_tests}")
    print(f"Correct: {total_correct}")
    print(f"Overall accuracy: {overall_accuracy:.2%}")
    print()

    # Check success
    success_threshold = 0.90
    passed = overall_accuracy >= success_threshold

    if passed:
        print(f"✅ PASS: Accuracy {overall_accuracy:.2%} >= {success_threshold:.0%}")
        print()
        print("CharCNN generalizes well after retraining with 50x more data!")
    else:
        print(f"⚠️  PARTIAL: Accuracy {overall_accuracy:.2%} < {success_threshold:.0%}")
        print()
        print(f"Improvement from before: 47.74% → {overall_accuracy:.2%}")

    # Show worst performers
    print()
    print("=" * 80)
    print("Worst Performing Operations (bottom 10)")
    print("=" * 80)
    print()

    sorted_results = sorted(results_by_op, key=lambda x: x['accuracy'])
    for r in sorted_results[:10]:
        print(f"{r['operation']:30s} {r['correct']:2d}/{r['tested']:2d} ({r['accuracy']:.0%})")

    # Show best performers
    print()
    print("=" * 80)
    print("Best Performing Operations (top 10)")
    print("=" * 80)
    print()

    for r in sorted(results_by_op, key=lambda x: x['accuracy'], reverse=True)[:10]:
        print(f"{r['operation']:30s} {r['correct']:2d}/{r['tested']:2d} ({r['accuracy']:.0%})")

    # Save results
    output = {
        'model': 'charcnn_large.pt',
        'training_size': 9760,
        'total_tests': total_tests,
        'total_correct': total_correct,
        'overall_accuracy': overall_accuracy,
        'passed': passed,
        'results_by_operation': results_by_op
    }

    Path('validation').mkdir(exist_ok=True)
    with open('validation/charcnn_large_validation.json', 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print("Results saved to: validation/charcnn_large_validation.json")
    print()

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Quick test script for the MixFlow parameter extractor."""

from extrator_test import extract_mixflow_classes_from_file, print_mixflow_class_info

# Test on the test_workflow.py file
file_path = "test_workflow.py"
print(f"Extracting MixFlow classes from: {file_path}")
print("=" * 80)

classes = extract_mixflow_classes_from_file(file_path)

print(f"\nFound {len(classes)} MixFlow subclass(es):\n")

for cls in classes:
    print_mixflow_class_info(cls)

print("\n" + "=" * 80)
print("Extraction complete!")

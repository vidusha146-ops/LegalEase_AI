"""
LegalEase AI - Phase 5 Line Coverage Measurement Harness
========================================================
Uses Python's standard library trace module to compute line-level execution coverage
across all Phase 5 service modules during test execution.
"""

import sys
import os
import trace
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Create trace instance to track execution counts
tracer = trace.Trace(count=1, trace=0)

# Import and execute the audit function under the tracer
from tests.audit_phase5 import run_phase5_audit

tracer.runfunc(run_phase5_audit)

# Get results
results = tracer.results()

# Define Phase 5 service files to analyze
target_files = [
    "document_intelligence.py",
    "information_extraction.py",
    "evidence_classifier.py",
    "timeline_engine.py",
    "consistency_analyzer.py",
    "evidence_mapper.py",
]

print("\n" + "=" * 80)
print("PHASE 5 LINE-LEVEL CODE EXECUTION COVERAGE BENCHMARK")
print("=" * 80)
print(f"{'Target Module':35s} | {'Executable Lines':18s} | {'Executed Lines':16s} | {'Coverage %':10s}")
print("-" * 80)

total_executable = 0
total_executed = 0

for root, _, files in os.walk(os.path.join(BACKEND_DIR, "app", "services")):
    for f in files:
        if f in target_files:
            file_path = os.path.join(root, f)
            # Read all lines in file to find non-empty, non-comment lines
            with open(file_path, "r", encoding="utf-8") as fp:
                lines = fp.readlines()

            executable_lines = []
            for idx, line in enumerate(lines, 1):
                stripped = line.strip()
                if (
                    stripped
                    and not stripped.startswith("#")
                    and not stripped.startswith('"""')
                    and not stripped.startswith("'''")
                ):
                    executable_lines.append(idx)

            executed_lines = [
                line_no
                for (filename, line_no), count in results.counts.items()
                if os.path.abspath(filename) == os.path.abspath(file_path) and count > 0
            ]

            num_exec = len(executable_lines)
            num_covered = len([l for l in executed_lines if l in executable_lines])
            cov_pct = (num_covered / num_exec * 100.0) if num_exec > 0 else 100.0

            total_executable += num_exec
            total_executed += num_covered

            print(f"{f:35s} | {num_exec:18d} | {num_covered:16d} | {cov_pct:9.1f}%")

total_cov = (total_executed / total_executable * 100.0) if total_executable > 0 else 0.0
print("-" * 80)
print(f"{'OVERALL PHASE 5 SERVICES':35s} | {total_executable:18d} | {total_executed:16d} | {total_cov:9.1f}%")
print("=" * 80)

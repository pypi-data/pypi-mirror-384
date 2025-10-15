#!/usr/bin/env python3
"""
Enhanced profiling analysis script for sq3_profile.prof
"""

import pstats
from pathlib import Path


def analyze_profile():
    profile_file = Path(__file__).parent / "sq3_profile.prof"

    if not profile_file.exists():
        print(f"Profile file not found: {profile_file}")
        print("Run sq3-only.py first to generate the profile")
        return

    stats = pstats.Stats(str(profile_file))
    stats.strip_dirs()

    print("=" * 80)
    print("DETAILED ANALYSIS OF SQ3 PROFILING")
    print("=" * 80)

    print("\n1. EKFSM MODULE ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"ekfsm", 15)

    print("\n2. IO4EDGE_CLIENT MODULE ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"io4edge_client", 15)

    print("\n3. SOCKET/TRANSPORT LAYER ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"socket|transport", 10)

    print("\n4. DISPLAY OPERATIONS ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"display|pixel|image", 10)

    print("\n5. BUTTON OPERATIONS ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"button|read_stream", 10)

    print("\n6. MOST TIME-CONSUMING FUNCTIONS (ALL)")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(20)

    print("\n7. FUNCTIONS WITH MOST CALLS")
    print("-" * 40)
    stats.sort_stats("ncalls").print_stats(15)

    print("\n8. CUMULATIVE TIME ANALYSIS")
    print("-" * 40)
    stats.sort_stats("cumtime").print_stats(15)


if __name__ == "__main__":
    analyze_profile()

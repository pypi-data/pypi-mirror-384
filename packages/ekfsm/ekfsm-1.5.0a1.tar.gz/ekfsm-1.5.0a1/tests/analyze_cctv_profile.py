#!/usr/bin/env python3
"""
Enhanced profiling analysis script for cctv_profile.prof
Analyzes CCTV system profiling results focusing on:
- Watchdog operations
- LED control functions
- Button array operations
- ekfsm and io4edge_client module usage
"""

import pstats
from pathlib import Path


def analyze_cctv_profile():
    profile_file = Path(__file__).parent / "cctv_profile.prof"

    if not profile_file.exists():
        print(f"Profile file not found: {profile_file}")
        print("Run cctv.py first to generate the profile")
        return

    stats = pstats.Stats(str(profile_file))
    stats.strip_dirs()

    print("=" * 80)
    print("DETAILED ANALYSIS OF CCTV PROFILING")
    print("=" * 80)

    print("\n1. EKFSM MODULE ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"ekfsm", 15)

    print("\n2. IO4EDGE_CLIENT MODULE ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"io4edge_client", 15)

    print("\n3. WATCHDOG OPERATIONS ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"watchdog|kick", 10)

    print("\n4. LED CONTROL OPERATIONS ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"led|colorLED|set", 10)

    print("\n5. BUTTON OPERATIONS ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"button|eject|read_stream", 10)

    print("\n6. SOCKET/TRANSPORT LAYER ANALYSIS")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(r"socket|transport", 10)

    print("\n7. MOST TIME-CONSUMING FUNCTIONS (ALL)")
    print("-" * 40)
    stats.sort_stats("tottime").print_stats(20)

    print("\n8. FUNCTIONS WITH MOST CALLS")
    print("-" * 40)
    stats.sort_stats("ncalls").print_stats(15)

    print("\n9. CUMULATIVE TIME ANALYSIS")
    print("-" * 40)
    stats.sort_stats("cumtime").print_stats(15)

    print("\n10. CCTV-SPECIFIC HARDWARE INTERACTIONS")
    print("-" * 40)
    # Look for CCTV-specific patterns
    stats.sort_stats("tottime").print_stats(r"smc|i4e", 10)


if __name__ == "__main__":
    analyze_cctv_profile()

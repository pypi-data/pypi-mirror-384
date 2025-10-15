import logging
import pprint
from pathlib import Path
import cProfile
import pstats

from ekfsm.system import System

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize system first (without profiling the setup)
config = Path(__file__).parent / "sq3-only.yaml"
system = System(config, abort=True)

pprint.pprint(f"System slots {system.slots}")

system.print()

cpu = system["CPU"]
cpuB = system.cpu
cpuC = system[0]

assert cpu == cpuB == cpuC

print(cpu.hwmon.cputemp())

eeprom = cpu.eeprom
eeprom.manufactured_at()

cpu_slot = system.slots["SYSTEM_SLOT"]
cpu_slotB = system.slots.SYSTEM_SLOT
cpu_slotC = system.slots[0]

assert cpu_slot == cpu_slotB == cpu_slotC

cpu.print()
print(f"probing CPU: {cpu.probe()}")
print(
    f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}"
)

sq3 = system["info"]
i4e = sq3.bmc

# Start profiling HIER - nach System-Setup, vor io4edge_client Aufrufen
profiler = cProfile.Profile(builtins=False)
profiler.enable()

fw_title, fw_name = i4e.identify_firmware()

print(f"Firmware: {fw_title} {fw_name}")

pixel = i4e.display

pixel.off()
pixel.display_image(str(Path(__file__).parent / "sim/SQ3.png"))


profiler.disable()

print("\n" + "=" * 80)
print("PROFILING RESULTS - ekfsm and io4edge_client modules")
print("=" * 80)

# Create stats object and filter for our modules
stats = pstats.Stats(profiler)
stats.strip_dirs()  # clean paths

# Print comprehensive profiling results
print("\n1. TOP FUNCTIONS BY TOTAL TIME (including subcalls)")
stats.sort_stats("tottime").print_stats(
    r"ekfsm|io4edge_client|client\.py|display|button", 30
)

print("\n2. TOP FUNCTIONS BY CUMULATIVE TIME (time + subcalls)")
stats.sort_stats("cumtime").print_stats(
    r"ekfsm|io4edge_client|client\.py|display|button", 30
)

print("\n3. TOP FUNCTIONS BY NUMBER OF CALLS")
stats.sort_stats("ncalls").print_stats(
    r"ekfsm|io4edge_client|client\.py|display|button", 20
)

print("\n3a. ALL FUNCTIONS - DEBUGGING VIEW (to see what's actually being called)")
stats.sort_stats("tottime").print_stats(50)  # Show top 50 functions overall

print("\n4. CALLERS/CALLEES ANALYSIS FOR TOP 5 FUNCTIONS")
# Get the top 5 functions by total time
top_funcs = stats.get_stats_profile().func_profiles
filtered_funcs = {
    k: v
    for k, v in top_funcs.items()
    if any(mod in str(k) for mod in ["ekfsm", "io4edge_client"])
}
sorted_funcs = sorted(filtered_funcs.items(), key=lambda x: x[1].tottime, reverse=True)

for i, (func_key, func_stats) in enumerate(sorted_funcs[:5]):
    print(f"\n--- Function #{i+1}: {func_key} ---")
    print(f"Total time: {func_stats.tottime:.6f}s, Calls: {func_stats.ncalls}")
    stats.print_callers(func_key)

# Save detailed profile to file for later analysis
profile_file = Path(__file__).parent / "sq3_profile.prof"
profiler.dump_stats(str(profile_file))
print(f"\n5. Detailed profile saved to: {profile_file}")
print("   Use: python -m pstats sq3_profile.prof")
print("   Or: snakeviz sq3_profile.prof (install: pip install snakeviz)")

print("\n" + "=" * 80)

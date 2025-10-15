import pprint
import logging
from pathlib import Path
import threading
from time import sleep
import cProfile
import pstats

from ekfsm.system import System

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize system first (without profiling the setup)
config = Path(__file__).parent / "cctv.yaml"
try:
    system = System(config, abort=True)
    system_initialized = True
except Exception as e:
    print(f"System initialization failed: {e}")
    print("Continuing with mock profiling demonstration...")
    system_initialized = False
    system = None

if not system_initialized:
    print("System not available, creating mock profiling demonstration...")
    print(
        "This demonstrates the profiling structure that would be used with real hardware."
    )
    print("The same profiling patterns from sq3-only.py can be applied here.")
    exit(0)

# Start profiling HIER - nach System-Setup, vor io4edge_client Aufrufen
profiler = cProfile.Profile(builtins=False)
profiler.enable()

try:
    pprint.pprint(f"System slots {system.slots}")

    system.print()

    print(system.smc.i4e.leds.client._fb_client.connected)

    cpu = system["CPU"]
    cpuB = system.cpu
    cpuC = system[0]

    assert cpu == cpuB == cpuC

    # To check why below is failing
    # cpu_slot = system.slots["SYSTEM_SLOT"]
    # cpu_slotB = system.slots.SYSTEM_SLOT
    # cpu_slotC = system.slots[0]

    # assert cpu_slot == cpu_slotB == cpu_slotC

    cpu.print()
    print(f"probing CPU: {cpu.probe()}")
    print(
        f"inventory: {cpu.inventory.vendor()} {cpu.inventory.model()} {cpu.inventory.serial()}"
    )

    smc = system.smc

    smc.print()

    i4e = smc.i4e
    i4e.watchdog.kick()
    print(i4e.watchdog.client._fb_client.connected)
    i4e.leds.led2.set(0, True)
    print(system.smc.i4e.leds.client._fb_client.connected)
    i4e.leds.led5.set(3, True)
    print(system.smc.i4e.leds.client._fb_client.connected)
    i4e.leds.led3.set(5, False)
    print(system.smc.i4e.leds.client._fb_client.connected)

    button_array = i4e.buttons
    # print(button_array._client._fb_client.connected)

    eject = button_array.eject

    eject.handler = lambda: print("Eject pressed")

    stop_event = threading.Event()
    button_thread = threading.Thread(target=button_array.read, args=(stop_event,))
    button_thread.start()

    for i in range(30):
        print("Main thread running...")
        # i4e.watchdog.kick()
        # print(i4e.watchdog.client._fb_client.connected)
        # i4e.leds.led2.set(0, True)
        # print(system.smc.i4e.leds.client._fb_client.connected)
        # i4e.leds.led5.set(3, True)
        # print(system.smc.i4e.leds.client._fb_client.connected)
        # i4e.leds.led3.set(5, False)
        # print(system.smc.i4e.leds.client._fb_client.connected)
        sleep(1)

    # To stop the thread:
    stop_event.set()
    button_thread.join()

except Exception as e:
    print(f"Error during execution: {e}")
    print("This is expected on systems without the required hardware.")

finally:
    profiler.disable()

    print("\n" + "=" * 80)
    print("PROFILING RESULTS - ekfsm and io4edge_client modules (CCTV)")
    print("=" * 80)

    # Create stats object and filter for our modules
    stats = pstats.Stats(profiler)
    stats.strip_dirs()  # clean paths

    # Print comprehensive profiling results
    print("\n1. TOP FUNCTIONS BY TOTAL TIME (including subcalls)")
    stats.sort_stats("tottime").print_stats(
        r"ekfsm|io4edge_client|client\.py|watchdog|led|button", 30
    )

    print("\n2. TOP FUNCTIONS BY CUMULATIVE TIME (time + subcalls)")
    stats.sort_stats("cumtime").print_stats(
        r"ekfsm|io4edge_client|client\.py|watchdog|led|button", 30
    )

    print("\n3. TOP FUNCTIONS BY NUMBER OF CALLS")
    stats.sort_stats("ncalls").print_stats(
        r"ekfsm|io4edge_client|client\.py|watchdog|led|button", 20
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
    sorted_funcs = sorted(
        filtered_funcs.items(), key=lambda x: x[1].tottime, reverse=True
    )

    for i, (func_key, func_stats) in enumerate(sorted_funcs[:5]):
        print(f"\n--- Function #{i+1}: {func_key} ---")
        print(f"Total time: {func_stats.tottime:.6f}s, Calls: {func_stats.ncalls}")
        stats.print_callers(func_key)

    # Save detailed profile to file for later analysis
    profile_file = Path(__file__).parent / "cctv_profile.prof"
    profiler.dump_stats(str(profile_file))
    print(f"\n5. Detailed profile saved to: {profile_file}")
    print("   Use: python -m pstats cctv_profile.prof")
    print("   Or: snakeviz cctv_profile.prof (install: pip install snakeviz)")

    print("\n" + "=" * 80)

#!/usr/bin/env python3
"""
Template für Profiling von ekfsm und io4edge_client Modulen

Dieses Template zeigt, wie das Profiling-Prinzip auf beliebige Scripts angewendet wird.
Kopieren Sie diesen Code und passen Sie ihn an Ihr spezifisches Script an.

Verwendung:
1. Importieren Sie cProfile und pstats
2. Initialisieren Sie das System OHNE Profiling
3. Starten Sie das Profiling VOR den io4edge_client Aufrufen
4. Führen Sie Ihre io4edge_client/ekfsm Operationen aus
5. Stoppen Sie das Profiling und analysieren Sie die Ergebnisse
"""

import cProfile
import pstats
from pathlib import Path
import logging

# Optional: Setzen Sie Logging-Level für bessere Sichtbarkeit
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def profile_ekfsm_io4edge_operations():
    """
    Template-Funktion für Profiling von ekfsm und io4edge_client Operationen
    """

    # SCHRITT 1: System-Initialisierung OHNE Profiling
    print("Initializing system...")
    try:
        from ekfsm.system import System

        # Passen Sie den Konfigurationspfad an Ihr Script an
        config = Path(__file__).parent / "your-config.yaml"
        system = System(config, abort=True)
        system_available = True

    except Exception as e:
        print(f"System initialization failed: {e}")
        print("Continuing with demonstration of profiling structure...")
        system_available = False

    if not system_available:
        print("\n" + "=" * 60)
        print("PROFILING TEMPLATE STRUCTURE")
        print("=" * 60)
        print("1. Import cProfile and pstats")
        print("2. Initialize system WITHOUT profiling")
        print("3. Start profiler BEFORE io4edge_client calls")
        print("4. Execute your io4edge_client operations")
        print("5. Stop profiler and analyze results")
        print("6. Filter results for ekfsm|io4edge_client modules")
        return

    # SCHRITT 2: Profiling starten - NACH System-Setup, VOR io4edge_client Aufrufen
    print("Starting profiler...")
    profiler = cProfile.Profile(builtins=False)
    profiler.enable()

    try:
        # SCHRITT 3: Ihre io4edge_client/ekfsm Operationen hier
        print("Executing monitored operations...")

        # Beispiel-Operationen (passen Sie diese an Ihr Script an):

        # System-Operationen
        system.print()

        # Beispiel: CPU-Zugriff
        cpu = system["CPU"]  # Ändern Sie "CPU" entsprechend Ihrer Konfiguration
        cpu.print()

        # Beispiel: Hardware-Module Zugriff
        # board = system["your_board_name"]
        # i4e = board.your_io4edge_device

        # Beispiel: io4edge_client Operationen
        # i4e.watchdog.kick()
        # i4e.leds.led1.set(0, True)
        # button_array = i4e.buttons
        # button_array.some_button.handler = lambda: print("Button pressed")

        # Beispiel: Streaming-Operationen
        # stop_event = threading.Event()
        # button_thread = threading.Thread(target=button_array.read, args=(stop_event,))
        # button_thread.start()
        # time.sleep(5)  # Simulate some work
        # stop_event.set()
        # button_thread.join()

        print("Operations completed successfully")

    except Exception as e:
        print(f"Error during monitored operations: {e}")

    finally:
        # SCHRITT 4: Profiling stoppen und analysieren
        profiler.disable()

        print("\n" + "=" * 80)
        print("PROFILING RESULTS - ekfsm and io4edge_client modules")
        print("=" * 80)

        # Stats-Objekt erstellen
        stats = pstats.Stats(profiler)
        stats.strip_dirs()

        # SCHRITT 5: Analysieren Sie die Ergebnisse

        print("\n1. TOP FUNCTIONS BY TOTAL TIME")
        # Passen Sie den Regex-Filter an Ihre spezifischen Module an
        stats.sort_stats("tottime").print_stats(r"ekfsm|io4edge_client|your_module", 20)

        print("\n2. TOP FUNCTIONS BY CUMULATIVE TIME")
        stats.sort_stats("cumtime").print_stats(r"ekfsm|io4edge_client|your_module", 20)

        print("\n3. TOP FUNCTIONS BY NUMBER OF CALLS")
        stats.sort_stats("ncalls").print_stats(r"ekfsm|io4edge_client|your_module", 15)

        print("\n4. ALL FUNCTIONS OVERVIEW")
        stats.sort_stats("tottime").print_stats(30)

        # SCHRITT 6: Profiling-Datei speichern für detaillierte Analyse
        profile_file = Path(__file__).parent / "your_script_profile.prof"
        profiler.dump_stats(str(profile_file))

        print(f"\n5. PROFILE FILE SAVED: {profile_file}")
        print(f"   Detailed analysis: python -m pstats {profile_file}")
        print(f"   Visual analysis: pip install snakeviz && snakeviz {profile_file}")

        print("\n" + "=" * 80)


def create_profile_analysis_script(script_name):
    """
    Erstellt ein Analyse-Script für ein spezifisches Profiling
    """
    analysis_script = f"""#!/usr/bin/env python3
'''
Analysis script for {script_name}_profile.prof
'''

import pstats
from pathlib import Path

def analyze_{script_name}_profile():
    profile_file = Path(__file__).parent / "{script_name}_profile.prof"

    if not profile_file.exists():
        print(f"Profile file not found: {{profile_file}}")
        return

    stats = pstats.Stats(str(profile_file))
    stats.strip_dirs()

    print("="*80)
    print("DETAILED ANALYSIS OF {script_name.upper()} PROFILING")
    print("="*80)

    # Modulspezifische Analysen
    print("\\n1. EKFSM MODULE ANALYSIS")
    stats.sort_stats("tottime").print_stats(r"ekfsm", 15)

    print("\\n2. IO4EDGE_CLIENT MODULE ANALYSIS")
    stats.sort_stats("tottime").print_stats(r"io4edge_client", 15)

    # Fügen Sie hier weitere spezifische Analysen ein

if __name__ == "__main__":
    analyze_{script_name}_profile()
"""

    analysis_file = Path(__file__).parent / f"analyze_{script_name}_profile.py"
    analysis_file.write_text(analysis_script)
    print(f"Analysis script created: {analysis_file}")


if __name__ == "__main__":
    print("PROFILING TEMPLATE FOR EKFSM AND IO4EDGE_CLIENT")
    print("=" * 50)
    profile_ekfsm_io4edge_operations()

    # Optional: Erstellen Sie ein Analyse-Script
    # create_profile_analysis_script("your_script_name")

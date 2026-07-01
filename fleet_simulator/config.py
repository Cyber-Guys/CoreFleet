# NOTE: `from .types import DriverProfile` lives at the BOTTOM of this module.
# The `types` submodules import the constants below, so the constants must be
# defined before `types` is imported, otherwise the import cycle breaks.

# ---------------------------------------------------------------------------
# Costanti fisiche / di simulazione
# ---------------------------------------------------------------------------
IDLE_RPM = 820
MAX_RPM = 6800
WHEEL_CIRCUMFERENCE_M = 2.0  # circonferenza ruota
FINAL_DRIVE = 4.0
GEAR_RATIOS = [None, 3.5, 2.05, 1.35, 1.0, 0.8]  # marce 1..5 (None = indice 0)
COLD_THRESHOLD_C = 60.0  # sotto questa T il motore è "freddo"
AMBIENT_C = 18.0
TARGET_COOLANT_C = 91.0
COOLANT_TAU_S = 170.0  # costante di tempo riscaldamento motore


# Soglie eventi di guida (valori assoluti, fisicamente sensati)
HARSH_ACCEL_MS2 = 3.0
HARSH_BRAKE_MS2 = -3.5
OVERREV_RPM = 4500
IDLE_SPEED_MS = 0.6  # sotto = fermo


# Stima energia di trasmissione: SOLO indicativa, da giustificare nel report.
# Ordine di grandezza per radio cellulare in trasmissione attiva.
JOULES_PER_MB = 1100.0


# Imported here (not at top) to avoid a circular import: the `types` package
# reads the constants defined above during its own import.
from .types import DriverProfile  # noqa: E402


# Tipologie di guidatore predefinite, da usare per le simulazioni
PROFILES = {
    "aggressive": DriverProfile(
        name="aggressive", accel_peak=4.2, brake_peak=4.8,
        shift_rpm=5200, overshoot=0.22, idle_tendency=0.35,
        cold_aggression=0.85, jerk_noise=0.9, reaction_s=1.6
    ),

    "normal": DriverProfile(
        name="normal", accel_peak=2.4, brake_peak=2.8,
        shift_rpm=3200, overshoot=0.06, idle_tendency=0.25,
        cold_aggression=0.40, jerk_noise=0.35, reaction_s=3.0
    ),

    "calm": DriverProfile(
        name="calm", accel_peak=1.5, brake_peak=1.8,
        shift_rpm=2500, overshoot=0.0, idle_tendency=0.20,
        cold_aggression=0.10, jerk_noise=0.15, reaction_s=4.5
    ),
}


# Limiti di velocità per tipo di strada (km/h)
SPEED_LIMITS_KMH = [30, 50, 50, 70, 90, 110, 130]


# Consumo asset per visualizzazione (semplificato, non fisico):
# carburante e olio calano col chilometraggio del trip.
FUEL_PCT_PER_KM = 8.0     # % serbatoio consumata per km
OIL_PCT_PER_KM = 1.2      # % olio consumata per km
OIL_BASE_WEAR = 0.3       # usura olio fissa per trip


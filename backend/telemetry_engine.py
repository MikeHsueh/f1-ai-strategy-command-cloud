import math
from pathlib import Path

import joblib
import numpy as np


FEATURE_COLUMNS = [
    "LapNumber",
    "LapRatio",
    "Stint",
    "TyreLife",
    "RemainingLaps",
    "FuelLoad",
    "Soft",
    "Medium",
    "Hard",
    "Intermediate",
    "Wet",
    "IsDryTyre",
    "IsWetTyre",
    "AvgSpeed",
    "MaxSpeed",
    "SpeedStd",
    "ThrottleMean",
    "ThrottleStd",
    "BrakeMean",
    "BrakeRatio",
    "RPMMean",
    "RPMStd",
    "AirTemp",
    "TrackTemp",
    "Humidity",
    "Rainfall",
    "TrackAirDiff",
    "WetConditionIndex",
    "Degradation",
    "RollingDegradation",
    "PaceDelta",
    "MovingAverageLapTime",
    "LapTimeTrend",
    "TireTemperatureProxy",
    "PitWindowScore",
    "IsLateStint",
    "LongRunFlag",
    "PerformanceLossRate",
    "NormalizedPaceLoss",
    "PitPressureIndex",
]

FEATURE_CENTER = np.array([
    35.0, 0.50, 2.0, 13.0, 27.0, 55.0,
    0.25, 0.35, 0.30, 0.04, 0.02, 0.90, 0.08,
    220.0, 320.0, 58.0, 63.0, 28.0, 18.0, 0.18, 10800.0, 1700.0,
    23.0, 35.0, 55.0, 0.05, 12.0, 0.03,
    0.35, 0.05, 1.8, 91.0, 0.03, 92.0,
    0.36, 0.25, 0.12, 0.006, 0.025, 0.34,
], dtype=np.float32)

FEATURE_SCALE = np.array([
    24.0, 0.29, 1.0, 10.0, 23.0, 32.0,
    0.43, 0.48, 0.46, 0.20, 0.14, 0.30, 0.27,
    55.0, 35.0, 24.0, 25.0, 16.0, 23.0, 0.20, 1700.0, 950.0,
    6.0, 10.0, 18.0, 0.22, 12.0, 0.16,
    0.80, 0.45, 2.8, 12.0, 0.35, 18.0,
    0.25, 0.43, 0.32, 0.018, 0.035, 0.25,
], dtype=np.float32)

BACKEND_DIR = Path(__file__).resolve().parent
SCALER_CANDIDATES = [
    BACKEND_DIR / "scaler_40.pkl",
    BACKEND_DIR / "scaler_attention_40.pkl",
]


def _load_scaler():
    for path in SCALER_CANDIDATES:
        if not path.exists():
            continue

        scaler = joblib.load(path)
        if getattr(scaler, "n_features_in_", None) == len(FEATURE_COLUMNS):
            return scaler, str(path)

    return None, None


FEATURE_SCALER, FEATURE_SCALER_PATH = _load_scaler()


def _num(payload, key, default=0.0):
    try:
        value = payload.get(key, default)
        if value is None:
            return float(default)
        value = float(value)
        if not math.isfinite(value):
            return float(default)
        return value
    except Exception:
        return float(default)


def _clip(value, lower, upper):
    return float(np.clip(float(value), lower, upper))


def _compound_flags(compound):
    compound = str(compound or "MEDIUM").upper()
    soft = 1.0 if compound == "SOFT" else 0.0
    medium = 1.0 if compound == "MEDIUM" else 0.0
    hard = 1.0 if compound == "HARD" else 0.0
    intermediate = 1.0 if compound in {"INTER", "INTERMEDIATE"} else 0.0
    wet = 1.0 if compound == "WET" else 0.0
    return soft, medium, hard, intermediate, wet, float(soft + medium + hard > 0), float(intermediate + wet > 0)


def _expected_tyre_life(compound):
    compound = str(compound or "MEDIUM").upper()
    if compound == "SOFT":
        return 18.0
    if compound == "MEDIUM":
        return 26.0
    if compound == "HARD":
        return 36.0
    if compound in {"INTER", "INTERMEDIATE"}:
        return 20.0
    if compound == "WET":
        return 24.0
    return 28.0


def calculate_tire_health(compound, tyre_life, degradation=None):
    """Estimate remaining tire health from compound life and degradation."""
    compound = str(compound or "MEDIUM").upper()
    tyre_life = max(0.0, float(tyre_life or 0.0))
    if degradation is None:
        degradation = tyre_life * 0.055
    health = 100.0 - (tyre_life / max(_expected_tyre_life(compound), 1.0)) * 72.0 - max(0.0, float(degradation)) * 8.0
    return round(_clip(health, 5.0, 100.0), 1)


def _tire_temperature_proxy(speed, throttle, brake, track_temp, tyre_life, compound, rainfall, humidity):
    speed_norm = _clip(speed, 0.0, 360.0) / 360.0
    throttle_norm = _clip(throttle, 0.0, 100.0) / 100.0
    brake_norm = _clip(brake, 0.0, 100.0) / 100.0
    age_norm = _clip(tyre_life / max(_expected_tyre_life(compound), 1.0), 0.0, 1.8)
    wet_cooling = (1.0 if rainfall else 0.0) * (10.0 + 8.0 * (_clip(humidity, 0.0, 100.0) / 100.0))

    compound_offset = {
        "SOFT": 4.0,
        "MEDIUM": 1.0,
        "HARD": -2.0,
        "INTER": -8.0,
        "INTERMEDIATE": -8.0,
        "WET": -12.0,
    }.get(str(compound).upper(), 0.0)

    temp = track_temp + 42.0 * speed_norm + 18.0 * throttle_norm + 22.0 * brake_norm + 7.0 * age_norm + compound_offset - wet_cooling
    return _clip(temp, 35.0, 145.0)


def _pit_window_score(tyre_life, remaining_laps, degradation, normalized_pace_loss, compound, total_laps, rainfall, humidity):
    age_score = _clip(tyre_life / max(_expected_tyre_life(compound), 1.0), 0.0, 1.25) / 1.25
    deg_score = _clip((degradation + 0.75) / 5.0, 0.0, 1.0)
    pace_score = _clip(normalized_pace_loss / 0.07, 0.0, 1.0)
    progress_score = _clip(1.0 - remaining_laps / max(total_laps, 1.0), 0.0, 1.0)
    wet_score = _clip((float(bool(rainfall)) + humidity / 100.0) / 2.0, 0.0, 1.0)
    return _clip(0.30 * age_score + 0.25 * deg_score + 0.20 * pace_score + 0.15 * progress_score + 0.10 * wet_score, 0.0, 1.0)


def _pit_pressure_index(pit_window_score, tyre_life, degradation, performance_loss_rate, normalized_pace_loss, remaining_laps, compound):
    age_pressure = _clip(tyre_life / max(_expected_tyre_life(compound), 1.0), 0.0, 1.5) / 1.5
    deg_pressure = _clip(degradation / 4.0, 0.0, 1.0)
    rate_pressure = _clip(performance_loss_rate / 0.05, 0.0, 1.0)
    pace_pressure = _clip(normalized_pace_loss / 0.07, 0.0, 1.0)
    remaining_pressure = _clip(1.0 / max(remaining_laps, 1.0), 0.0, 1.0)
    return _clip(0.35 * pit_window_score + 0.20 * age_pressure + 0.15 * deg_pressure + 0.15 * rate_pressure + 0.10 * pace_pressure + 0.05 * remaining_pressure, 0.0, 1.0)


def _build_row(payload, step_offset):
    circuit = payload.get("circuit", "Silverstone")
    total_laps = max(_num(payload, "total_laps", payload.get("TotalLaps", 52)), 1.0)
    lap = _clip(_num(payload, "lap", 1) - step_offset, 1.0, total_laps)
    tyre_life = max(0.0, _num(payload, "tire_age", payload.get("TyreLife", 0)) - step_offset)
    stint = max(1.0, _num(payload, "current_stint", 1))
    compound = payload.get("compound", "MEDIUM")
    soft, medium, hard, intermediate, wet, is_dry, is_wet = _compound_flags(compound)

    remaining_laps = max(0.0, total_laps - lap)
    lap_ratio = _clip(lap / total_laps, 0.0, 1.0)
    fuel_load = _clip(_num(payload, "fuel_load", 110.0 * (1.0 - lap_ratio)), 0.0, 110.0)

    speed = _clip(_num(payload, "speed", 250.0) - step_offset * 1.8, 0.0, 380.0)
    max_speed = _clip(_num(payload, "max_speed", min(380.0, speed + 34.0)), 0.0, 380.0)
    speed_std = _clip(_num(payload, "speed_std", 42.0 + (1.0 - _num(payload, "throttle", 70.0) / 100.0) * 28.0), 0.0, 140.0)
    throttle = _clip(_num(payload, "throttle", 70.0), 0.0, 100.0)
    throttle_std = _clip(_num(payload, "throttle_std", max(8.0, 35.0 - throttle * 0.18)), 0.0, 60.0)
    brake = _clip(_num(payload, "brake", 12.0), 0.0, 100.0)
    brake_ratio = _clip(_num(payload, "brake_ratio", brake / 100.0), 0.0, 1.0)
    rpm = _clip(_num(payload, "rpm", 10800.0), 0.0, 20000.0)
    rpm_std = _clip(_num(payload, "rpm_std", 780.0 + speed_std * 13.0), 0.0, 8000.0)

    air_temp = _clip(_num(payload, "air_temp", 23.0), -20.0, 60.0)
    track_temp = _clip(_num(payload, "track_temp", 35.0), -20.0, 85.0)
    humidity = _clip(_num(payload, "humidity", 55.0), 0.0, 100.0)
    rain_risk = _clip(_num(payload, "rain_risk", 0.0), 0.0, 100.0)
    rainfall = 1.0 if rain_risk >= 55.0 or str(compound).upper() in {"INTER", "INTERMEDIATE", "WET"} else 0.0
    track_air_diff = track_temp - air_temp
    wet_condition_index = rainfall * humidity / 100.0

    base_degradation = tyre_life * 0.055 + max(0.0, track_temp - 30.0) * 0.018 + brake_ratio * 0.16
    degradation = _clip(base_degradation, -10.0, 20.0)
    rolling_degradation = _clip(0.010 * tyre_life + max(0.0, track_temp - 35.0) * 0.002, -5.0, 5.0)
    normalized_pace_loss = _clip(0.0035 * tyre_life + 0.004 * degradation + brake_ratio * 0.004, 0.0, 0.35)
    pace_delta = _clip(normalized_pace_loss * 92.0, 0.0, 120.0)
    moving_average_lap_time = _clip(_num(payload, "lap_time", 91.0) + pace_delta * 0.30, 0.0, 300.0)
    lap_time_trend = _clip(rolling_degradation + normalized_pace_loss * 0.25, -5.0, 5.0)
    tire_temp = _tire_temperature_proxy(speed, throttle, brake, track_temp, tyre_life, compound, rainfall, humidity)
    perf_loss_rate = _clip(normalized_pace_loss / max(tyre_life + 1.0, 1.0), -0.03, 0.12)
    is_late_stint = 1.0 if tyre_life >= 0.65 * _expected_tyre_life(compound) else 0.0
    long_run_flag = 1.0 if tyre_life >= 0.80 * _expected_tyre_life(compound) else 0.0
    pit_window = _pit_window_score(tyre_life, remaining_laps, degradation, normalized_pace_loss, compound, total_laps, rainfall, humidity)
    pit_pressure = _pit_pressure_index(pit_window, tyre_life, degradation, perf_loss_rate, normalized_pace_loss, remaining_laps, compound)

    return [
        lap, lap_ratio, stint, tyre_life, remaining_laps, fuel_load,
        soft, medium, hard, intermediate, wet, is_dry, is_wet,
        speed, max_speed, speed_std, throttle, throttle_std, brake, brake_ratio, rpm, rpm_std,
        air_temp, track_temp, humidity, rainfall, track_air_diff, wet_condition_index,
        degradation, rolling_degradation, pace_delta, moving_average_lap_time, lap_time_trend, tire_temp,
        pit_window, is_late_stint, long_run_flag, perf_loss_rate, normalized_pace_loss, pit_pressure,
    ]


def build_feature_vector(payload):
    raw_sequence = np.array([
        _build_row(payload, step_offset)
        for step_offset in range(4, -1, -1)
    ], dtype=np.float32)

    if FEATURE_SCALER is not None:
        normalized = FEATURE_SCALER.transform(raw_sequence).astype(np.float32)
        scaling = {
            "mode": "standard_scaler",
            "path": FEATURE_SCALER_PATH,
        }
    else:
        normalized = ((raw_sequence - FEATURE_CENTER) / np.maximum(FEATURE_SCALE, 1e-6)).astype(np.float32)
        scaling = {
            "mode": "physics_fallback_standardization",
            "path": None,
        }

    current_features = dict(zip(FEATURE_COLUMNS, raw_sequence[-1].tolist()))
    return normalized, raw_sequence, current_features, scaling

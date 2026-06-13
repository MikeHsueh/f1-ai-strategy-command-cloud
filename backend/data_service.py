from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parent
RAW_PATH = BACKEND_DIR / "raw_f1_data.parquet"
ENGINEERED_PATH = BACKEND_DIR / "engineered_f1_data.parquet"


RACE_META = {
    1: ("Bahrain", "Bahrain GP", "BHR", 26.0325, 50.5106, "Desert circuit", "desert", "5.412 km", 15, "braking", "medium"),
    2: ("SaudiArabia", "Saudi Arabian GP", "SAU", 21.6319, 39.1044, "High-speed street circuit", "street", "6.174 km", 27, "high speed", "flat"),
    3: ("Australia", "Australian GP", "AUS", -37.8497, 144.968, "Temporary park circuit", "street", "5.278 km", 14, "stop-go", "low"),
    4: ("Japan", "Japanese GP", "JPN", 34.8431, 136.541, "Figure-eight circuit", "technical", "5.807 km", 18, "technical", "rolling"),
    5: ("China", "Chinese GP", "CHN", 31.3389, 121.219, "Permanent circuit", "permanent", "5.451 km", 16, "traction", "flat"),
    6: ("Miami", "Miami GP", "MIA", 25.9581, -80.2389, "Temporary circuit", "street", "5.412 km", 19, "traction", "flat"),
    7: ("EmiliaRomagna", "Emilia Romagna GP", "EMR", 44.3439, 11.7167, "Historic permanent circuit", "technical", "4.909 km", 19, "technical", "rolling"),
    8: ("Monaco", "Monaco GP", "MON", 43.7347, 7.4206, "Street circuit", "street", "3.337 km", 19, "low speed", "+42 m"),
    9: ("Canada", "Canadian GP", "CAN", 45.5, -73.5228, "Island street circuit", "street", "4.361 km", 14, "kerbs", "flat"),
    10: ("Spain", "Spanish GP", "ESP", 41.57, 2.2611, "Permanent circuit", "permanent", "4.657 km", 14, "balanced", "medium"),
    11: ("Austria", "Austrian GP", "AUT", 47.2197, 14.7647, "Mountain circuit", "technical", "4.318 km", 10, "short lap", "+65 m"),
    12: ("GreatBritain", "British GP", "GBR", 52.0786, -1.0169, "Permanent circuit", "permanent", "5.891 km", 18, "high speed", "flat"),
    13: ("Hungary", "Hungarian GP", "HUN", 47.583, 19.251, "Permanent circuit", "technical", "4.381 km", 14, "downforce", "medium"),
    14: ("Belgium", "Belgian GP", "BEL", 50.4372, 5.9714, "Forest circuit", "technical", "7.004 km", 20, "power", "+102 m"),
    15: ("Netherlands", "Dutch GP", "NED", 52.3888, 4.5409, "Coastal circuit", "technical", "4.259 km", 14, "flow", "banked"),
    16: ("Italy", "Italian GP", "ITA", 45.6156, 9.2811, "Historic park circuit", "permanent", "5.793 km", 11, "low drag", "flat"),
    17: ("Azerbaijan", "Azerbaijan GP", "AZE", 40.3725, 49.8533, "Street circuit", "street", "6.003 km", 20, "long straight", "flat"),
    18: ("Singapore", "Singapore GP", "SGP", 1.2914, 103.864, "Night street circuit", "street", "4.940 km", 19, "traction", "flat"),
    19: ("UnitedStates", "United States GP", "USA", 30.1328, -97.6411, "Permanent circuit", "technical", "5.513 km", 20, "mixed", "+41 m"),
    20: ("Mexico", "Mexico City GP", "MEX", 19.4042, -99.0907, "High-altitude circuit", "technical", "4.304 km", 17, "thin air", "2240 m"),
    21: ("SaoPaulo", "Sao Paulo GP", "SAP", -23.7036, -46.6997, "Anti-clockwise circuit", "technical", "4.309 km", 15, "traction", "rolling"),
    22: ("LasVegas", "Las Vegas GP", "LVG", 36.1147, -115.1728, "Street circuit", "street", "6.201 km", 17, "low temp", "flat"),
    23: ("Qatar", "Qatar GP", "QAT", 25.49, 51.4542, "Desert circuit", "desert", "5.419 km", 16, "high load", "flat"),
    24: ("AbuDhabi", "Abu Dhabi GP", "ABU", 24.4672, 54.6031, "Marina circuit", "desert", "5.281 km", 16, "traction", "flat"),
}


def safe_num(value, default=0.0):
    try:
        if pd.isna(value):
            return float(default)
        value = float(value)
        if not np.isfinite(value):
            return float(default)
        return value
    except Exception:
        return float(default)


def safe_int(value, default=0):
    return int(round(safe_num(value, default)))


def seconds(value, default=np.nan):
    try:
        if pd.isna(value):
            return float(default)
        if hasattr(value, "total_seconds"):
            return float(value.total_seconds())
        return float(value)
    except Exception:
        return float(default)


def normalize_compound(value):
    text = str(value or "").strip().upper()
    aliases = {
        "S": "SOFT",
        "SOFT": "SOFT",
        "M": "MEDIUM",
        "MEDIUM": "MEDIUM",
        "H": "HARD",
        "HARD": "HARD",
        "I": "INTERMEDIATE",
        "INTER": "INTERMEDIATE",
        "INTERMEDIATE": "INTERMEDIATE",
        "W": "WET",
        "WET": "WET",
    }
    return aliases.get(text, "UNKNOWN")


def compound_letter(compound):
    return {
        "SOFT": "S",
        "MEDIUM": "M",
        "HARD": "H",
        "INTERMEDIATE": "I",
        "WET": "W",
        "UNKNOWN": "?",
    }.get(normalize_compound(compound), "?")


def rain_risk_from_raw(value):
    rainfall = safe_num(value, 0.0)
    if rainfall <= 1.0:
        return float(np.clip(rainfall * 100.0, 0.0, 100.0))
    return float(np.clip(rainfall, 0.0, 100.0))


def race_meta(round_number):
    round_number = int(round_number)
    data = RACE_META.get(round_number)
    if data:
        key, label, short, lat, lon, terrain, terrain_class, length, turns, profile, elevation = data
    else:
        key, label, short, lat, lon = f"Round{round_number}", f"Round {round_number}", f"R{round_number}", 0.0, 0.0
        terrain, terrain_class, length, turns, profile, elevation = "Dataset circuit", "permanent", "--", "--", "dataset", "--"
    return {
        "round": round_number,
        "key": key,
        "label": label,
        "short": short,
        "lat": lat,
        "lon": lon,
        "terrain": terrain,
        "terrain_class": terrain_class,
        "length": length,
        "turns": turns,
        "profile": profile,
        "elevation": elevation,
    }


@lru_cache(maxsize=1)
def raw_data():
    df = pd.read_parquet(RAW_PATH).copy()
    for column in ["Year", "RoundNumber", "LapNumber", "Stint", "TyreLife", "Position"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["TrackTemp_Raw", "AirTemp_Raw", "Humidity_Raw", "Rainfall_Raw", "SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["Driver"] = df["Driver"].astype(str).str.upper()
    df["Compound"] = df["Compound"].map(normalize_compound)
    return df


@lru_cache(maxsize=1)
def engineered_data():
    df = pd.read_parquet(ENGINEERED_PATH).copy()
    df["Driver"] = df["Driver"].astype(str).str.upper()
    for column in df.columns:
        if column != "Driver":
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def latest_year():
    return int(raw_data()["Year"].max())


def round_from_circuit(circuit):
    if not circuit:
        return None
    text = str(circuit)
    for round_number, meta in RACE_META.items():
        if text in {meta[0], meta[1], meta[2]}:
            return round_number
    return None


def resolve_context(payload):
    df = raw_data()
    year = safe_int(payload.get("year"), latest_year())
    available_years = set(df["Year"].dropna().astype(int))
    if year not in available_years:
        year = latest_year()

    round_number = payload.get("round_number")
    if round_number in (None, ""):
        round_number = round_from_circuit(payload.get("circuit"))
    if round_number is None:
        year_df = df[df["Year"] == year]
        round_number = int(year_df["RoundNumber"].max())
    round_number = safe_int(round_number, 1)

    session = df[(df["Year"] == year) & (df["RoundNumber"] == round_number)]
    if session.empty:
        year_df = df[df["Year"] == year]
        round_number = int(year_df["RoundNumber"].max())
        session = year_df[year_df["RoundNumber"] == round_number]

    total_laps = int(session["LapNumber"].max()) if not session.empty else 50
    lap = int(np.clip(safe_int(payload.get("lap"), 1), 1, max(total_laps, 1)))
    drivers = sorted(session["Driver"].dropna().unique().tolist())
    driver = str(payload.get("driver") or "").upper()
    if driver not in drivers:
        driver = "NOR" if "NOR" in drivers else (drivers[0] if drivers else "VER")

    meta = race_meta(round_number)
    meta["total_laps"] = total_laps
    return {
        "year": year,
        "round_number": round_number,
        "lap": lap,
        "driver": driver,
        "total_laps": total_laps,
        "meta": meta,
    }


def session_frame(year, round_number):
    df = raw_data()
    return df[(df["Year"] == year) & (df["RoundNumber"] == round_number)].copy()


def rows_at_lap(session, lap):
    subset = session[session["LapNumber"] <= lap].sort_values(["Driver", "LapNumber"])
    if subset.empty:
        subset = session.sort_values(["Driver", "LapNumber"])
    return subset.groupby("Driver", as_index=False).tail(1)


def latest_row_at_lap(session, driver, lap):
    rows = session[(session["Driver"] == driver) & (session["LapNumber"] <= lap)].sort_values("LapNumber")
    if rows.empty:
        rows = session[session["Driver"] == driver].sort_values("LapNumber")
    if rows.empty:
        return None
    return rows.iloc[-1]


def row_speed(row):
    speeds = [safe_num(row.get(column), np.nan) for column in ["SpeedI1", "SpeedI2", "SpeedFL", "SpeedST"]]
    speeds = [value for value in speeds if np.isfinite(value) and value > 0]
    if not speeds:
        return 0.0, 0.0, 0.0
    return float(np.mean(speeds)), float(np.max(speeds)), float(np.std(speeds))


def lap_time_seconds(row):
    return seconds(row.get("LapTime"), np.nan)


def gap_snapshot(rows, driver):
    ordered = rows.sort_values(["Position", "Driver"], na_position="last").reset_index(drop=True)
    index = ordered.index[ordered["Driver"] == driver]
    if len(index) == 0:
        return 0.0, 0.0
    idx = int(index[0])
    current_time = seconds(ordered.iloc[idx].get("Time"), np.nan)

    def gap_to(other_idx):
        if other_idx < 0 or other_idx >= len(ordered):
            return 0.0
        other_time = seconds(ordered.iloc[other_idx].get("Time"), np.nan)
        if np.isfinite(current_time) and np.isfinite(other_time):
            return abs(current_time - other_time)
        own_lap = lap_time_seconds(ordered.iloc[idx])
        other_lap = lap_time_seconds(ordered.iloc[other_idx])
        if np.isfinite(own_lap) and np.isfinite(other_lap):
            return abs(own_lap - other_lap)
        return 0.0

    return gap_to(idx - 1), gap_to(idx + 1)


def forecast_pit_lap(row, lap, total_laps, pit_risk):
    compound = normalize_compound(row.get("Compound"))
    tyre_age = safe_num(row.get("TyreLife"), 0)
    expected_life = {
        "SOFT": 18,
        "MEDIUM": 26,
        "HARD": 36,
        "INTERMEDIATE": 20,
        "WET": 24,
    }.get(compound, 28)
    remaining_tyre_life = max(1.0, expected_life - tyre_age)
    pressure_factor = float(np.clip(1.0 - pit_risk * 0.65, 0.25, 1.0))
    laps_to_stop = max(1, int(round(remaining_tyre_life * pressure_factor)))
    return min(int(total_laps), int(lap) + laps_to_stop)


def driver_entry(row, session, lap, focus_driver, total_cars, pit_probability=None):
    avg_speed, max_speed, speed_std = row_speed(row)
    driver = str(row.get("Driver", "")).upper()
    position = safe_int(row.get("Position"), total_cars)
    if position <= 0:
        position = total_cars
    compound = normalize_compound(row.get("Compound"))
    tyre_age = safe_int(row.get("TyreLife"), 0)
    session_total_laps = max(safe_num(session["LapNumber"].max(), lap), 1.0)
    progress = ((safe_num(row.get("LapNumber"), lap) / session_total_laps) + (position - 1) / max(total_cars, 1)) % 1.0
    angle = progress * 2.0 * np.pi - np.pi / 2.0
    lap_time = lap_time_seconds(row)
    expected_life = {"SOFT": 18, "MEDIUM": 26, "HARD": 36, "INTERMEDIATE": 20, "WET": 24}.get(compound, 28)
    risk = pit_probability if driver == focus_driver and pit_probability is not None else tyre_age / max(expected_life, 1)
    risk = float(np.clip(risk, 0.0, 1.0))
    pit_lap = forecast_pit_lap(row, lap, session_total_laps, risk)
    return {
        "code": driver,
        "driver": driver,
        "team": str(row.get("Team") or "Unknown"),
        "position": int(position),
        "gap": "",
        "compound": compound,
        "compound_label": f"{compound_letter(compound)} - {tyre_age}",
        "tyre_age": int(tyre_age),
        "pit_risk": round(risk, 4),
        "pit_forecast_lap": pit_lap,
        "pit_forecast": f"Est. Pit L{pit_lap}",
        "pit_forecast_source": "current_lap_tyre_pressure",
        "coordinates": {
            "x": round(float(50.0 + np.cos(angle) * 40.0), 2),
            "y": round(float(50.0 + np.sin(angle) * 32.0), 2),
            "source": "dataset_rank_lap_projection",
        },
        "telemetry": {
            "speed": round(avg_speed, 1),
            "max_speed": round(max_speed, 1),
            "speed_std": round(speed_std, 2),
            "lap_time": round(float(lap_time), 3) if np.isfinite(lap_time) else 0.0,
            "sector1": round(seconds(row.get("Sector1Time"), 0.0), 3),
            "sector2": round(seconds(row.get("Sector2Time"), 0.0), 3),
            "sector3": round(seconds(row.get("Sector3Time"), 0.0), 3),
        },
    }


def classification_snapshot(year, round_number, lap, focus_driver, pit_probability=None):
    session = session_frame(year, round_number)
    rows = rows_at_lap(session, lap).sort_values(["Position", "Driver"], na_position="last")
    total = max(len(rows), 1)
    entries = [driver_entry(row, session, lap, focus_driver, total, pit_probability) for _, row in rows.iterrows()]
    entries = sorted(entries, key=lambda item: (item["position"], item["code"]))

    row_by_driver = {str(row.get("Driver", "")).upper(): row for _, row in rows.iterrows()}
    leader_time = seconds(row_by_driver.get(entries[0]["code"], {}).get("Time"), np.nan) if entries else np.nan
    for index, entry in enumerate(entries):
        row = row_by_driver.get(entry["code"])
        row_time = seconds(row.get("Time"), np.nan) if row is not None else np.nan
        if index == 0:
            entry["gap"] = "Leader"
        elif np.isfinite(row_time) and np.isfinite(leader_time):
            entry["gap"] = f"+{max(0.0, row_time - leader_time):.1f}"
        else:
            entry["gap"] = f"P{entry['position']}"
    return entries, {entry["code"]: entry["pit_forecast"] for entry in entries[:10]}


def apply_manual_position_override(entries, focus_driver, manual_position):
    if not entries:
        return entries

    target_index = int(np.clip(safe_int(manual_position, 1), 1, len(entries))) - 1
    focus_index = next((index for index, entry in enumerate(entries) if entry["code"] == focus_driver), None)
    if focus_index is None:
        return entries

    reordered = list(entries)
    focus_entry = dict(reordered.pop(focus_index))
    reordered.insert(target_index, focus_entry)

    for index, entry in enumerate(reordered, start=1):
        entry["position"] = index
        if entry["code"] == focus_driver:
            entry["gap"] = "Manual"

    return reordered


def apply_scenario_focus_driver(entries, payload, focus_driver, pit_probability=None):
    if not entries:
        return entries

    compound = normalize_compound(payload.get("compound"))
    tyre_age = safe_int(payload.get("tire_age"), 0)
    expected_life = {
        "SOFT": 18,
        "MEDIUM": 26,
        "HARD": 36,
        "INTERMEDIATE": 20,
        "WET": 24,
    }.get(compound, 28)
    manual_risk = float(np.clip(pit_probability if pit_probability is not None else tyre_age / max(expected_life, 1), 0.0, 1.0))

    updated = []
    for entry in entries:
        if entry["code"] != focus_driver:
            updated.append(entry)
            continue

        focus_entry = dict(entry)
        focus_entry["compound"] = compound
        focus_entry["tyre_age"] = tyre_age
        focus_entry["compound_label"] = f"{compound_letter(compound)} - {tyre_age}"
        focus_entry["pit_risk"] = round(manual_risk, 4)
        focus_entry["pit_forecast_lap"] = int(
            forecast_pit_lap(
                {"Compound": compound, "TyreLife": tyre_age},
                safe_int(payload.get("lap"), 1),
                safe_int(payload.get("total_laps"), 52),
                manual_risk,
            )
        )
        focus_entry["pit_forecast"] = f"Est. Pit L{focus_entry['pit_forecast_lap']}"
        focus_entry["telemetry"] = {
            **focus_entry.get("telemetry", {}),
            "speed": round(safe_num(payload.get("speed"), focus_entry.get("telemetry", {}).get("speed", 0.0)), 1),
        }
        updated.append(focus_entry)
    return updated


def enrich_payload_from_dataset(payload):
    payload = dict(payload or {})
    context = resolve_context(payload)
    session = session_frame(context["year"], context["round_number"])
    row = latest_row_at_lap(session, context["driver"], context["lap"])
    rows = rows_at_lap(session, context["lap"])
    if row is None:
        return payload

    avg_speed, max_speed, speed_std = row_speed(row)
    gap_ahead, gap_behind = gap_snapshot(rows, context["driver"])
    lap_ratio = context["lap"] / max(context["total_laps"], 1)
    historical_rain = rain_risk_from_raw(row.get("Rainfall_Raw"))
    live_weather = str(payload.get("weather_mode", "manual")).lower() == "live"

    current_air = safe_num(payload.get("air_temp"), safe_num(row.get("AirTemp_Raw"), 23.0))
    current_track = safe_num(payload.get("track_temp"), safe_num(row.get("TrackTemp_Raw"), current_air + 8.0))
    current_humidity = safe_num(payload.get("humidity"), safe_num(row.get("Humidity_Raw"), 55.0))
    current_rain = safe_num(payload.get("rain_risk"), historical_rain)
    current_wind = safe_num(payload.get("wind_speed"), 0.0)
    current_wind_dir = safe_num(payload.get("wind_direction"), 0.0)
    model_rain = max(float(np.clip(current_rain, 0.0, 100.0)), historical_rain)

    display_air = current_air if live_weather else safe_num(row.get("AirTemp_Raw"), current_air)
    display_track = current_track if live_weather else safe_num(row.get("TrackTemp_Raw"), current_track)
    display_humidity = current_humidity if live_weather else safe_num(row.get("Humidity_Raw"), current_humidity)
    display_rain = current_rain if live_weather else historical_rain

    lap_time = lap_time_seconds(row)
    manual_position_override = bool(payload.get("manual_position_override", False))
    manual_control_mode = bool(payload.get("manual_control_mode", False)) or str(payload.get("control_mode", "dataset")).lower() == "scenario"
    initial_tire_override = bool(payload.get("initial_tire_override", False))
    manual_position = safe_int(payload.get("position"), safe_int(row.get("Position"), 1))
    manual_compound = normalize_compound(payload.get("compound"))
    manual_tire_age = safe_int(payload.get("tire_age"), safe_int(row.get("TyreLife"), 0))
    manual_stint = safe_int(payload.get("current_stint"), safe_int(row.get("Stint"), 1))
    manual_gap_ahead = round(safe_num(payload.get("gap_ahead"), gap_ahead), 2)
    manual_gap_behind = round(safe_num(payload.get("gap_behind"), gap_behind), 2)
    manual_fuel_load = round(safe_num(payload.get("fuel_load"), max(0.0, 110.0 * (1.0 - lap_ratio))), 1)

    payload.update({
        "year": context["year"],
        "round_number": context["round_number"],
        "circuit": context["meta"]["key"],
        "race_label": context["meta"]["label"],
        "terrain": context["meta"]["terrain"],
        "driver": context["driver"],
        "lap": context["lap"],
        "total_laps": context["total_laps"],
        "position": manual_position if manual_position_override or manual_control_mode else safe_int(row.get("Position"), manual_position),
        "compound": manual_compound if initial_tire_override else normalize_compound(row.get("Compound")),
        "tire_age": manual_tire_age if initial_tire_override else safe_int(row.get("TyreLife"), manual_tire_age),
        "current_stint": manual_stint if manual_control_mode else safe_int(row.get("Stint"), manual_stint),
        "speed": round(avg_speed, 1),
        "max_speed": round(max_speed, 1),
        "speed_std": round(speed_std, 2),
        "rpm": safe_num(payload.get("rpm"), 10800.0),
        "throttle": safe_num(payload.get("throttle"), 70.0),
        "brake": safe_num(payload.get("brake"), 10.0),
        "gap_ahead": manual_gap_ahead if manual_control_mode else round(gap_ahead, 2),
        "gap_behind": manual_gap_behind if manual_control_mode else round(gap_behind, 2),
        "fuel_load": manual_fuel_load if manual_control_mode else round(max(0.0, 110.0 * (1.0 - lap_ratio)), 1),
        "lap_time": round(float(lap_time), 3) if np.isfinite(lap_time) else safe_num(payload.get("lap_time"), 91.0),
        "air_temp": display_air,
        "track_temp": display_track,
        "humidity": display_humidity,
        "rain_risk": model_rain,
        "display_rain_risk": display_rain,
        "current_rain_risk": current_rain,
        "historical_rain_risk": historical_rain,
        "wind_speed": current_wind,
        "wind_direction": current_wind_dir,
        "weather_mode": "live" if live_weather else "dataset",
        "manual_position_override": manual_position_override,
        "manual_control_mode": manual_control_mode,
    })
    payload["_race_context"] = context
    payload["_weather_context"] = {
        "current": {
            "air_temp": round(current_air, 1),
            "track_temp": round(current_track, 1),
            "humidity": round(current_humidity, 1),
            "rain_risk": round(float(np.clip(current_rain, 0.0, 100.0)), 1),
            "wind_speed": round(current_wind, 1),
            "wind_direction": round(current_wind_dir, 1),
            "source": "open-meteo" if live_weather else "dataset",
        },
        "dataset": {
            "air_temp": round(safe_num(row.get("AirTemp_Raw"), display_air), 1),
            "track_temp": round(safe_num(row.get("TrackTemp_Raw"), display_track), 1),
            "humidity": round(safe_num(row.get("Humidity_Raw"), display_humidity), 1),
            "rain_risk": round(historical_rain, 1),
            "condition": "wet" if historical_rain >= 45 else "dry",
            "source": "raw_f1_data.parquet",
        },
        "model": {
            "rain_risk": round(model_rain, 1),
            "condition": "wet" if model_rain >= 45 else "dry",
            "source": "max(current_weather, dataset_race_weather)",
        },
    }
    return payload


@lru_cache(maxsize=128)
def final_positions(year, round_number):
    session = session_frame(year, round_number)
    last_rows = session.sort_values(["Driver", "LapNumber"]).groupby("Driver", as_index=False).tail(1)
    return {str(row["Driver"]).upper(): safe_int(row.get("Position"), 20) for _, row in last_rows.iterrows()}


def strategy_option(label, rows, final_map, fallback_position, path, trigger):
    if rows.empty:
        return {
            "label": label,
            "path": path,
            "trigger": trigger,
            "projected_position": fallback_position,
            "projected_text": f"P{fallback_position}",
            "sample_size": 0,
            "confidence": 0.0,
            "source": "insufficient_dataset_analogues",
        }
    positions = []
    for _, row in rows.iterrows():
        driver = str(row.get("Driver", "")).upper()
        row_year = safe_int(row.get("Year"), 0)
        row_round = safe_int(row.get("RoundNumber"), 0)
        row_final_map = final_positions(row_year, row_round) if row_year and row_round else final_map
        if driver in row_final_map:
            positions.append(row_final_map[driver])
    if not positions:
        positions = [fallback_position]
    projected = int(np.clip(round(float(np.mean(positions))), 1, 20))
    spread = float(np.std(positions)) if len(positions) > 1 else 0.0
    confidence = float(np.clip(len(positions) / 30.0, 0.15, 0.92) * np.clip(1.0 - spread / 8.0, 0.35, 1.0))
    return {
        "label": label,
        "path": path,
        "trigger": trigger,
        "projected_position": projected,
        "projected_text": f"P{projected}",
        "sample_size": int(len(positions)),
        "confidence": round(confidence, 2),
        "source": "engineered_f1_data_nearest_analogues",
    }


def multi_strategy_options(payload):
    context = payload.get("_race_context") or resolve_context(payload)
    year = context["year"]
    round_number = context["round_number"]
    lap = context["lap"]
    position = safe_int(payload.get("position"), 10)
    tire_age = safe_num(payload.get("tire_age"), 0.0)
    rain_risk = safe_num(payload.get("rain_risk"), 0.0)
    eng = engineered_data()

    def nearest_pool(source):
        if source.empty:
            return source
        pool = source.copy()
        pool["_distance"] = (
            (pool["lap"].fillna(lap) - lap).abs() / 8.0
            + (pool["position"].fillna(position) - position).abs() / 5.0
            + (pool["tire_age"].fillna(tire_age) - tire_age).abs() / 10.0
            + (pool["rain_risk"].fillna(rain_risk / 100.0) - rain_risk / 100.0).abs() * 2.0
        )
        return pool.sort_values("_distance").head(40).drop(columns=["_distance"])

    same_year_round = eng[(eng["Year"] == year) & (eng["RoundNumber"] == round_number)]
    same_round = eng[eng["RoundNumber"] == round_number]

    strict = same_year_round[
        same_year_round["lap"].between(lap - 3, lap + 3)
        & same_year_round["position"].between(position - 5, position + 5)
        & same_year_round["tire_age"].between(max(0, tire_age - 8), tire_age + 8)
        & ((same_year_round["rain_risk"].fillna(0.0) - rain_risk / 100.0).abs() <= 0.45)
    ] if not same_year_round.empty else same_year_round

    broad = same_round[
        same_round["lap"].between(lap - 6, lap + 6)
        & same_round["position"].between(position - 8, position + 8)
        & same_round["tire_age"].between(max(0, tire_age - 12), tire_age + 12)
    ] if not same_round.empty else same_round

    fallback = nearest_pool(eng)

    def option_rows(label_column, active=True):
        value_filter = lambda frame: frame[label_column].fillna(0) >= 0.5 if active else frame[label_column].fillna(0) < 0.5
        for pool in [strict, broad, fallback]:
            if pool.empty or label_column not in pool.columns:
                continue
            rows = pool[value_filter(pool)]
            if not rows.empty:
                return nearest_pool(rows)
        return eng.iloc[0:0]

    final_map = final_positions(year, round_number)
    stop_rows = option_rows("Label_Pit_Next_Lap", active=True)
    hold_rows = option_rows("Label_Pit_Next_Lap", active=False)
    sc_rows = option_rows("Label_SC_Next_3_Laps", active=True)
    wet_path = "INTERMEDIATE/WET" if rain_risk >= 55 else str(payload.get("next_compound", "HARD"))
    current_compound = str(payload.get("compound", "MEDIUM"))
    return [
        strategy_option("Option A (Box next lap)", stop_rows, final_map, position, f"{current_compound} -> {wet_path}", "pit-next-lap analogues"),
        strategy_option("Option B (Extend stint)", hold_rows, final_map, position, f"{current_compound} long-run", "hold analogues"),
        strategy_option("Option C (SC window)", sc_rows, final_map, position, f"SC delta -> {wet_path}", "safety-car analogues"),
    ]


def sector_session_seconds(row, sector):
    return seconds(row.get(f"Sector{sector}SessionTime"), np.nan)


def delta_trend(payload):
    context = payload.get("_race_context") or resolve_context(payload)
    session = session_frame(context["year"], context["round_number"])
    lap = context["lap"]
    focus = context["driver"]
    rows = rows_at_lap(session, lap).sort_values(["Position", "Driver"], na_position="last").reset_index(drop=True)
    focus_idx = rows.index[rows["Driver"] == focus]
    if len(focus_idx) == 0:
        return {"y_axis_label": "Delta (s) / Laptime", "series": [], "source": "raw_f1_data.parquet"}
    idx = int(focus_idx[0])
    rivals = []
    if idx > 0:
        rivals.append(("Gap to car ahead", str(rows.iloc[idx - 1]["Driver"]).upper()))
    if idx + 1 < len(rows):
        rivals.append(("Gap to car behind", str(rows.iloc[idx + 1]["Driver"]).upper()))
    series = []
    for label, rival in rivals:
        points = []
        for race_lap in range(max(1, lap - 3), lap + 1):
            focus_row = session[(session["Driver"] == focus) & (session["LapNumber"] == race_lap)]
            rival_row = session[(session["Driver"] == rival) & (session["LapNumber"] == race_lap)]
            if focus_row.empty or rival_row.empty:
                continue
            focus_row = focus_row.iloc[0]
            rival_row = rival_row.iloc[0]
            for sector in [1, 2, 3]:
                focus_time = sector_session_seconds(focus_row, sector)
                rival_time = sector_session_seconds(rival_row, sector)
                if np.isfinite(focus_time) and np.isfinite(rival_time):
                    points.append({"label": f"L{race_lap} S{sector}", "value": round(focus_time - rival_time, 3)})
        if points:
            values = np.array([point["value"] for point in points], dtype=float)
            x_axis = np.arange(len(values), dtype=float)
            slope = float(np.polyfit(x_axis, values, 1)[0]) if len(values) > 1 else 0.0
            predicted = [{"label": f"L{lap + 1} S{sector}", "value": round(float(values[-1] + slope * sector), 3)} for sector in [1, 2, 3]]
            series.append({"name": f"{label} ({rival})", "line": "solid", "mode": "historical", "data": points})
            series.append({"name": f"{label} ({rival}) projected", "line": "dashed", "mode": "predictive", "data": predicted})
    return {"y_axis_label": "Delta (s) / Laptime", "series": series, "source": "raw_f1_data.parquet + short-horizon regression"}


def weather_radar(payload):
    weather = payload.get("_weather_context", {})
    model = weather.get("model", {})
    current = weather.get("current", {})
    rain = safe_num(model.get("rain_risk"), safe_num(payload.get("rain_risk"), 0.0))
    wind = safe_num(current.get("wind_speed"), safe_num(payload.get("wind_speed"), 0.0))
    direction = safe_num(current.get("wind_direction"), safe_num(payload.get("wind_direction"), 0.0))
    intensity = float(np.clip(rain / 100.0, 0.0, 1.0))
    forecast = payload.get("weather_forecast")
    bands = []
    if isinstance(forecast, list):
        for index, item in enumerate(forecast[:3], start=1):
            if not isinstance(item, dict):
                continue
            probability = safe_num(item.get("precipitation_probability"), rain)
            rain_amount = max(0.0, safe_num(item.get("rain"), 0.0))
            precipitation_index = max(probability / 100.0, float(np.clip(rain_amount / 2.5, 0.0, 1.0)))
            bands.append({
                "horizon_hours": safe_int(item.get("horizon_hours"), index),
                "precipitation_index": round(float(np.clip(precipitation_index, 0.0, 1.0)), 3),
                "precipitation_probability": round(float(np.clip(probability, 0.0, 100.0)), 1),
                "rain_mm": round(rain_amount, 2),
            })
    if not bands:
        bands = [
            {"horizon_hours": hour, "precipitation_index": round(intensity, 3), "precipitation_probability": round(rain, 1), "rain_mm": 0.0}
            for hour in [0, 1, 2]
        ]
    return {
        "condition": "wet" if rain >= 45 else "dry",
        "precipitation_index": round(intensity, 3),
        "wind_speed": round(wind, 1),
        "wind_direction": round(direction, 1),
        "bands": bands,
        "source": "open_meteo_hourly_and_dataset_wet_context" if forecast else "dataset_weather_snapshot",
    }


def dataset_context(payload, pit_probability=None):
    context = payload.get("_race_context") or resolve_context(payload)
    classification, top10 = classification_snapshot(
        context["year"],
        context["round_number"],
        context["lap"],
        context["driver"],
        pit_probability=pit_probability,
    )
    if payload.get("manual_control_mode", False):
        classification = apply_scenario_focus_driver(
            classification,
            payload,
            context["driver"],
            pit_probability=pit_probability,
        )
    if payload.get("manual_position_override", False):
        classification = apply_manual_position_override(
            classification,
            context["driver"],
            payload.get("position"),
        )
        top10 = {entry["code"]: entry["pit_forecast"] for entry in classification[:10]}
    elif payload.get("manual_control_mode", False):
        top10 = {entry["code"]: entry["pit_forecast"] for entry in classification[:10]}
    selected = next((entry for entry in classification if entry["code"] == context["driver"]), classification[0] if classification else None)
    return {
        "race_context": {
            "year": context["year"],
            "round_number": context["round_number"],
            "lap": context["lap"],
            "total_laps": context["total_laps"],
            **context["meta"],
        },
        "selected_driver": selected,
        "classification": classification,
        "top10_pit_forecast": top10,
        "weather_context": payload.get("_weather_context", {}),
        "weather_radar": weather_radar(payload),
        "delta_trend": delta_trend(payload),
        "multi_strategy": multi_strategy_options(payload),
    }


def context_payload(year=None, round_number=None):
    df = raw_data()
    default_year = latest_year()
    year = safe_int(year, default_year)
    if year not in set(df["Year"].dropna().astype(int)):
        year = default_year
    year_df = df[df["Year"] == year]

    races = []
    for rnd in sorted(year_df["RoundNumber"].dropna().astype(int).unique().tolist()):
        race_df = year_df[year_df["RoundNumber"] == rnd]
        meta = race_meta(rnd)
        meta["total_laps"] = int(race_df["LapNumber"].max())
        meta["year"] = year
        races.append(meta)

    if not races:
        return {"source": "raw_f1_data.parquet", "seasons": [], "races": [], "teams": {}, "drivers": [], "default_selection": {}}

    available_rounds = {race["round"] for race in races}
    round_number = safe_int(round_number, 12 if 12 in available_rounds else races[0]["round"])
    if round_number not in available_rounds:
        round_number = races[0]["round"]
    session = year_df[year_df["RoundNumber"] == round_number]
    latest_rows = session.sort_values(["Driver", "LapNumber"]).groupby("Driver", as_index=False).tail(1)

    teams = {}
    for _, row in latest_rows.sort_values(["Team", "Driver"]).iterrows():
        team = str(row.get("Team") or "Unknown")
        driver = str(row.get("Driver") or "").upper()
        if not driver:
            continue
        teams.setdefault(team, []).append({"code": driver, "name": driver, "team": team})

    seasons = []
    for season in sorted(df["Year"].dropna().astype(int).unique().tolist()):
        season_df = df[df["Year"] == season]
        seasons.append({"year": season, "rounds": sorted(season_df["RoundNumber"].dropna().astype(int).unique().tolist())})

    drivers = sorted(latest_rows["Driver"].dropna().astype(str).str.upper().unique().tolist())
    default_driver = "NOR" if "NOR" in drivers else (drivers[0] if drivers else "VER")
    return {
        "source": "raw_f1_data.parquet",
        "seasons": seasons,
        "races": races,
        "teams": teams,
        "drivers": drivers,
        "default_selection": {
            "year": year,
            "round_number": round_number,
            "driver": default_driver,
            "lap": 1,
        },
    }

import copy
import math
import os
import threading
import time

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from data_service import context_payload, raw_data
from simulator import feature_importance, predict_probability, simulate_strategy
from strategy_model import MODEL_INFO
from telemetry_engine import FEATURE_COLUMNS, calculate_tire_health


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "dist"

app = Flask(__name__, static_folder=None)
CORS(app, supports_credentials=True)

_CACHE_TTL_SECONDS = 60
_MEMORY_CACHE = {}
_CACHE_LOCK = threading.Lock()
_KEY_LOCKS = {}


def _cache_key(payload):
    return tuple(sorted(
        (str(key), str(value))
        for key, value in payload.items()
        if value is None or isinstance(value, (str, int, float, bool))
    ))


def _cached_value(namespace, key, builder, ttl=_CACHE_TTL_SECONDS):
    full_key = (namespace, key)
    now = time.monotonic()

    with _CACHE_LOCK:
        cached = _MEMORY_CACHE.get(full_key)
        if cached and now - cached["created_at"] < ttl:
            return copy.deepcopy(cached["value"])
        key_lock = _KEY_LOCKS.setdefault(full_key, threading.Lock())

    with key_lock:
        now = time.monotonic()
        with _CACHE_LOCK:
            cached = _MEMORY_CACHE.get(full_key)
            if cached and now - cached["created_at"] < ttl:
                return copy.deepcopy(cached["value"])

        value = builder()
        with _CACHE_LOCK:
            _MEMORY_CACHE[full_key] = {
                "created_at": time.monotonic(),
                "value": copy.deepcopy(value),
            }
            if len(_MEMORY_CACHE) > 512:
                expired = [
                    cache_key
                    for cache_key, entry in _MEMORY_CACHE.items()
                    if time.monotonic() - entry["created_at"] >= ttl
                ]
                for cache_key in expired:
                    _MEMORY_CACHE.pop(cache_key, None)
                    _KEY_LOCKS.pop(cache_key, None)
        return value


def _cached_context(year=None, round_number=None):
    key = (str(year or ""), str(round_number or ""))
    return _cached_value(
        "context",
        key,
        lambda: context_payload(year=year, round_number=round_number),
    )


def _cached_strategy(payload):
    normalized = clean_payload(payload)
    return _cached_value(
        "strategy",
        _cache_key(normalized),
        lambda: simulate_strategy(normalized),
    )


DRIVER_NAMES = {
    "ALB": "Alexander Albon",
    "ALO": "Fernando Alonso",
    "BEA": "Oliver Bearman",
    "BOT": "Valtteri Bottas",
    "COL": "Franco Colapinto",
    "DEV": "Nyck de Vries",
    "GAS": "Pierre Gasly",
    "HAM": "Lewis Hamilton",
    "HUL": "Nico Hulkenberg",
    "LAW": "Liam Lawson",
    "LAT": "Nicholas Latifi",
    "LEC": "Charles Leclerc",
    "MAG": "Kevin Magnussen",
    "MSC": "Mick Schumacher",
    "NOR": "Lando Norris",
    "OCO": "Esteban Ocon",
    "PER": "Sergio Perez",
    "PIA": "Oscar Piastri",
    "RIC": "Daniel Ricciardo",
    "RUS": "George Russell",
    "SAI": "Carlos Sainz",
    "SAR": "Logan Sargeant",
    "STR": "Lance Stroll",
    "TSU": "Yuki Tsunoda",
    "VER": "Max Verstappen",
    "VET": "Sebastian Vettel",
    "ZHO": "Zhou Guanyu",
}


def clean_payload(payload):
    payload = dict(payload or {})

    string_defaults = {
        "year": "2024",
        "circuit": "GreatBritain",
        "driver": "NOR",
        "compound": "MEDIUM",
        "next_compound": "HARD",
        "terrain": "Permanent",
        "weather_mode": "manual",
        "control_mode": "dataset",
    }
    int_defaults = {
        "lap": 1,
        "tire_age": 0,
        "speed": 260,
        "rpm": 10800,
        "throttle": 70,
        "brake": 10,
        "humidity": 55,
        "rain_risk": 0,
        "position": 1,
        "current_stint": 1,
        "total_laps": 52,
        "round_number": 12,
    }
    float_defaults = {
        "track_temp": 35.0,
        "air_temp": 23.0,
        "wind_speed": 0.0,
        "wind_direction": 0.0,
        "gap_ahead": 2.0,
        "gap_behind": 2.0,
        "fuel_load": 80.0,
    }

    for field, default in string_defaults.items():
        payload[field] = str(payload.get(field, default) or default)

    for field, default in int_defaults.items():
        try:
            payload[field] = int(payload.get(field, default))
        except (TypeError, ValueError):
            payload[field] = default

    for field, default in float_defaults.items():
        try:
            payload[field] = float(payload.get(field, default))
        except (TypeError, ValueError):
            payload[field] = default

    payload["safety_car"] = bool(payload.get("safety_car", False))
    payload["manual_position_override"] = bool(payload.get("manual_position_override", False))
    payload["initial_tire_override"] = bool(payload.get("initial_tire_override", False))
    payload["manual_control_mode"] = str(payload.get("control_mode", "dataset")).lower() == "scenario"
    return payload


def request_payload():
    return clean_payload({
        "year": request.args.get("year"),
        "round_number": request.args.get("round_number"),
        "driver": request.args.get("driver"),
        "lap": request.args.get("lap"),
        "position": request.args.get("position"),
        "control_mode": request.args.get("control_mode", "dataset"),
    })


def probability_value(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value / 100.0 if value > 1 else value))


def risk_rule(probability):
    if probability >= 0.85:
        return "CRITICAL", "PIT_NOW"
    if probability >= 0.65:
        return "HIGH", "PREPARE_PIT"
    if probability >= 0.35:
        return "MEDIUM", "MONITOR"
    return "LOW", "STAY_OUT"


def prediction_payload(result):
    strategy = result.get("strategy", {})
    probability = probability_value(strategy.get("pit_probability", 0.0))
    risk, action = risk_rule(probability)
    return {
        "pit_probability": probability,
        "optimal_pit_lap": int(strategy.get("optimal_pit_lap", 0)),
        "recommended_tire": strategy.get("recommended_tire", "HOLD"),
        "expected_gain": float(strategy.get("expected_gain", 0.0)),
        "undercut_probability": probability_value(strategy.get("undercut_success_probability", 0.0)),
        "risk": risk,
        "action": action,
        "attention": strategy.get("attention", []),
    }


def context_for_payload(payload):
    return _cached_context(
        year=payload.get("year"),
        round_number=payload.get("round_number"),
    )


def driver_list(context):
    drivers = []
    seen = set()
    for team, members in context.get("teams", {}).items():
        for member in members:
            code = str(member.get("code", "")).upper()
            if not code or code in seen:
                continue
            seen.add(code)
            drivers.append({
                "code": code,
                "name": DRIVER_NAMES.get(code, member.get("name", code)),
                "team": member.get("team", team),
            })
    return drivers


@app.route("/api/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "source": "backend",
        "model": MODEL_INFO,
        "feature_columns": FEATURE_COLUMNS,
    })


@app.after_request
def add_cache_headers(response):
    if request.path in {"/api/seasons", "/api/races", "/api/drivers"}:
        response.headers["Cache-Control"] = "public, max-age=60"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    started = time.perf_counter()
    return jsonify({
        "status": "ok" if MODEL_INFO.get("weights_loaded") else "degraded",
        "source": "backend",
        "model": {
            **MODEL_INFO,
            "feature_count": len(FEATURE_COLUMNS),
            "scaler_mode": "runtime",
        },
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    })


@app.route("/api/seasons", methods=["GET"])
def seasons():
    context = _cached_context()
    return jsonify({
        "source": context.get("source", "backend"),
        "seasons": context.get("seasons", []),
    })


@app.route("/api/races", methods=["GET"])
def races():
    context = _cached_context(year=request.args.get("year"))
    return jsonify({
        "source": context.get("source", "backend"),
        "races": context.get("races", []),
    })


@app.route("/api/drivers", methods=["GET"])
def drivers():
    context = _cached_context(
        year=request.args.get("year"),
        round_number=request.args.get("round_number"),
    )
    return jsonify({
        "source": context.get("source", "backend"),
        "drivers": driver_list(context),
    })


@app.route("/api/laps", methods=["GET"])
def laps():
    payload = request_payload()
    context = context_for_payload(payload)
    selected = next(
        (
            race for race in context.get("races", [])
            if int(race.get("round", 0)) == int(payload.get("round_number", 0))
        ),
        context.get("races", [{}])[0] if context.get("races") else {},
    )
    total_laps = int(selected.get("total_laps", payload.get("total_laps", 52)))
    return jsonify({"laps": list(range(1, total_laps + 1)), "total_laps": total_laps})


@app.route("/api/race-state", methods=["GET"])
def race_state():
    payload = request_payload()
    result = _cached_strategy(payload)
    state = result.get("race_state", {})
    weather = result.get("weather", {})
    tire = result.get("tire", {})
    telemetry = result.get("telemetry", {})
    selected = result.get("selected_driver") or {}
    total_laps = int(result.get("race_context", {}).get("total_laps", 52))
    tire_life = float(tire.get("life", 0.0))
    degradation = max(0.0, float(tire.get("degradation", 0.0)))
    return jsonify({
        "lap": int(state.get("lap", 1)),
        "total_laps": total_laps,
        "position": int(state.get("position", selected.get("position", 1))),
        "gap_ahead": float(state.get("gap_ahead", 0.0)),
        "gap_behind": float(state.get("gap_behind", 0.0)),
        "safety_car": bool(state.get("safety_car", False)),
        "safety_car_incident_risk": probability_value(state.get("safety_car_incident_risk", 0.0)),
        "driver": selected.get("code", request.args.get("driver", "NOR")),
        "team": selected.get("team", "Unknown"),
        "speed": float(telemetry.get("speed", 0.0)),
        "rpm": float(telemetry.get("rpm", 0.0)),
        "throttle": float(telemetry.get("throttle", 0.0)),
        "brake": float(telemetry.get("brake", 0.0)),
        "weather": {
            **weather,
            "condition": result.get("weather_radar", {}).get("condition", "dry"),
        },
        "tire": {
            **tire,
            "health": tire.get(
                "health",
                calculate_tire_health(tire.get("compound", "MEDIUM"), tire_life, degradation),
            ),
        },
    })


@app.route("/api/weather", methods=["GET"])
def weather():
    result = _cached_strategy(request_payload())
    return jsonify({
        **result.get("weather", {}),
        "condition": result.get("weather_radar", {}).get("condition", "dry"),
    })


@app.route("/api/features", methods=["GET"])
def features():
    payload = request_payload()
    items = _cached_value(
        "features",
        _cache_key(payload),
        lambda: feature_importance(payload),
    )
    return jsonify({"features": items})


@app.route("/api/predict", methods=["POST"])
def predict():
    result = _cached_strategy(clean_payload(request.json))
    return jsonify(prediction_payload(result))


@app.route("/api/pit-probability-timeline", methods=["GET"])
def pit_probability_timeline():
    payload = request_payload()

    def build_timeline():
        context = context_for_payload(payload)
        selected_race = next(
            (
                race for race in context.get("races", [])
                if int(race.get("round", 0)) == int(payload.get("round_number", 0))
            ),
            context.get("races", [{}])[0] if context.get("races") else {},
        )
        total_laps = int(selected_race.get("total_laps", 52))

        df = raw_data()
        driver_rows = df[
            (df["Year"] == int(payload["year"]))
            & (df["RoundNumber"] == int(payload["round_number"]))
            & (df["Driver"].astype(str).str.upper() == str(payload["driver"]).upper())
        ]
        actual_pits = {
            int(row["LapNumber"]): str(row.get("Compound") or "UNKNOWN").upper()
            for _, row in driver_rows[driver_rows["PitInTime"].notna()].iterrows()
        }

        important_laps = {
            1,
            total_laps,
            *actual_pits.keys(),
        }
        max_points = 20
        remaining = max(0, max_points - len(important_laps))
        sampled_laps = set(important_laps)
        if remaining:
            step = max(1, math.ceil(total_laps / remaining))
            sampled_laps.update(range(1, total_laps + 1, step))

        if len(sampled_laps) > max_points:
            optional = sorted(sampled_laps - important_laps)
            keep_count = max(0, max_points - len(important_laps))
            if keep_count and optional:
                indexes = {
                    round(index * (len(optional) - 1) / max(1, keep_count - 1))
                    for index in range(keep_count)
                }
                optional = [optional[index] for index in sorted(indexes)]
            else:
                optional = []
            sampled_laps = important_laps | set(optional)

        timeline = []
        for lap in sorted(sampled_laps):
            probability, enriched = predict_probability({**payload, "lap": lap})
            timeline.append({
                "lap": lap,
                "probability": round(probability, 5),
                "actual_pit": lap in actual_pits,
                "compound": actual_pits.get(
                    lap,
                    str(enriched.get("compound", "UNKNOWN")).upper(),
                ),
            })
        return {
            "timeline": timeline,
            "source": "trained_model_sampled",
            "sample_count": len(timeline),
            "total_laps": total_laps,
        }

    result = _cached_value(
        "timeline",
        (
            str(payload.get("year")),
            str(payload.get("round_number")),
            str(payload.get("driver")).upper(),
        ),
        build_timeline,
    )
    return jsonify(result)


@app.route("/api/pace-trend", methods=["GET"])
def pace_trend():
    result = _cached_strategy(request_payload())
    trend = result.get("delta_trend", {})
    return jsonify({
        "series": trend.get("series", []),
        "y_axis_label": trend.get("y_axis_label", "Delta (s) / Laptime"),
        "source": trend.get("source", "backend"),
    })


@app.route("/api/simulate-strategy", methods=["POST"])
def simulate_strategy_endpoint():
    body = dict(request.json or {})
    override_enabled = bool(body.get(
        "enableInitialTireOverride",
        body.get("enable_initial_tire_override", False),
    ))

    live_payload = clean_payload({
        "year": body.get("year"),
        "round_number": body.get("round_number"),
        "driver": body.get("driver"),
        "lap": body.get("lap"),
        "control_mode": "dataset",
    })
    live_result = simulate_strategy(live_payload)
    live_tire = live_result.get("tire", {})
    live_state = live_result.get("race_state", {})
    live_weather = live_result.get("weather", {})

    scenario_input = {
        **body,
        "control_mode": "scenario",
        "manual_position_override": True,
        "initial_tire_override": override_enabled,
        "position": body.get("position", live_state.get("position", 1)),
        "gap_ahead": live_state.get("gap_ahead", 0.0),
        "gap_behind": live_state.get("gap_behind", 0.0),
        "safety_car": bool(body.get("safetyCar", body.get("safety_car", False))),
        "rain_risk": body.get("rainRisk", body.get("rain_risk", live_weather.get("model_rain_risk", 0))),
        "next_compound": body.get("nextCompound", body.get("next_compound", "HARD")),
        "target_pit_lap": body.get("targetPitLap", body.get("target_lap", body.get("lap", 1))),
    }
    if override_enabled:
        scenario_input["compound"] = body.get("initialCompound", body.get("initial_compound", live_tire.get("compound", "MEDIUM")))
        scenario_input["tire_age"] = body.get("initialTyreLife", body.get("initial_tyre_life", live_tire.get("life", 0)))

    payload = clean_payload(scenario_input)
    result = simulate_strategy(payload)
    prediction = prediction_payload(result)
    current_position = int(result.get("race_state", {}).get("position", payload.get("position", 1)))
    simulated_tire = result.get("tire", {})
    rain_risk = max(
        float(result.get("weather", {}).get("model_rain_risk", payload.get("rain_risk", 0))),
        float(live_result.get("weather", {}).get("model_rain_risk", 0)),
    )
    recommended_tire = (
        "WET"
        if rain_risk > 75
        else "INTERMEDIATE"
        if rain_risk > 45
        else str(payload.get("next_compound", "HARD")).upper()
    )
    projected_position = max(
        1,
        current_position - (1 if prediction["pit_probability"] >= 0.65 else 0),
    )
    return jsonify({
        "pit_probability": prediction["pit_probability"],
        "projected_position": projected_position,
        "expected_gain": prediction["expected_gain"],
        "recommended_tire": recommended_tire,
        "live_current_tire": live_tire,
        "simulated_initial_tire": simulated_tire,
        "target_pit_lap": int(payload.get("target_pit_lap", payload.get("lap", 1))),
        "override_applied": override_enabled,
        "summary": (
            "Safety Car deployment reduces pit-loss exposure."
            if payload.get("safety_car")
            else "Initial tire override applied and the 40-feature vector was rebuilt."
            if override_enabled
            else "Scenario recalculated from the live RaceState feature vector."
        ),
    })


@app.route("/api/driver-comparison", methods=["GET"])
def driver_comparison():
    result = _cached_strategy(request_payload())
    rows = []
    for entry in result.get("classification", []):
        pit_probability = probability_value(entry.get("pit_risk", 0.0))
        telemetry = entry.get("telemetry") or {}
        rows.append({
            "code": entry.get("code", "--"),
            "team": entry.get("team", "Unknown"),
            "position": int(entry.get("position", 0)),
            "gap": entry.get("gap", "--"),
            "compound": entry.get("compound", "UNKNOWN"),
            "tyre_age": int(entry.get("tyre_age", 0)),
            "pit_probability": pit_probability,
            "predicted_pit_lap": entry.get("pit_forecast_lap"),
            "pace_delta": float(telemetry.get("lap_time", 0.0)),
        })
    return jsonify({"drivers": rows, "source": "classification_snapshot"})


@app.route("/api/context", methods=["GET"])
def context():
    return jsonify(context_payload(
        year=request.args.get("year"),
        round_number=request.args.get("round_number"),
    ))


@app.route("/api/simulate", methods=["POST", "OPTIONS"])
@app.route("/api/dashboard", methods=["POST", "OPTIONS"])
def handle_simulation():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    result = simulate_strategy(clean_payload(request.json))
    return jsonify(result)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    requested = FRONTEND_DIST / path
    if path and requested.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )

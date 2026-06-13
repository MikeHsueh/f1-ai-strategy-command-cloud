import numpy as np
import torch

from data_service import dataset_context, enrich_payload_from_dataset
from strategy_model import MODEL_INFO, model, device
from telemetry_engine import FEATURE_COLUMNS, build_feature_vector, calculate_tire_health


def _clip(value, lower=0.0, upper=1.0):
    try:
        value = float(value)
    except Exception:
        value = lower
    return max(lower, min(upper, value))


def _num(payload, key, default=0.0):
    try:
        value = payload.get(key, default)
        if value is None:
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _strategy_side_channels(payload, current_features, pit_prob):
    rain_risk = _clip(max(_num(payload, "rain_risk", 0.0), _num(payload, "historical_rain_risk", 0.0)) / 100.0)
    gap_ahead = max(_num(payload, "gap_ahead", 2.0), 0.0)
    gap_behind = max(_num(payload, "gap_behind", 2.0), 0.0)
    position = int(max(1, _num(payload, "position", 1)))
    circuit = str(payload.get("circuit", "Silverstone"))

    traffic_pressure = _clip((3.0 - min(gap_ahead, gap_behind)) / 3.0)
    street_factor = 1.0 if circuit in {"Monaco", "Baku", "Singapore", "Las Vegas", "Madrid"} else 0.0
    undercut = _clip(0.38 + traffic_pressure * 0.28 + pit_prob * 0.20 - street_factor * 0.10 - rain_risk * 0.08)
    safety_car = _clip(0.04 + rain_risk * 0.28 + street_factor * 0.12 + (0.05 if position > 12 else 0.0))

    degradation = float(current_features.get("Degradation", 0.0))
    expected_gain = max(0.0, 4.8 - degradation * 0.9 - current_features.get("NormalizedPaceLoss", 0.0) * 10.0)

    if rain_risk > 0.75:
        recommended_tire = "WET"
    elif rain_risk > 0.45:
        recommended_tire = "INTERMEDIATE"
    elif pit_prob > 0.70:
        recommended_tire = payload.get("next_compound", "HARD")
    elif pit_prob > 0.42:
        recommended_tire = "READY"
    else:
        recommended_tire = "HOLD"

    optimal_lap = int(min(
        _num(payload, "total_laps", current_features.get("LapNumber", 1) + current_features.get("RemainingLaps", 1)),
        max(current_features.get("LapNumber", 1) + 1, current_features.get("LapNumber", 1) + round(2 + (1 - pit_prob) * 3)),
    ))

    return {
        "undercut": undercut,
        "safety_car": safety_car,
        "expected_gain": expected_gain,
        "recommended_tire": recommended_tire,
        "optimal_lap": optimal_lap,
    }


def simulate_strategy(payload):
    payload = enrich_payload_from_dataset(payload)
    feature_vector, raw_sequence, current_features, scaling = build_feature_vector(payload)
    tensor = torch.tensor(feature_vector, dtype=torch.float32).unsqueeze(0).to(device)

    with torch.no_grad():
        logits, attention_weights = model(tensor, return_attention=True)
        pit_prob = torch.sigmoid(logits).item()

    channels = _strategy_side_channels(payload, current_features, pit_prob)
    attention = attention_weights.squeeze(0).detach().cpu().numpy().round(4).tolist()
    context = dataset_context(payload, pit_probability=pit_prob)

    model_info = {
        **MODEL_INFO,
        "feature_count": len(FEATURE_COLUMNS),
        "feature_columns": FEATURE_COLUMNS,
        "scaler_mode": scaling["mode"],
        "scaler_path": scaling["path"],
    }

    strategy_response = {
        "pit_probability": round(pit_prob * 100, 1),
        "optimal_pit_lap": channels["optimal_lap"],
        "recommended_tire": channels["recommended_tire"],
        "expected_gain": round(channels["expected_gain"], 2),
        "undercut_success_probability": round(channels["undercut"] * 100, 1),
        "undercut_risk": "HIGH" if channels["undercut"] > 0.65 else "LOW",
        "attention": attention,
    }
    tire_degradation = round(float(current_features["Degradation"]), 3)
    tire_life = _num(payload, "tire_age", 0.0)
    tire_compound = payload.get("compound", "MEDIUM")

    if payload.get("safety_car", False):
        sc_option = next((option for option in context.get("multi_strategy", []) if "SC" in option.get("label", "")), None)
        strategy_response["optimal_pit_lap"] = int(_num(payload, "lap", channels["optimal_lap"]))
        strategy_response["safety_car_projected_position"] = sc_option.get("projected_text") if sc_option else None
        strategy_response["safety_car_samples"] = sc_option.get("sample_size") if sc_option else 0

    return {
        "source": "backend",
        "model": model_info,
        "strategy": strategy_response,
        "weather": {
            "track_temp": _num(payload, "track_temp", 0.0),
            "air_temp": _num(payload, "air_temp", 0.0),
            "humidity": _num(payload, "humidity", 0.0),
            "rain_risk": _num(payload, "display_rain_risk", _num(payload, "rain_risk", 0.0)),
            "model_rain_risk": _num(payload, "rain_risk", 0.0),
            "historical_rain_risk": _num(payload, "historical_rain_risk", 0.0),
            "wind_speed": _num(payload, "wind_speed", 0.0),
            "wind_direction": _num(payload, "wind_direction", 0.0),
        },
        "tire": {
            "compound": tire_compound,
            "life": tire_life,
            "degradation": tire_degradation,
            "temperature_proxy": round(float(current_features["TireTemperatureProxy"]), 1),
            "health": calculate_tire_health(tire_compound, tire_life, tire_degradation),
        },
        "telemetry": {
            "speed": _num(payload, "speed", 0.0),
            "rpm": _num(payload, "rpm", 0.0),
            "throttle": _num(payload, "throttle", 0.0),
            "brake": _num(payload, "brake", 0.0),
        },
        "race_state": {
            "lap": int(_num(payload, "lap", 1.0)),
            "position": int(_num(payload, "position", 1.0)),
            "gap_ahead": _num(payload, "gap_ahead", 0.0),
            "gap_behind": _num(payload, "gap_behind", 0.0),
            "safety_car": bool(payload.get("safety_car", False)),
            "safety_car_incident_risk": round(channels["safety_car"] * 100, 1),
        },
        "features": current_features,
        **context,
    }


def predict_probability(payload):
    """Run the trained model without building the heavier dashboard context."""
    enriched = enrich_payload_from_dataset(payload)
    feature_vector, _, _, _ = build_feature_vector(enriched)
    tensor = torch.tensor(feature_vector, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
    return float(torch.sigmoid(logits).item()), enriched


def predict_probabilities(payloads):
    """Run one batched model inference for a sequence of timeline payloads."""
    enriched_payloads = []
    feature_vectors = []

    for payload in payloads:
        enriched = enrich_payload_from_dataset(payload)
        feature_vector, _, _, _ = build_feature_vector(enriched)
        enriched_payloads.append(enriched)
        feature_vectors.append(feature_vector)

    if not feature_vectors:
        return []

    tensor = torch.from_numpy(np.stack(feature_vectors).astype(np.float32)).to(device)
    with torch.inference_mode():
        probabilities = torch.sigmoid(model(tensor)).detach().cpu().tolist()

    return list(zip((float(value) for value in probabilities), enriched_payloads))


def feature_importance(payload):
    """Return local input sensitivity for the selected model inference."""
    enriched = enrich_payload_from_dataset(payload)
    feature_vector, _, current_features, _ = build_feature_vector(enriched)
    tensor = torch.tensor(
        feature_vector,
        dtype=torch.float32,
        device=device,
    ).unsqueeze(0)
    tensor.requires_grad_(True)

    model.zero_grad(set_to_none=True)
    logits = model(tensor)
    logits.sum().backward()
    sensitivity = tensor.grad
    if sensitivity is None:
        importance = torch.ones(len(FEATURE_COLUMNS), device=device)
    else:
        importance = sensitivity.detach().abs().mean(dim=(0, 1))

    total = float(importance.sum().item())
    if total <= 0:
        normalized = [1.0 / len(FEATURE_COLUMNS)] * len(FEATURE_COLUMNS)
    else:
        normalized = (importance / total).detach().cpu().tolist()

    return [
        {
            "name": name,
            "value": float(current_features.get(name, 0.0)),
            "importance": round(float(normalized[index]), 6),
            "group": _feature_group(name),
        }
        for index, name in enumerate(FEATURE_COLUMNS)
    ]


def _feature_group(name):
    groups = {
        "Race State": {"LapNumber", "LapRatio", "Stint", "TyreLife", "RemainingLaps", "FuelLoad"},
        "Tire Compound": {"Soft", "Medium", "Hard", "Intermediate", "Wet", "IsDryTyre", "IsWetTyre"},
        "Telemetry": {"AvgSpeed", "MaxSpeed", "SpeedStd", "ThrottleMean", "ThrottleStd", "BrakeMean", "BrakeRatio", "RPMMean", "RPMStd"},
        "Weather": {"AirTemp", "TrackTemp", "Humidity", "Rainfall", "TrackAirDiff", "WetConditionIndex"},
        "Tire Physics": {"Degradation", "RollingDegradation", "PaceDelta", "MovingAverageLapTime", "LapTimeTrend", "TireTemperatureProxy"},
        "Strategy": {"PitWindowScore", "IsLateStint", "LongRunFlag", "PerformanceLossRate", "NormalizedPaceLoss", "PitPressureIndex"},
    }
    return next((group for group, names in groups.items() if name in names), "Other")

import numpy as np

from chaours.alerts import (
    deficit_alerts,
    neutronic_alerts,
    remit_alerts,
    spot_below_usage_value_alerts,
)
from chaours.types import (
    AlertKind,
    Maintenance,
    OutageKind,
    Plant,
    PlantResult,
    Severity,
)


def _plant(plant_id: str) -> Plant:
    return Plant(
        id=plant_id,
        eic_code=f"EIC-{plant_id}",
        nominal_power_mw=900.0,
        initial_jepp=300.0,
    )


def _result(plant_id: str, depletion_days: list[int] | None = None) -> PlantResult:
    values = [1.0, 1.0, 1.0, 1.0]
    return PlantResult(
        plant_id=plant_id,
        production_factors=values,
        energy_mwh=values,
        remaining_jepp=values,
        depletion_days=list(depletion_days or []),
    )


def _maintenance(start_day: int, end_day: int) -> Maintenance:
    return Maintenance(kind=OutageKind.ASR, start_day=start_day, end_day=end_day)


def test_spot_below_usage_value_raises_alert():
    alerts = spot_below_usage_value_alerts(
        np.array([50.0, 80.0]),
        (_plant("P1"),),
        {"P1": 60.0},
    )

    assert len(alerts) == 1
    assert alerts[0].kind == AlertKind.SPOT_BELOW_USAGE_VALUE
    assert alerts[0].day == 0
    assert alerts[0].plant_id == "P1"


def test_spot_above_usage_value_raises_no_alert():
    alerts = spot_below_usage_value_alerts(
        np.array([70.0, 80.0]),
        (_plant("P1"),),
        {"P1": 60.0},
    )

    assert alerts == []


def test_usage_values_are_matched_by_plant_id_not_order():
    alerts = spot_below_usage_value_alerts(
        np.array([50.0, 80.0]),
        (_plant("P1"), _plant("P2")),
        {"P2": 60.0, "P1": 40.0},
    )

    assert [(alert.plant_id, alert.day) for alert in alerts] == [("P2", 0)]


def test_neutronic_alert_when_depletion_precedes_outage():
    alerts = neutronic_alerts(
        (_result("P1", [5]),),
        {"P1": (_maintenance(10, 12),)},
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.kind == AlertKind.NEUTRONIC_ANOMALY
    assert alert.severity == Severity.CRITICAL
    assert alert.day == 5
    assert alert.plant_id == "P1"
    assert "10" in alert.message
    assert "modulation manuelle" in alert.message


def test_neutronic_alert_when_no_future_stop_exists():
    alerts = neutronic_alerts(
        (_result("P1", [5]),),
        {"P1": (_maintenance(1, 3),)},
    )

    assert len(alerts) == 1
    assert alerts[0].day == 5
    assert "aucun arrêt" in alerts[0].message


def test_neutronic_alert_ignores_other_plants_for_next_stop():
    alerts = neutronic_alerts(
        (_result("P1", [5]),),
        {
            "P2": (_maintenance(7, 9),),
            "P1": (_maintenance(11, 13),),
        },
    )

    assert len(alerts) == 1
    assert "11" in alerts[0].message


def test_one_neutronic_alert_per_depletion_day():
    alerts = neutronic_alerts(
        (_result("P1", [2, 7]),),
        {"P1": (_maintenance(10, 12),)},
    )

    assert [alert.day for alert in alerts] == [2, 7]
    assert all(
        alert.kind == AlertKind.NEUTRONIC_ANOMALY for alert in alerts
    )


def test_remit_alert_above_threshold():
    alerts = remit_alerts(
        np.array([[150.0, 50.0]]),
        ("P1",),
    )

    assert len(alerts) == 1
    assert alerts[0].kind == AlertKind.REMIT_UMM
    assert alerts[0].severity == Severity.WARNING
    assert alerts[0].day == 1
    assert alerts[0].plant_id == "P1"
    assert "P1" in alerts[0].message


def test_no_remit_alert_below_threshold():
    alerts = remit_alerts(
        np.array([[50.0, -20.0]]),
        ("P1",),
    )

    assert alerts == []


def test_remit_threshold_is_strict():
    alerts = remit_alerts(
        np.array([[100.0, -100.0]]),
        ("P1",),
    )

    assert alerts == []


def test_remit_alert_day_index_and_plant_id():
    alerts = remit_alerts(
        np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -200.0],
            ]
        ),
        ("P1", "P2"),
    )

    assert [(alert.plant_id, alert.day) for alert in alerts] == [("P2", 3)]


def test_remit_alerts_include_planned_stop_boundaries():
    alerts = remit_alerts(
        np.array([[-1_000.0, 1_000.0]]),
        ("P1",),
    )

    assert [alert.day for alert in alerts] == [1, 2]


def test_deficit_alert_per_deficit_day():
    alerts = deficit_alerts(np.array([0, 3], dtype=np.intp))

    assert len(alerts) == 2
    assert [alert.day for alert in alerts] == [0, 3]
    assert all(alert.kind == AlertKind.RTE_DEFICIT for alert in alerts)
    assert all(alert.severity == Severity.CRITICAL for alert in alerts)
    assert all(alert.plant_id is None for alert in alerts)


def test_deficit_alerts_empty_without_deficit():
    assert deficit_alerts(np.array([], dtype=np.intp)) == []

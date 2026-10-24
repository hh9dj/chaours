import numpy as np
import pytest

from chaours.alerts import spot_below_usage_value_alerts
from chaours.types import AlertKind, Plant


def _plant(plant_id: str) -> Plant:
    return Plant(
        id=plant_id,
        eic_code=f"EIC-{plant_id}",
        nominal_power_mw=900.0,
        initial_jepp=300.0,
    )


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


@pytest.mark.skip(reason="not implemented")
def test_neutronic_alert_when_depletion_precedes_outage():
    pass


@pytest.mark.skip(reason="not implemented")
def test_remit_alert_above_threshold():
    pass


@pytest.mark.skip(reason="not implemented")
def test_no_remit_alert_below_threshold():
    pass


@pytest.mark.skip(reason="not implemented")
def test_deficit_alert_per_deficit_day():
    pass

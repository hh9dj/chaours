import numpy as np

from chaours.alerts import (
    deficit_alerts,
    neutronic_alerts,
    remit_alerts,
    spot_below_usage_value_alerts,
)
from chaours.types import (
    Arret,
    ResultatTranche,
    TypeAlerte,
    TypeArret,
)


def _result(
    tranche_id: str,
    jours_epuisement: list[int] | None = None,
) -> ResultatTranche:
    values = [1.0, 1.0, 1.0, 1.0]
    return ResultatTranche(
        tranche_id=tranche_id,
        facteurs_production=values,
        energie_mwh=values,
        jepp_restant=values,
        jours_epuisement=list(jours_epuisement or []),
    )


def _arret(jour_debut: int, jour_fin: int) -> Arret:
    return Arret(
        type_arret=TypeArret.ASR,
        jour_debut=jour_debut,
        jour_fin=jour_fin,
    )


def test_spot_below_usage_value_raises_one_national_alert_per_day():
    alerts = spot_below_usage_value_alerts(
        np.array([50.0, 80.0, 40.0]),
        np.array([60.0, 60.0, 60.0]),
    )

    assert len(alerts) == 2
    assert [alerte.type_alerte for alerte in alerts] == [
        TypeAlerte.SPOT_BELOW_USAGE_VALUE,
        TypeAlerte.SPOT_BELOW_USAGE_VALUE,
    ]
    assert [alerte.jour for alerte in alerts] == [0, 2]
    assert all(alerte.tranche_id is None for alerte in alerts)


def test_spot_above_or_equal_usage_value_raises_no_alert():
    alerts = spot_below_usage_value_alerts(
        np.array([70.0, 60.0]),
        np.array([60.0, 60.0]),
    )

    assert alerts == []


def test_neutronic_alert_when_depletion_precedes_outage():
    alerts = neutronic_alerts(
        (_result("P1", [3]),),
        {"P1": (_arret(6, 8),)},
    )

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.type_alerte == TypeAlerte.NEUTRONIC_ANOMALY
    assert alert.jour == 3
    assert alert.tranche_id == "P1"
    assert "6" in alert.message
    assert "modulation manuelle" in alert.message


def test_neutronic_alert_when_no_future_stop_exists():
    alerts = neutronic_alerts(
        (_result("P1", [3]),),
        {"P1": (_arret(0, 2),)},
    )

    assert len(alerts) == 1
    assert alerts[0].jour == 3
    assert "aucun arrêt" in alerts[0].message


def test_neutronic_alert_ignores_other_tranches_for_next_stop():
    alerts = neutronic_alerts(
        (_result("P1", [3]),),
        {
            "P2": (_arret(4, 6),),
            "P1": (_arret(5, 7),),
        },
    )

    assert len(alerts) == 1
    assert "5" in alerts[0].message


def test_one_neutronic_alert_per_depletion_day():
    alerts = neutronic_alerts(
        (_result("P1", [1, 2]),),
        {"P1": (_arret(3, 4),)},
    )

    assert [alerte.jour for alerte in alerts] == [1, 2]
    assert all(
        alerte.type_alerte == TypeAlerte.NEUTRONIC_ANOMALY
        for alerte in alerts
    )


def test_remit_alert_above_threshold():
    alerts = remit_alerts(
        np.array([[150.0, 50.0]]),
        ("P1",),
    )

    assert len(alerts) == 1
    assert alerts[0].type_alerte == TypeAlerte.REMIT_UMM
    assert alerts[0].jour == 1
    assert alerts[0].tranche_id == "P1"
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


def test_remit_alert_day_index_and_tranche_id():
    alerts = remit_alerts(
        np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -200.0],
            ]
        ),
        ("P1", "P2"),
    )

    assert [(alerte.tranche_id, alerte.jour) for alerte in alerts] == [
        ("P2", 3)
    ]


def test_remit_alerts_include_planned_stop_boundaries():
    alerts = remit_alerts(
        np.array([[-1_000.0, 1_000.0]]),
        ("P1",),
    )

    assert [alerte.jour for alerte in alerts] == [1, 2]


def test_deficit_alert_per_deficit_day():
    alerts = deficit_alerts(np.array([0, 3], dtype=np.intp))

    assert len(alerts) == 2
    assert [alerte.jour for alerte in alerts] == [0, 3]
    assert all(
        alerte.type_alerte == TypeAlerte.RTE_DEFICIT for alerte in alerts
    )
    assert all(alerte.tranche_id is None for alerte in alerts)


def test_deficit_alerts_empty_without_deficit():
    assert deficit_alerts(np.array([], dtype=np.intp)) == []

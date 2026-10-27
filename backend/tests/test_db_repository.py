from __future__ import annotations

from collections.abc import Generator

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlmodel import Session

from chaours.db.models import (
    ArretTable,
    DonneeJournaliereTable,
    ModulationTable,
    SimulationTable,
    TrancheTable,
)
from chaours.db.repository import (
    add_tranche,
    create_simulation,
    delete_simulation,
    duplicate_simulation,
    get_simulation,
    list_simulations,
    replace_arrets,
    replace_modulations,
    update_simulation,
    update_tranche,
)
from chaours.db.session import (
    build_engine,
    build_session_factory,
    create_db_and_tables,
)
from chaours.types import (
    Arret,
    ConfigurationTranche,
    Modulation,
    ParametresSimulation,
    Simulation,
    SimulationCreation,
    SimulationTranche,
    Tranche,
    TypeArret,
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = build_engine("sqlite://")
    create_db_and_tables(engine)
    session_factory = build_session_factory(engine)
    with session_factory() as database_session:
        yield database_session


def _simulation(name: str = "simulation") -> Simulation:
    return Simulation(
        nom=name,
        horizon_jours=10,
        prix_spot_eur_mwh=[
            10.5,
            20.0,
            30.25,
            40.0,
            50.0,
            60.0,
            70.0,
            80.0,
            90.0,
            100.0,
        ],
        demande_nationale_mwh=[1_000.0] * 10,
        valeur_usage_eur_mwh=[60.5] * 10,
        tranches=[
            SimulationTranche(
                tranche=Tranche(
                    identifiant="P1",
                    code_eic="EIC-P1",
                    puissance_nominale_mw=900.0,
                    jepp_initial=300.5,
                ),
                arrets=[
                    Arret(
                        type_arret=TypeArret.ASR,
                        jour_debut=1,
                        jour_fin=3,
                    )
                ],
                modulations=[
                    Modulation(jour_debut=4, jour_fin=6, facteur=0.5)
                ],
            ),
            SimulationTranche(
                tranche=Tranche(
                    identifiant="P2",
                    code_eic="EIC-P2",
                    puissance_nominale_mw=1_300.25,
                    jepp_initial=280.0,
                ),
                arrets=[
                    Arret(
                        type_arret=TypeArret.VD,
                        jour_debut=7,
                        jour_fin=9,
                    )
                ],
            ),
        ],
    )


def _creation(simulation: Simulation) -> SimulationCreation:
    return SimulationCreation(
        nom=simulation.nom,
        horizon_jours=simulation.horizon_jours,
        prix_spot_eur_mwh=list(simulation.prix_spot_eur_mwh),
        demande_nationale_mwh=list(simulation.demande_nationale_mwh),
        valeur_usage_eur_mwh=list(simulation.valeur_usage_eur_mwh),
        tranches=list(simulation.tranches),
    )


def _count(session: Session, model: type) -> int:
    count = session.scalar(select(func.count()).select_from(model))
    return int(count or 0)


def test_create_and_get_simulation_round_trip(session: Session):
    simulation = _simulation()

    created = create_simulation(session, _creation(simulation))
    loaded = get_simulation(session, created.simulation_id)

    assert loaded is not None
    assert created.simulation_id != simulation.simulation_id
    assert loaded.simulation_id == created.simulation_id
    assert loaded.nom == "simulation"
    assert loaded.horizon_jours == 10
    assert loaded.prix_spot_eur_mwh == simulation.prix_spot_eur_mwh
    assert loaded.demande_nationale_mwh == simulation.demande_nationale_mwh
    assert loaded.valeur_usage_eur_mwh == simulation.valeur_usage_eur_mwh
    assert [entry.tranche.identifiant for entry in loaded.tranches] == [
        "P1",
        "P2",
    ]
    assert loaded.tranches[0].tranche.puissance_nominale_mw == 900.0
    assert loaded.tranches[0].tranche.jepp_initial == 300.5
    assert loaded.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]
    assert loaded.tranches[0].modulations == [
        Modulation(jour_debut=4, jour_fin=6, facteur=0.5)
    ]
    assert loaded.tranches[1].arrets == [
        Arret(type_arret=TypeArret.VD, jour_debut=7, jour_fin=9)
    ]


def test_get_unknown_simulation_returns_none(session: Session):
    assert get_simulation(session, _simulation().simulation_id) is None


def test_list_simulations_returns_summaries(session: Session):
    first = create_simulation(session, _creation(_simulation("first")))
    second = create_simulation(session, _creation(_simulation("second")))

    summaries = list_simulations(session)

    assert {summary.simulation_id for summary in summaries} == {
        first.simulation_id,
        second.simulation_id,
    }
    assert {summary.nombre_tranches for summary in summaries} == {2}
    assert {summary.horizon_jours for summary in summaries} == {10}


def test_delete_simulation_cascades_to_children(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    assert _count(session, TrancheTable) == 2
    assert _count(session, DonneeJournaliereTable) == 10
    assert _count(session, ArretTable) == 2
    assert _count(session, ModulationTable) == 1

    assert delete_simulation(session, simulation.simulation_id) is True
    assert get_simulation(session, simulation.simulation_id) is None
    assert _count(session, SimulationTable) == 0
    assert _count(session, TrancheTable) == 0
    assert _count(session, DonneeJournaliereTable) == 0
    assert _count(session, ArretTable) == 0
    assert _count(session, ModulationTable) == 0


def test_delete_unknown_simulation_returns_false(session: Session):
    assert delete_simulation(session, _simulation().simulation_id) is False


def test_duplicate_simulation_gets_new_id_and_suffixed_name(
    session: Session,
):
    original = create_simulation(session, _creation(_simulation("plan")))

    duplicate = duplicate_simulation(session, original.simulation_id)

    assert duplicate is not None
    assert duplicate.simulation_id != original.simulation_id
    assert duplicate.nom == "plan (copie)"
    assert duplicate.valeur_usage_eur_mwh == original.valeur_usage_eur_mwh
    assert [entry.tranche.identifiant for entry in duplicate.tranches] == [
        "P1",
        "P2",
    ]
    assert duplicate.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]
    assert get_simulation(session, duplicate.simulation_id) is not None
    assert get_simulation(session, original.simulation_id) is not None


def test_duplicate_name_is_trimmed_to_model_limit(session: Session):
    original = create_simulation(
        session,
        _creation(_simulation("x" * 200)),
    )

    duplicate = duplicate_simulation(session, original.simulation_id)

    assert duplicate is not None
    assert len(duplicate.nom) == 200
    assert duplicate.nom.endswith(" (copie)")


def test_duplicate_unknown_simulation_returns_none(session: Session):
    assert duplicate_simulation(session, _simulation().simulation_id) is None


def test_update_simulation_replaces_parameters_and_series(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    payload = ParametresSimulation(
        nom="renamed",
        horizon_jours=10,
        prix_spot_eur_mwh=[1.0] * 10,
        demande_nationale_mwh=[2.0] * 10,
        valeur_usage_eur_mwh=[3.0] * 10,
    )

    updated = update_simulation(session, simulation.simulation_id, payload)

    assert updated is not None
    assert updated.nom == "renamed"
    assert updated.prix_spot_eur_mwh == [1.0] * 10
    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.demande_nationale_mwh == [2.0] * 10
    assert loaded.valeur_usage_eur_mwh == [3.0] * 10


def test_update_simulation_rejects_schedules_outside_new_horizon(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))
    payload = ParametresSimulation(
        nom="shorter",
        horizon_jours=5,
        prix_spot_eur_mwh=[1.0] * 5,
        demande_nationale_mwh=[2.0] * 5,
        valeur_usage_eur_mwh=[3.0] * 5,
    )

    with pytest.raises(ValidationError):
        update_simulation(session, simulation.simulation_id, payload)

    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.horizon_jours == 10


def test_update_unknown_simulation_returns_none(session: Session):
    payload = ParametresSimulation(
        nom="unknown",
        horizon_jours=4,
        prix_spot_eur_mwh=[1.0] * 4,
        demande_nationale_mwh=[2.0] * 4,
        valeur_usage_eur_mwh=[3.0] * 4,
    )

    assert update_simulation(
        session,
        _simulation().simulation_id,
        payload,
    ) is None


def test_update_tranche_keeps_identifier_and_replaces_configuration(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))
    payload = ConfigurationTranche(
        code_eic="EIC-NEW",
        puissance_nominale_mw=1_100.0,
        jepp_initial=250.0,
    )

    updated = update_tranche(
        session,
        simulation.simulation_id,
        "P1",
        payload,
    )

    assert updated is not None
    assert updated.tranches[0].tranche.identifiant == "P1"
    assert updated.tranches[0].tranche.code_eic == "EIC-NEW"
    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].tranche.puissance_nominale_mw == 1_100.0
    assert loaded.tranches[0].tranche.jepp_initial == 250.0


def test_update_tranche_returns_none_for_unknown_tranche(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    payload = ConfigurationTranche(
        code_eic="EIC-NEW",
        puissance_nominale_mw=1_100.0,
        jepp_initial=250.0,
    )

    assert update_tranche(
        session,
        simulation.simulation_id,
        "UNKNOWN",
        payload,
    ) is None


def test_replace_arrets_persists_validated_simulation(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    replacement = [
        Arret(type_arret=TypeArret.VP, jour_debut=2, jour_fin=4)
    ]

    updated = replace_arrets(
        session,
        simulation.simulation_id,
        "P1",
        replacement,
    )

    assert updated is not None
    assert updated.tranches[0].arrets == replacement
    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].arrets == replacement
    assert loaded.tranches[1].arrets == [
        Arret(type_arret=TypeArret.VD, jour_debut=7, jour_fin=9)
    ]


def test_replace_modulations_persists_validated_simulation(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))
    replacement = [
        Modulation(jour_debut=1, jour_fin=3, facteur=0.25),
        Modulation(jour_debut=3, jour_fin=5, facteur=0.75),
    ]

    updated = replace_modulations(
        session,
        simulation.simulation_id,
        "P1",
        replacement,
    )

    assert updated is not None
    assert updated.tranches[0].modulations == replacement
    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].modulations == replacement


def test_replace_schedules_returns_none_for_unknown_simulation(
    session: Session,
):
    assert (
        replace_arrets(
            session,
            _simulation().simulation_id,
            "P1",
            [],
        )
        is None
    )
    assert (
        replace_modulations(
            session,
            _simulation().simulation_id,
            "P1",
            [],
        )
        is None
    )


def test_replace_schedules_returns_none_for_unknown_tranche(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))

    assert (
        replace_arrets(
            session,
            simulation.simulation_id,
            "UNKNOWN",
            [],
        )
        is None
    )
    assert (
        replace_modulations(
            session,
            simulation.simulation_id,
            "UNKNOWN",
            [],
        )
        is None
    )


def test_replace_arrets_rejects_overlap_without_persisting(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))

    with pytest.raises(ValidationError):
        replace_arrets(
            session,
            simulation.simulation_id,
            "P1",
            [
                Arret(
                    type_arret=TypeArret.ASR,
                    jour_debut=1,
                    jour_fin=4,
                ),
                Arret(
                    type_arret=TypeArret.VP,
                    jour_debut=3,
                    jour_fin=5,
                ),
            ],
        )

    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]


def test_replace_arrets_rejects_window_outside_horizon(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))

    with pytest.raises(ValidationError):
        replace_arrets(
            session,
            simulation.simulation_id,
            "P1",
            [Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=11)],
        )

    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]


def test_simulations_are_isolated(session: Session):
    first = create_simulation(session, _creation(_simulation("first")))
    second = create_simulation(session, _creation(_simulation("second")))

    replace_arrets(
        session,
        first.simulation_id,
        "P1",
        [Arret(type_arret=TypeArret.VP, jour_debut=2, jour_fin=4)],
    )

    loaded_first = get_simulation(session, first.simulation_id)
    loaded_second = get_simulation(session, second.simulation_id)
    assert loaded_first is not None
    assert loaded_second is not None
    assert loaded_first.tranches[0].arrets == [
        Arret(type_arret=TypeArret.VP, jour_debut=2, jour_fin=4)
    ]
    assert loaded_second.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]


def test_get_simulation_rejects_missing_daily_row(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    row = session.get(
        DonneeJournaliereTable,
        (simulation.simulation_id, 5),
    )
    assert row is not None
    session.delete(row)
    session.commit()

    with pytest.raises(ValueError):
        get_simulation(session, simulation.simulation_id)


def test_get_simulation_rejects_out_of_horizon_daily_row(
    session: Session,
):
    simulation = create_simulation(session, _creation(_simulation()))
    session.add(
        DonneeJournaliereTable(
            simulation_id=simulation.simulation_id,
            jour=10,
            prix_spot_eur_mwh=1.0,
            demande_nationale_mwh=1.0,
            valeur_usage_eur_mwh=1.0,
        )
    )
    session.commit()

    with pytest.raises(ValueError):
        get_simulation(session, simulation.simulation_id)


def test_create_and_get_simulation_without_tranches(session: Session):
    simulation = _simulation()
    simulation.tranches = []

    created = create_simulation(session, _creation(simulation))
    loaded = get_simulation(session, created.simulation_id)

    assert loaded is not None
    assert loaded.tranches == []
    summaries = list_simulations(session)
    assert summaries[0].nombre_tranches == 0


def test_add_tranche_to_empty_simulation(session: Session):
    simulation = _simulation()
    simulation.tranches = []
    created = create_simulation(session, _creation(simulation))
    entry = SimulationTranche(
        tranche=Tranche(
            identifiant="P1",
            code_eic="EIC-P1",
            puissance_nominale_mw=900.0,
            jepp_initial=300.0,
        ),
        arrets=[
            Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
        ],
    )

    updated = add_tranche(session, created.simulation_id, entry)

    assert updated is not None
    assert [item.tranche.identifiant for item in updated.tranches] == ["P1"]
    loaded = get_simulation(session, created.simulation_id)
    assert loaded is not None
    assert loaded.tranches[0].tranche.identifiant == "P1"
    assert loaded.tranches[0].arrets == [
        Arret(type_arret=TypeArret.ASR, jour_debut=1, jour_fin=3)
    ]


def test_add_tranche_rejects_duplicate_identifier(session: Session):
    simulation = create_simulation(session, _creation(_simulation()))
    duplicate = SimulationTranche(
        tranche=Tranche(
            identifiant="P1",
            code_eic="EIC-DUP",
            puissance_nominale_mw=900.0,
            jepp_initial=300.0,
        )
    )

    with pytest.raises(ValidationError):
        add_tranche(session, simulation.simulation_id, duplicate)

    loaded = get_simulation(session, simulation.simulation_id)
    assert loaded is not None
    assert [item.tranche.identifiant for item in loaded.tranches] == [
        "P1",
        "P2",
    ]


def test_add_tranche_returns_none_for_unknown_simulation(
    session: Session,
):
    entry = SimulationTranche(
        tranche=Tranche(
            identifiant="P1",
            code_eic="EIC-P1",
            puissance_nominale_mw=900.0,
            jepp_initial=300.0,
        )
    )

    assert add_tranche(session, _simulation().simulation_id, entry) is None

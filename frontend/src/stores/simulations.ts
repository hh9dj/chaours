import { defineStore } from 'pinia'

import {
  ApiError,
  ajouterTranche as ajouterTrancheApi,
  chargerSimulation as chargerSimulationApi,
  creerSimulation as creerSimulationApi,
  executerSimulation,
  listerSimulations,
  messageErreur,
  modifierArrets as modifierArretsApi,
  modifierConfigurationTranche,
  modifierModulations as modifierModulationsApi,
  modifierSimulation as modifierSimulationApi,
  supprimerSimulation as supprimerSimulationApi,
} from '../api/client'
import type {
  Arret,
  ConfigurationTranche,
  Modulation,
  ParametresSimulation,
  ResultatSimulation,
  Simulation,
  SimulationCreation,
  SimulationResume,
  SimulationTranche,
} from '../api/types'

interface EtatSimulations {
  simulations: SimulationResume[]
  currentSimulation: Simulation | null
  currentResult: ResultatSimulation | null
  loading: boolean
  saving: boolean
  error: string | null
  errorStatus: number | null
}

export const useSimulationsStore = defineStore('simulations', {
  state: (): EtatSimulations => ({
    simulations: [],
    currentSimulation: null,
    currentResult: null,
    loading: false,
    saving: false,
    error: null,
    errorStatus: null,
  }),

  actions: {
    definirErreur(error: unknown) {
      this.error = messageErreur(error)
      this.errorStatus = error instanceof ApiError ? error.statut : null
    },

    reinitialiserErreur() {
      this.error = null
      this.errorStatus = null
    },

    async chargerListe() {
      this.loading = true
      this.reinitialiserErreur()
      try {
        this.simulations = await listerSimulations()
      } catch (error) {
        this.definirErreur(error)
      } finally {
        this.loading = false
      }
    },

    async rafraichirListeSilencieusement() {
      try {
        this.simulations = await listerSimulations()
      } catch {
        // La liste sera rechargée par le dashboard.
      }
    },

    async chargerSimulation(simulationId: string) {
      this.loading = true
      this.reinitialiserErreur()
      this.currentSimulation = null
      this.currentResult = null

      try {
        const simulation = await chargerSimulationApi(simulationId)
        this.currentSimulation = simulation
        this.currentResult = await executerSimulation(simulationId)
      } catch (error) {
        this.definirErreur(error)
        this.currentSimulation = null
        this.currentResult = null
      } finally {
        this.loading = false
      }
    },

    async rechargerApresEchec(simulationId: string) {
      this.currentResult = null
      try {
        this.currentSimulation = await chargerSimulationApi(simulationId)
        this.currentResult = await executerSimulation(simulationId)
      } catch {
        // L'erreur initiale reste affichée et aucun résultat incohérent ne reste visible.
      }
    },

    async creerSimulation(payload: SimulationCreation): Promise<Simulation> {
      this.saving = true
      this.reinitialiserErreur()
      try {
        const simulation = await creerSimulationApi(payload)
        this.currentSimulation = simulation
        await this.rafraichirListeSilencieusement()
        return simulation
      } catch (error) {
        this.definirErreur(error)
        throw error
      } finally {
        this.saving = false
      }
    },

    async supprimerSimulation(simulationId: string) {
      this.saving = true
      this.reinitialiserErreur()
      try {
        await supprimerSimulationApi(simulationId)
        this.simulations = this.simulations.filter(
          (simulation) => simulation.simulation_id !== simulationId,
        )
        if (this.currentSimulation?.simulation_id === simulationId) {
          this.currentSimulation = null
          this.currentResult = null
        }
      } catch (error) {
        this.definirErreur(error)
        throw error
      } finally {
        this.saving = false
      }
    },

    async ajouterTranche(
      simulationId: string,
      payload: SimulationTranche,
    ) {
      this.saving = true
      this.reinitialiserErreur()
      try {
        this.currentSimulation = await ajouterTrancheApi(
          simulationId,
          payload,
        )
        this.currentResult = await executerSimulation(simulationId)
      } catch (error) {
        this.definirErreur(error)
        await this.rechargerApresEchec(simulationId)
        throw error
      } finally {
        this.saving = false
      }
    },

    async enregistrerTranche(
      simulationId: string,
      trancheId: string,
      configuration: ConfigurationTranche,
      arrets: Arret[],
      modulations: Modulation[],
    ) {
      this.saving = true
      this.reinitialiserErreur()
      try {
        let simulation = await modifierConfigurationTranche(
          simulationId,
          trancheId,
          configuration,
        )
        this.currentSimulation = simulation

        simulation = await modifierArretsApi(simulationId, trancheId, arrets)
        this.currentSimulation = simulation

        simulation = await modifierModulationsApi(
          simulationId,
          trancheId,
          modulations,
        )
        this.currentSimulation = simulation

        this.currentResult = await executerSimulation(simulationId)
      } catch (error) {
        this.definirErreur(error)
        await this.rechargerApresEchec(simulationId)
        throw error
      } finally {
        this.saving = false
      }
    },

    async enregistrerParametres(
      simulationId: string,
      payload: ParametresSimulation,
    ) {
      this.saving = true
      this.reinitialiserErreur()
      try {
        this.currentSimulation = await modifierSimulationApi(
          simulationId,
          payload,
        )
        this.currentResult = await executerSimulation(simulationId)
      } catch (error) {
        this.definirErreur(error)
        await this.rechargerApresEchec(simulationId)
        throw error
      } finally {
        this.saving = false
      }
    },

    async relancerSimulation(simulationId: string) {
      this.saving = true
      this.reinitialiserErreur()
      try {
        this.currentResult = await executerSimulation(simulationId)
      } catch (error) {
        this.definirErreur(error)
        throw error
      } finally {
        this.saving = false
      }
    },
  },
})

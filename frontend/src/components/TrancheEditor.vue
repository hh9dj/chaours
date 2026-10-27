<script setup lang="ts">
import { reactive, ref } from 'vue'

import { messageErreur } from '../api/client'
import type {
  Arret,
  Modulation,
  SimulationTranche,
  TypeArret,
} from '../api/types'
import { useSimulationsStore } from '../stores/simulations'
import {
  libelleTypeArret,
  validerFenetres,
  validerModulations,
} from '../lib/timeline'
import BaseDialog from './BaseDialog.vue'

const props = defineProps<{
  simulationId: string
  simulationTranche: SimulationTranche
  horizonJours: number
}>()

const emit = defineEmits<{
  fermer: []
  enregistre: []
}>()

const store = useSimulationsStore()

const identifiant = props.simulationTranche.tranche.identifiant
const configuration = reactive({
  code_eic: props.simulationTranche.tranche.code_eic,
  puissance_nominale_mw: props.simulationTranche.tranche.puissance_nominale_mw,
  jepp_initial: props.simulationTranche.tranche.jepp_initial,
})
const arrets = ref<Arret[]>(
  props.simulationTranche.arrets.map((arret) => ({ ...arret })),
)
const modulations = ref<Modulation[]>(
  props.simulationTranche.modulations.map((modulation) => ({ ...modulation })),
)
const erreurs = ref<string[]>([])
const erreurApi = ref<string | null>(null)

function ajouterArret() {
  arrets.value.push({
    type_arret: 'ASR',
    jour_debut: 0,
    jour_fin: Math.min(30, props.horizonJours),
  })
}

function supprimerArret(index: number) {
  arrets.value.splice(index, 1)
}

function ajouterModulation() {
  modulations.value.push({
    jour_debut: 0,
    jour_fin: Math.min(30, props.horizonJours),
    facteur: 1,
  })
}

function supprimerModulation(index: number) {
  modulations.value.splice(index, 1)
}

function valider(): {
  arretsPayload: Arret[]
  modulationsPayload: Modulation[]
} | null {
  const messages: string[] = []

  if (configuration.code_eic.trim().length === 0) {
    messages.push('Le code EIC est obligatoire.')
  }
  const puissance = Number(configuration.puissance_nominale_mw)
  if (!Number.isFinite(puissance) || puissance <= 0) {
    messages.push('La puissance nominale doit être supérieure à 0 MW.')
  }
  const jepp = Number(configuration.jepp_initial)
  if (!Number.isFinite(jepp) || jepp < 0) {
    messages.push('Le JEPP initial doit être positif ou nul.')
  }

  const arretsPayload: Arret[] = arrets.value.map((arret) => ({
    type_arret: arret.type_arret,
    jour_debut: Number(arret.jour_debut),
    jour_fin: Number(arret.jour_fin),
  }))
  const modulationsPayload: Modulation[] = modulations.value.map(
    (modulation) => ({
      jour_debut: Number(modulation.jour_debut),
      jour_fin: Number(modulation.jour_fin),
      facteur: Number(modulation.facteur),
    }),
  )

  messages.push(
    ...validerFenetres(arretsPayload, props.horizonJours, 'Arrêt').map(
      (erreur) => erreur.message,
    ),
    ...validerModulations(
      modulationsPayload,
      props.horizonJours,
    ).map((erreur) => erreur.message),
  )

  erreurs.value = messages
  if (messages.length > 0) return null

  return { arretsPayload, modulationsPayload }
}

async function enregistrer() {
  erreurApi.value = null
  const donnees = valider()
  if (!donnees) return

  try {
    await store.enregistrerTranche(
      props.simulationId,
      identifiant,
      {
        code_eic: configuration.code_eic.trim(),
        puissance_nominale_mw: Number(configuration.puissance_nominale_mw),
        jepp_initial: Number(configuration.jepp_initial),
      },
      donnees.arretsPayload,
      donnees.modulationsPayload,
    )
    emit('enregistre')
  } catch (error) {
    erreurApi.value = messageErreur(error)
  }
}
</script>

<template>
  <BaseDialog
    :titre="`Modifier la tranche ${identifiant}`"
    description="Les modifications sont enregistrées côté serveur, puis la simulation est recalculée."
    taille="large"
    :closeable="!store.saving"
    @fermer="emit('fermer')"
  >
    <div
      v-if="erreurs.length > 0 || erreurApi"
      role="alert"
      class="mb-5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <p v-if="erreurApi">{{ erreurApi }}</p>
      <ul v-if="erreurs.length > 0" class="list-inside list-disc space-y-1">
        <li v-for="erreur in erreurs" :key="erreur">{{ erreur }}</li>
      </ul>
    </div>

    <div class="space-y-6">
      <section class="rounded-xl border border-slate-200 p-4">
        <h3 class="text-sm font-semibold text-slate-950">Configuration</h3>
        <p class="mt-1 text-xs text-slate-500">
          L’identifiant est immuable. L’horizon courant est de
          {{ horizonJours }} jours.
        </p>

        <div class="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label for="tranche-identifiant" class="etiquette">
              Identifiant
            </label>
            <input
              id="tranche-identifiant"
              class="champ bg-slate-100 text-slate-600"
              type="text"
              :value="identifiant"
              readonly
              aria-readonly="true"
            />
          </div>
          <div>
            <label for="tranche-code-eic" class="etiquette">Code EIC</label>
            <input
              id="tranche-code-eic"
              v-model="configuration.code_eic"
              class="champ"
              type="text"
              autocomplete="off"
            />
          </div>
          <div>
            <label for="tranche-puissance" class="etiquette">
              Puissance nominale (MW)
            </label>
            <input
              id="tranche-puissance"
              v-model.number="configuration.puissance_nominale_mw"
              class="champ"
              type="number"
              min="0"
              step="any"
            />
          </div>
          <div>
            <label for="tranche-jepp" class="etiquette">JEPP initial</label>
            <input
              id="tranche-jepp"
              v-model.number="configuration.jepp_initial"
              class="champ"
              type="number"
              min="0"
              step="any"
            />
          </div>
        </div>
      </section>

      <section class="rounded-xl border border-slate-200 p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold text-slate-950">Arrêts</h3>
            <p class="mt-1 text-xs text-slate-500">
              Intervalle semi-ouvert : le jour de fin est exclu. Deux arrêts ne
              peuvent pas se chevaucher.
            </p>
          </div>
          <button type="button" class="bouton-secondaire" @click="ajouterArret">
            + Ajouter un arrêt
          </button>
        </div>

        <p
          v-if="arrets.length === 0"
          class="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500"
        >
          Aucun arrêt planifié sur cette tranche.
        </p>

        <ul v-else class="mt-4 space-y-3">
          <li
            v-for="(arret, index) in arrets"
            :key="index"
            class="grid items-end gap-3 rounded-lg bg-slate-50 p-3 md:grid-cols-[1.6fr_0.8fr_0.8fr_auto]"
          >
            <div>
              <label :for="`arret-type-${index}`" class="etiquette">
                Type d’arrêt
              </label>
              <select
                :id="`arret-type-${index}`"
                v-model="arret.type_arret"
                class="champ"
              >
                <option
                  v-for="type in (['ASR', 'VP', 'VD'] as TypeArret[])"
                  :key="type"
                  :value="type"
                >
                  {{ libelleTypeArret(type) }}
                </option>
              </select>
            </div>
            <div>
              <label :for="`arret-debut-${index}`" class="etiquette">
                Jour de début
              </label>
              <input
                :id="`arret-debut-${index}`"
                v-model.number="arret.jour_debut"
                class="champ"
                type="number"
                min="0"
                step="1"
              />
            </div>
            <div>
              <label :for="`arret-fin-${index}`" class="etiquette">
                Jour de fin (exclu)
              </label>
              <input
                :id="`arret-fin-${index}`"
                v-model.number="arret.jour_fin"
                class="champ"
                type="number"
                min="1"
                step="1"
              />
            </div>
            <button
              type="button"
              class="bouton-discret mb-0.5 text-red-700 hover:bg-red-50 hover:text-red-800"
              :aria-label="`Supprimer l’arrêt ${index + 1}`"
              @click="supprimerArret(index)"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </section>

      <section class="rounded-xl border border-slate-200 p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold text-slate-950">Modulations</h3>
            <p class="mt-1 text-xs text-slate-500">
              Facteur entre 0 et 1. Les fenêtres ne peuvent pas se chevaucher.
            </p>
          </div>
          <button
            type="button"
            class="bouton-secondaire"
            @click="ajouterModulation"
          >
            + Ajouter une modulation
          </button>
        </div>

        <p
          v-if="modulations.length === 0"
          class="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500"
        >
          Aucune modulation planifiée sur cette tranche.
        </p>

        <ul v-else class="mt-4 space-y-3">
          <li
            v-for="(modulation, index) in modulations"
            :key="index"
            class="grid items-end gap-3 rounded-lg bg-slate-50 p-3 md:grid-cols-[1fr_1fr_0.8fr_auto]"
          >
            <div>
              <label :for="`modulation-debut-${index}`" class="etiquette">
                Jour de début
              </label>
              <input
                :id="`modulation-debut-${index}`"
                v-model.number="modulation.jour_debut"
                class="champ"
                type="number"
                min="0"
                step="1"
              />
            </div>
            <div>
              <label :for="`modulation-fin-${index}`" class="etiquette">
                Jour de fin (exclu)
              </label>
              <input
                :id="`modulation-fin-${index}`"
                v-model.number="modulation.jour_fin"
                class="champ"
                type="number"
                min="1"
                step="1"
              />
            </div>
            <div>
              <label :for="`modulation-facteur-${index}`" class="etiquette">
                Facteur (0 à 1)
              </label>
              <input
                :id="`modulation-facteur-${index}`"
                v-model.number="modulation.facteur"
                class="champ"
                type="number"
                min="0"
                max="1"
                step="0.05"
              />
            </div>
            <button
              type="button"
              class="bouton-discret mb-0.5 text-red-700 hover:bg-red-50 hover:text-red-800"
              :aria-label="`Supprimer la modulation ${index + 1}`"
              @click="supprimerModulation(index)"
            >
              Supprimer
            </button>
          </li>
        </ul>
      </section>
    </div>

    <template #pied>
      <button
        type="button"
        class="bouton-secondaire"
        :disabled="store.saving"
        @click="emit('fermer')"
      >
        Annuler
      </button>
      <button
        type="button"
        class="bouton-primaire"
        :disabled="store.saving"
        @click="enregistrer"
      >
        {{ store.saving ? 'Enregistrement…' : 'Enregistrer et recalculer' }}
      </button>
    </template>
  </BaseDialog>
</template>

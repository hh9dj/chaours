<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'

import ChaoursLogo from './components/ChaoursLogo.vue'
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="border-b border-edf-blue-deep bg-edf-blue text-white">
      <div
        class="mx-auto flex w-full max-w-[1600px] items-center justify-between gap-6 px-6 py-4"
      >
        <RouterLink
          to="/"
          class="flex items-center gap-3 rounded-lg focus-visible:outline-edf-orange"
          aria-label="CHAOURS, revenir au tableau de bord"
        >
          <ChaoursLogo />
          <span>
            <span class="block text-base font-bold tracking-[0.18em]">CHAOURS</span>
            <span class="block text-xs text-blue-100/75">
              Programmation des arrêts nucléaires
            </span>
          </span>
        </RouterLink>

        <p class="hidden text-xs text-blue-100/75 md:block">
          Les calculs sont réalisés côté serveur.
        </p>
      </div>
    </header>

    <main class="mx-auto w-full max-w-[1600px] flex-1 px-6 py-8">
      <RouterView />
    </main>

    <footer class="border-t border-edf-grey bg-white">
      <div
        class="mx-auto flex w-full max-w-[1600px] flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-slate-500"
      >
        <span>CHAOURS — simulateur d’aide à la décision</span>
        <span>Interface de démonstration, calculs métier serveur</span>
      </div>
    </footer>
  </div>
</template>

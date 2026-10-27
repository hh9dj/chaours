<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <header class="border-b border-slate-200 bg-slate-950 text-white">
      <div
        class="mx-auto flex w-full max-w-[1600px] items-center justify-between gap-6 px-6 py-4"
      >
        <RouterLink
          to="/"
          class="flex items-center gap-3 rounded-lg focus-visible:outline-sky-400"
          aria-label="CHAOURS, revenir au tableau de bord"
        >
          <span
            class="flex h-9 w-9 items-end justify-center gap-0.5 rounded-lg bg-sky-500 px-2 py-1.5"
            aria-hidden="true"
          >
            <span class="h-2 w-1 rounded-sm bg-slate-950" />
            <span class="h-4 w-1 rounded-sm bg-slate-950" />
            <span class="h-3 w-1 rounded-sm bg-slate-950" />
            <span class="h-5 w-1 rounded-sm bg-slate-950" />
          </span>
          <span>
            <span class="block text-base font-bold tracking-[0.18em]">CHAOURS</span>
            <span class="block text-xs text-slate-400">
              Programmation des arrêts nucléaires
            </span>
          </span>
        </RouterLink>

        <p class="hidden text-xs text-slate-400 md:block">
          Les calculs sont réalisés côté serveur.
        </p>
      </div>
    </header>

    <main class="mx-auto w-full max-w-[1600px] flex-1 px-6 py-8">
      <RouterView />
    </main>

    <footer class="border-t border-slate-200 bg-white">
      <div
        class="mx-auto flex w-full max-w-[1600px] flex-wrap items-center justify-between gap-2 px-6 py-4 text-xs text-slate-500"
      >
        <span>CHAOURS — simulateur d’aide à la décision</span>
        <span>Interface de démonstration, calculs métier serveur</span>
      </div>
    </footer>
  </div>
</template>

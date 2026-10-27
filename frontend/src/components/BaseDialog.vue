<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    titre: string
    description?: string
    taille?: 'normal' | 'large'
    closeable?: boolean
  }>(),
  {
    description: '',
    taille: 'normal',
    closeable: true,
  },
)

const emit = defineEmits<{ fermer: [] }>()

const titreId = useId()
const panneau = ref<HTMLElement | null>(null)

function fermer() {
  emit('fermer')
}

function surTouche(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.closeable) fermer()
}

onMounted(() => {
  document.addEventListener('keydown', surTouche)
  document.body.classList.add('overflow-hidden')
  panneau.value?.focus()
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', surTouche)
  document.body.classList.remove('overflow-hidden')
})
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-edf-blue-deep/55 p-4 backdrop-blur-sm sm:p-8"
      @click.self="closeable && fermer()"
    >
      <section
        ref="panneau"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titreId"
        tabindex="-1"
        class="my-auto w-full overflow-hidden rounded-2xl border border-edf-grey bg-white shadow-2xl"
        :class="taille === 'large' ? 'max-w-5xl' : 'max-w-2xl'"
      >
        <header
          class="flex items-start justify-between gap-4 border-b border-edf-grey px-6 py-5"
        >
          <div>
            <h2 :id="titreId" class="text-lg font-semibold text-slate-950">
              {{ titre }}
            </h2>
            <p v-if="description" class="mt-1 text-sm text-slate-500">
              {{ description }}
            </p>
          </div>
          <button
            type="button"
            class="bouton-discret shrink-0"
            aria-label="Fermer la fenêtre"
            :disabled="!closeable"
            @click="fermer"
          >
            <span aria-hidden="true" class="text-lg leading-none">×</span>
          </button>
        </header>

        <div class="px-6 py-5">
          <slot />
        </div>

        <footer
          v-if="$slots.pied"
          class="flex flex-wrap items-center justify-end gap-3 border-t border-edf-grey bg-edf-paper px-6 py-4"
        >
          <slot name="pied" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

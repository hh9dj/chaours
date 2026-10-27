<template>
  <span
    class="block h-12 w-12 shrink-0 overflow-hidden rounded-2xl shadow-sm ring-1 ring-white/10 sm:h-14 sm:w-14"
    aria-hidden="true"
  >
    <svg
      class="h-full w-full"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="chaours-logo-bg" x1="10" y1="4" x2="54" y2="62" gradientUnits="userSpaceOnUse">
          <stop stop-color="#0A4F9C" />
          <stop offset="1" stop-color="#052A5C" />
        </linearGradient>
        <linearGradient id="chaours-logo-tower" x1="23" y1="18" x2="42" y2="55" gradientUnits="userSpaceOnUse">
          <stop stop-color="#FFFFFF" />
          <stop offset="0.55" stop-color="#EAF2FB" />
          <stop offset="1" stop-color="#C9D9EC" />
        </linearGradient>
        <filter id="chaours-logo-steam-blur" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.15" />
        </filter>
      </defs>

      <rect width="64" height="64" rx="15" fill="url(#chaours-logo-bg)" />
      <circle cx="32" cy="26" r="18" fill="#FF5E11" fill-opacity="0.12" />

      <g filter="url(#chaours-logo-steam-blur)">
        <g class="steam steam-un">
          <ellipse cx="32" cy="14" rx="7.2" ry="3.1" fill="white" />
          <ellipse cx="27.5" cy="11.5" rx="4.2" ry="2.3" fill="white" />
          <ellipse cx="36" cy="12.2" rx="4.8" ry="2.5" fill="white" />
        </g>
        <g class="steam steam-deux">
          <ellipse cx="33" cy="11" rx="6.2" ry="3" fill="white" />
          <ellipse cx="29" cy="8.5" rx="4.6" ry="2.4" fill="white" />
        </g>
        <g class="steam steam-trois">
          <ellipse cx="30" cy="8" rx="5.5" ry="2.7" fill="white" />
          <ellipse cx="35" cy="6.5" rx="3.8" ry="2.1" fill="white" />
        </g>
      </g>

      <path
        d="M12 54C18 47 22 40 24 33C25.2 28.5 24.4 22.5 22 18H42C39.6 22.5 38.8 28.5 40 33C42 40 46 47 52 54H12Z"
        fill="url(#chaours-logo-tower)"
      />
      <ellipse cx="32" cy="18" rx="10" ry="2.2" fill="#F5F9FD" />
      <ellipse cx="32" cy="18" rx="7.4" ry="1.35" fill="#AFC3DC" opacity="0.7" />
      <path
        d="M23.5 34C24.5 38 24 44 22 50"
        stroke="#B7C9E2"
        stroke-width="1.6"
        stroke-linecap="round"
        opacity="0.9"
      />
      <path
        d="M19 41C19.5 44 18.5 48 16.5 51"
        stroke="#D8E4F2"
        stroke-width="1.4"
        stroke-linecap="round"
        opacity="0.8"
      />

      <path
        d="M10 54H54"
        stroke="#FF5E11"
        stroke-width="2.4"
        stroke-linecap="round"
      />
    </svg>
  </span>
</template>

<style scoped>
.steam {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: chaours-steam 5.4s ease-in-out infinite;
}

.steam-deux {
  animation-delay: 1.8s;
}

.steam-trois {
  animation-delay: 3.6s;
}

@keyframes chaours-steam {
  0% {
    opacity: 0;
    transform: translateY(4px) scale(0.8);
  }
  28% {
    opacity: 0.58;
  }
  100% {
    opacity: 0;
    transform: translateY(-8px) scale(1.28);
  }
}

@media (prefers-reduced-motion: reduce) {
  .steam {
    animation: none;
    opacity: 0.28;
    transform: none;
  }
}
</style>

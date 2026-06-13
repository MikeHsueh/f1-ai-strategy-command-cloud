import { nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { driver, type DriveStep, type Driver } from 'driver.js'

const TOUR_STORAGE_KEY = 'hasSeenOnboardingTour'
const TOUR_VERSION = 'full-site-v2'
const REQUIRED_TOUR_TARGET = '[data-tour="driver-selector"]'

type TourEntry = {
  routeName: 'dashboard' | 'replay' | 'simulator' | 'model-analysis'
  step: DriveStep
}

let activeTour: Driver | null = null

function hasSeenTour(): boolean {
  return window.localStorage.getItem(TOUR_STORAGE_KEY) === TOUR_VERSION
}

function markTourAsSeen(): void {
  window.localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION)
}

async function waitForTourTarget(selector: string, attempts = 40): Promise<boolean> {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (document.querySelector(selector)) return true
    await new Promise<void>((resolve) => window.setTimeout(resolve, 100))
  }

  return false
}

function getTargetSelector(entry: TourEntry): string {
  return typeof entry.step.element === 'string' ? entry.step.element : REQUIRED_TOUR_TARGET
}

const tourEntries: TourEntry[] = [
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="app-welcome"]',
      popover: {
        title: 'Welcome to F1 AI Strategy Command',
        description: 'This command center combines race context, tire physics, weather, and the 40-feature BiLSTM model to support pit-stop decisions.',
        side: 'bottom',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="driver-selector"]',
      popover: {
        title: 'Choose the race context',
        description: 'Select a season, Grand Prix, driver, and lap. This shared context immediately refreshes every panel and prediction.',
        side: 'bottom',
        align: 'center',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="race-state"]',
      popover: {
        title: 'Read the current race state',
        description: 'Monitor lap, position, gaps, speed, telemetry, Safety Car status, and the live tire assigned to the selected driver.',
        side: 'right',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="tire-state"]',
      popover: {
        title: 'Assess tire condition',
        description: 'Tire health combines compound, age, degradation, and temperature proxy. Lower health and rising degradation increase pit pressure.',
        side: 'right',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="weather"]',
      popover: {
        title: 'Track weather and surface conditions',
        description: 'Air temperature, track temperature, humidity, wind, and model rain risk influence tire choice and the expected crossover point.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="ai-strategy"]',
      popover: {
        title: 'Understand the AI pit recommendation',
        description: 'The gauge converts the latest feature sequence into next-lap pit probability, risk level, and an operational instruction.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="pit-timeline"]',
      popover: {
        title: 'Follow probability across the race',
        description: 'The cyan line shows pit probability by lap. The white marker is the selected lap, colored zones are decision thresholds, and yellow dots are recorded stops.',
        side: 'bottom',
        align: 'center',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="strategy-recommendation"]',
      popover: {
        title: 'Compare strategy options',
        description: 'Review the target pit window, recommended next compound, expected time gain, undercut score, projected position, and alternative stop plans.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'dashboard',
    step: {
      element: '[data-tour="simulation-controls"]',
      popover: {
        title: 'Test a quick scenario',
        description: 'Change the next tire, target lap, rain risk, or Safety Car condition and rerun the model without mutating the live race state.',
        side: 'top',
        align: 'center',
      },
    },
  },
  {
    routeName: 'replay',
    step: {
      element: '[data-tour="replay-control"]',
      popover: {
        title: 'Replay the race lap by lap',
        description: 'Use the scrubber and step controls to move through historical laps. All Replay charts stay synchronized with the selected lap.',
        side: 'bottom',
        align: 'center',
      },
    },
  },
  {
    routeName: 'replay',
    step: {
      element: '[data-tour="pit-timeline"]',
      popover: {
        title: 'Review prediction timing',
        description: 'Compare the model probability at each historical lap with the actual recorded pit stops to inspect early, late, or missed warnings.',
        side: 'bottom',
        align: 'center',
      },
    },
  },
  {
    routeName: 'replay',
    step: {
      element: '[data-tour="pace-trend"]',
      popover: {
        title: 'Inspect pace against immediate rivals',
        description: 'Solid lines represent observed sector deltas. Dashed lines extend the short predictive horizon so analysts can spot developing pace loss.',
        side: 'top',
        align: 'center',
      },
    },
  },
  {
    routeName: 'replay',
    step: {
      element: '[data-tour="driver-comparison"]',
      popover: {
        title: 'Compare the field',
        description: 'Rows show position, gap, tire, tire age, pit risk, and estimated stop lap. Selecting a row changes the global focused driver.',
        side: 'top',
        align: 'center',
      },
    },
  },
  {
    routeName: 'simulator',
    step: {
      element: '[data-tour="initial-tire-override"]',
      popover: {
        title: 'Override the simulated starting tire',
        description: 'Enable this only for experiments. The simulator recalculates tire health and compound features while preserving the original live RaceState.',
        side: 'right',
        align: 'start',
      },
    },
  },
  {
    routeName: 'simulator',
    step: {
      element: '[data-tour="simulation-controls"]',
      popover: {
        title: 'Build and run a strategy scenario',
        description: 'Set initial tire assumptions, next compound, target pit lap, weather risk, and Safety Car state, then use Run Simulation to infer a new outcome.',
        side: 'right',
        align: 'start',
      },
    },
  },
  {
    routeName: 'simulator',
    step: {
      element: '[data-tour="ai-strategy"]',
      popover: {
        title: 'Read the simulated pit risk',
        description: 'After simulation, this gauge displays the recalculated probability and action for the modified feature vector, not the untouched live state.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'simulator',
    step: {
      element: '[data-tour="strategy-recommendation"]',
      popover: {
        title: 'Evaluate the projected strategy',
        description: 'Use the recommended compound, expected gain, confidence, and projected finishing position to compare the scenario with the live plan.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'model-analysis',
    step: {
      element: '[data-tour="feature-importance"]',
      popover: {
        title: 'Feature Importance',
        description: 'This ranking estimates which current inputs contribute most to the decision. It explains model sensitivity, but it is not direct proof of causality.',
        side: 'right',
        align: 'start',
      },
    },
  },
  {
    routeName: 'model-analysis',
    step: {
      element: '[data-tour="attention-distribution"]',
      popover: {
        title: 'Temporal Attention Distribution',
        description: 'Each radar axis represents one timestep in the LSTM sequence. Larger weights indicate which recent laps the attention layer emphasized during inference.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'model-analysis',
    step: {
      element: '[data-tour="feature-ledger"]',
      popover: {
        title: 'Normalized Feature Ledger',
        description: 'This ledger exposes the current 40-feature inference vector by group. Values are normalized model inputs, so they may differ from raw engineering units.',
        side: 'top',
        align: 'center',
      },
    },
  },
  {
    routeName: 'model-analysis',
    step: {
      element: '[data-tour="model-health"]',
      popover: {
        title: 'Model and API health',
        description: 'Confirm backend availability, loaded weights, feature count, inference device, sequence length, input dimension, and the latest refresh time.',
        side: 'left',
        align: 'start',
      },
    },
  },
  {
    routeName: 'model-analysis',
    step: {
      element: '[data-tour="tour-replay"]',
      popover: {
        title: 'Tour complete',
        description: 'You can now use Dashboard, Replay, Simulator, and Model Analysis together. Select this help button whenever you need to replay the full guide.',
        side: 'bottom',
        align: 'end',
      },
    },
  },
]

export function useOnboardingTour() {
  const router = useRouter()
  let navigating = false

  async function moveToTourStep(tourDriver: Driver, index: number): Promise<void> {
    if (navigating || index < 0 || index >= tourEntries.length) return

    navigating = true
    const entry = tourEntries[index]

    try {
      if (router.currentRoute.value.name !== entry.routeName) {
        await router.push({ name: entry.routeName })
      }

      await nextTick()
      const targetIsReady = await waitForTourTarget(getTargetSelector(entry))
      if (targetIsReady) tourDriver.moveTo(index)
    } finally {
      navigating = false
    }
  }

  async function startTour(force = false): Promise<void> {
    if (!force && hasSeenTour()) return

    if (router.currentRoute.value.name !== 'dashboard') {
      await router.push({ name: 'dashboard' })
    }

    await nextTick()
    const targetIsReady = await waitForTourTarget(REQUIRED_TOUR_TARGET)
    if (!targetIsReady) return

    activeTour?.destroy()

    const tour = driver({
      steps: tourEntries.map((entry) => entry.step),
      animate: true,
      smoothScroll: true,
      allowClose: true,
      allowKeyboardControl: true,
      overlayColor: '#020406',
      overlayOpacity: 0.78,
      overlayClickBehavior: 'close',
      stagePadding: 8,
      stageRadius: 7,
      popoverOffset: 14,
      popoverClass: 'f1-driver-popover',
      disableActiveInteraction: true,
      showProgress: true,
      progressText: 'Step {{current}} of {{total}}',
      showButtons: ['close', 'previous', 'next'],
      prevBtnText: 'Back',
      nextBtnText: 'Next',
      doneBtnText: 'Finish',
      onPopoverRender(popover) {
        popover.closeButton.textContent = 'Skip'
        popover.closeButton.setAttribute('aria-label', 'Skip onboarding tour')
        popover.closeButton.title = 'Skip onboarding tour'
        popover.footerButtons.prepend(popover.closeButton)
      },
      async onNextClick(_element, _step, { driver: tourDriver }) {
        if (tourDriver.isLastStep()) {
          markTourAsSeen()
          tourDriver.destroy()
          return
        }

        await moveToTourStep(tourDriver, (tourDriver.getActiveIndex() ?? 0) + 1)
      },
      async onPrevClick(_element, _step, { driver: tourDriver }) {
        await moveToTourStep(tourDriver, (tourDriver.getActiveIndex() ?? 0) - 1)
      },
      onCloseClick(_element, _step, { driver: tourDriver }) {
        markTourAsSeen()
        tourDriver.destroy()
      },
      onDestroyed() {
        markTourAsSeen()
        activeTour = null
      },
    })

    activeTour = tour
    tour.drive()
  }

  return {
    hasSeenTour,
    startTour,
    startTourIfNeeded: () => startTour(false),
  }
}

import { useOverlay } from './useOverlay'
import { usePlayerStore } from '../stores/player'
import { useRadioStation } from './useRadioStation'
import { useRadioArcadePage } from './useRadioArcadePage'

export function useGamesPage() {
  const playerStore = usePlayerStore()
  const { closeNowPlaying } = useOverlay()

  const {
    currentTrack: stationCurrent,
    isRadioContext,
    isRadioAudible,
    toggleRadioAudio,
  } = useRadioStation(playerStore)

  const arcadePage = useRadioArcadePage({
    playerStore,
    stationCurrent,
    isRadioContext,
    isRadioAudible,
    syncLivePlayback: () => {},
    toggleRadioAudio,
    closeNowPlaying,
    haptics: { light: () => {}, medium: () => {} },
  })

  return {
    stationCurrent,
    isRadioContext,
    isRadioAudible,
    ...arcadePage,
  }
}

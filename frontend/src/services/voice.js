/**
 * ElevenLabs Voice AI Service
 * Uses backend API to generate Rachel voice narration
 * Silently skips if backend fails (no broken browser TTS fallback)
 */

import api from './api'

const BACKEND_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class VoiceService {
  constructor() {
    this.isSpeaking = false
    this.currentAudio = null
  }

  /**
   * Speak text using backend ElevenLabs API
   */
  async speak(text, options = {}) {
    if (!text || !text.trim()) return
    if (this.isSpeaking) return

    this.isSpeaking = true

    try {
      await this._speakWithBackendAPI(text, options)
    } catch (error) {
      // Silently fail — ElevenLabs unavailable or no Hindi TTS on system
      console.warn('[VoiceService] Voice unavailable:', error.message)
    } finally {
      this.isSpeaking = false
    }
  }

  /**
   * Speak using backend ElevenLabs API
   */
  async _speakWithBackendAPI(text, options = {}) {
    // Call backend to generate audio
    const response = await api.post('/voice/narrate', { text })

    if (!response.data.audio_url) {
      throw new Error('No audio URL in response')
    }

    // ✅ Fix: prepend backend base URL so Audio() hits FastAPI, not Vite
    const audioUrl = `${BACKEND_BASE}${response.data.audio_url}`

    const audio = new Audio(audioUrl)
    audio.volume = options.volume || 1.0

    // Wait for audio to load
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        cleanup()
        reject(new Error('Audio loading timeout'))
      }, 10000)

      const cleanup = () => {
        clearTimeout(timeout)
        audio.removeEventListener('canplay', onCanPlay)
        audio.removeEventListener('error', onError)
      }

      const onCanPlay = () => { cleanup(); resolve() }
      const onError = () => { cleanup(); reject(new Error('Audio failed to load')) }

      audio.addEventListener('canplay', onCanPlay, { once: true })
      audio.addEventListener('error', onError, { once: true })
      audio.load()
    })

    this.currentAudio = audio
    await audio.play()
  }

  /**
   * Stop current speech
   */
  stop() {
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.currentAudio = null
    }
    this.isSpeaking = false
  }

  /**
   * Narrate dashboard results
   */
  async narrateDashboard(data, type = 'seller') {
    if (!data) return

    if (type === 'seller') {
      const earnings = data.allocation_earnings_estimate_inr?.toFixed(2) || '0.00'
      await this.speak(`आपने आज सौर ऊर्जा से ${earnings} रुपये कमाए।`)
    } else {
      const savings = data.allocation_savings_estimate_inr?.toFixed(2) || '0.00'
      await this.speak(`आपने आज पूल से ${savings} रुपये की बचत की।`)
    }
  }

  /**
   * Narrate demand allocation result
   */
  async narrateAllocation(result) {
    if (!result) return

    const status = result.allocation_status || result.status
    if (!['matched', 'partial', 'success'].includes(status)) return

    const kwh = result.allocated_kwh || result.allocated_energy || result.demand_kwh || 0
    if (kwh > 0) {
      const savings = ((kwh * 12) - (kwh * 9)).toFixed(2)
      await this.speak(`बिल स्वीकृत। आपने पूल से खरीदकर ${savings} रुपये की बचत की।`)
    }
  }

  /**
   * Narrate bill summary
   */
  async narrateBill(bill) {
    if (!bill) return

    let text
    if (bill.net_payable < 0) {
      const credit = Math.abs(bill.net_payable).toFixed(2)
      text = `आपके खाते में ${credit} रुपये की वापसी है।`
    } else {
      const earned = (bill.solar_export_credit + bill.pool_sale_credit).toFixed(2)
      text = `सौर ऊर्जा से आपने ${earned} रुपये कमाए।`
    }

    await this.speak(text)
  }
}

export default new VoiceService()
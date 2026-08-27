// Centralized Registry for Offline Safety Voice Recordings

export const OFFLINE_AUDIO_ASSETS: Record<string, Record<string, any>> = {
  Default: {
    'default': require('../../assets/audio/custom_call.ogg'),
  },
};

export const getOfflineAudioSource = (voiceGender: string, languageCode: string) => {
  return OFFLINE_AUDIO_ASSETS.Default.default;
};

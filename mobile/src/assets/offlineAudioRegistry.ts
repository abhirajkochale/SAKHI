// Centralized Registry for 6 Bundled Offline Safety Voice Recordings

export const OFFLINE_AUDIO_ASSETS: Record<string, Record<string, any>> = {
  Male: {
    'en-IN': require('../../assets/audio/male_en.wav'),
    'hi-IN': require('../../assets/audio/male_hi.wav'),
    'mr-IN': require('../../assets/audio/male_mr.wav'),
  },
  Female: {
    'en-IN': require('../../assets/audio/female_en.wav'),
    'hi-IN': require('../../assets/audio/female_hi.wav'),
    'mr-IN': require('../../assets/audio/female_mr.wav'),
  },
};

export const getOfflineAudioSource = (voiceGender: string, languageCode: string) => {
  const genderKey = voiceGender === 'Female' ? 'Female' : 'Male';
  const langKey = OFFLINE_AUDIO_ASSETS[genderKey][languageCode] ? languageCode : 'en-IN';
  return OFFLINE_AUDIO_ASSETS[genderKey][langKey];
};

import React, { useState, useRef, useEffect } from 'react';
import { Modal, View, TouchableOpacity, StyleSheet, ActivityIndicator, Dimensions, Linking, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiCard } from './ui/SakhiCard';
import { createAudioPlayer, setAudioModeAsync, AudioPlayer } from 'expo-audio';
import { sakhiApi, CallFriendSettings } from '../api/sakhiApi';
import CallFriendSetupModal from './CallFriendSetupModal';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { getOfflineAudioSource } from '../assets/offlineAudioRegistry';
import AmenitySearch from './AmenitySearch';

const { width } = Dimensions.get('window');

interface Props {
  visible: boolean;
  onClose: () => void;
  initialCategory?: string | null;
}

// Synthesize a 2-second dual-tone phone ringtone PCM WAV (440Hz + 480Hz tone)
const generateRingtoneWavBase64 = (): string => {
  const sampleRate = 8000;
  const durationSec = 2.0;
  const numSamples = Math.floor(sampleRate * durationSec);
  const dataSize = numSamples * 2;
  const buffer = new Uint8Array(44 + dataSize);

  // RIFF header
  buffer.set([0x52, 0x49, 0x46, 0x46], 0);
  const fileSize = 36 + dataSize;
  buffer[4] = fileSize & 0xff;
  buffer[5] = (fileSize >> 8) & 0xff;
  buffer[6] = (fileSize >> 16) & 0xff;
  buffer[7] = (fileSize >> 24) & 0xff;
  buffer.set([0x57, 0x41, 0x56, 0x45], 8);
  buffer.set([0x66, 0x6d, 0x74, 0x20], 12);
  buffer[16] = 16; buffer[17] = 0; buffer[18] = 0; buffer[19] = 0;
  buffer[20] = 1; buffer[21] = 0;
  buffer[22] = 1; buffer[23] = 0;
  buffer[24] = sampleRate & 0xff;
  buffer[25] = (sampleRate >> 8) & 0xff;
  buffer[26] = (sampleRate >> 16) & 0xff;
  buffer[27] = (sampleRate >> 24) & 0xff;
  const byteRate = sampleRate * 2;
  buffer[28] = byteRate & 0xff;
  buffer[29] = (byteRate >> 8) & 0xff;
  buffer[30] = (byteRate >> 16) & 0xff;
  buffer[31] = (byteRate >> 24) & 0xff;
  buffer[32] = 2; buffer[33] = 0;
  buffer[34] = 16; buffer[35] = 0;
  buffer.set([0x64, 0x61, 0x74, 0x61], 36);
  buffer[40] = dataSize & 0xff;
  buffer[41] = (dataSize >> 8) & 0xff;
  buffer[42] = (dataSize >> 16) & 0xff;
  buffer[43] = (dataSize >> 24) & 0xff;

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    let sample = 0;
    if (t < 1.2) {
      const val1 = Math.sin(2 * Math.PI * 440 * t);
      const val2 = Math.sin(2 * Math.PI * 480 * t);
      sample = Math.floor(((val1 + val2) / 2) * 12000);
    }
    const idx = 44 + i * 2;
    buffer[idx] = sample & 0xff;
    buffer[idx + 1] = (sample >> 8) & 0xff;
  }

  let binary = '';
  const len = buffer.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(buffer[i]);
  }
  return btoa(binary);
};

export default function QuickFindModal({ visible, onClose, initialCategory }: Props) {
  const networkStatus = useNetworkStatus();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [resultCoords, setResultCoords] = useState<{lat: number, lon: number} | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Call a Friend state
  const [savedSettings, setSavedSettings] = useState<CallFriendSettings | null>(null);
  const [checkingSettings, setCheckingSettings] = useState(false);
  const [showSetupNeeded, setShowSetupNeeded] = useState(false);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [showModeSelection, setShowModeSelection] = useState(false);
  const [callMode, setCallMode] = useState<'online' | 'offline'>('online');

  const [isIncomingCall, setIsIncomingCall] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [callElapsedSeconds, setCallElapsedSeconds] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  
  // Call Controls
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaker, setIsSpeaker] = useState(true);

  const ringtonePlayerRef = useRef<AudioPlayer | null>(null);
  const ttsPlayerRef = useRef<AudioPlayer | null>(null);

  // Auto select mode based on network availability
  useEffect(() => {
    if (!networkStatus.isOnline) {
      setCallMode('offline');
    }
  }, [networkStatus.isOnline]);

  useEffect(() => {
    if (visible && initialCategory) {
      if (initialCategory === 'Call a Friend') {
        handleCallFriendTrigger();
      } else if (!selectedCategory) {
        handleSearch(initialCategory);
      }
    }
  }, [visible, initialCategory]);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (callActive) {
      interval = setInterval(() => {
        setCallElapsedSeconds(prev => {
          const next = prev + 1;
          const targetSeconds = (savedSettings?.duration_minutes || 2) * 60;
          if (next >= targetSeconds) {
            reset();
            return 0;
          }
          return next;
        });
      }, 1000);
    } else {
      setCallElapsedSeconds(0);
    }
    return () => clearInterval(interval);
  }, [callActive, savedSettings]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const stopAudioPlayers = () => {
    if (ringtonePlayerRef.current) {
      try {
        ringtonePlayerRef.current.pause();
        ringtonePlayerRef.current.remove();
      } catch (e) {}
      ringtonePlayerRef.current = null;
    }
    if (ttsPlayerRef.current) {
      try {
        ttsPlayerRef.current.pause();
        ttsPlayerRef.current.remove();
      } catch (e) {}
      ttsPlayerRef.current = null;
    }
  };

  const handleCallFriendTrigger = async () => {
    setCheckingSettings(true);
    setShowSetupNeeded(false);
    setShowModeSelection(false);

    try {
      // If offline, use fallback cached settings if available
      let settings: CallFriendSettings | null = null;
      if (networkStatus.isOnline) {
        settings = await sakhiApi.getCallFriendSettings();
      } else if (savedSettings) {
        settings = savedSettings;
      } else {
        // Create default offline fallback settings if none exist
        settings = {
          caller_name: 'Bro',
          language_code: 'en-IN',
          voice_gender: 'Female',
          script: 'Pre-recorded offline safety call.',
          duration_minutes: 2
        };
      }

      if (!settings && networkStatus.isOnline) {
        setShowSetupNeeded(true);
      } else {
        setSavedSettings(settings);
        setCallMode(networkStatus.isOnline ? 'online' : 'offline');
        setShowModeSelection(true);
      }
    } catch (err: any) {
      console.log('Online settings fetch failed, falling back to default/offline:', err);
      const fallbackSettings: CallFriendSettings = savedSettings || {
        caller_name: 'Bro',
        language_code: 'en-IN',
        voice_gender: 'Female',
        script: 'Pre-recorded offline safety call.',
        duration_minutes: 2
      };
      setSavedSettings(fallbackSettings);
      setCallMode('offline');
      setShowModeSelection(true);
    } finally {
      setCheckingSettings(false);
    }
  };

  const startCallFromModeSelection = () => {
    if (!savedSettings) return;
    setShowModeSelection(false);
    startIncomingCall(savedSettings);
  };

  const startIncomingCall = async (settings: CallFriendSettings) => {
    stopAudioPlayers();
    setIsIncomingCall(true);
    setCallActive(false);

    try {
      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
      });

      const ringtoneUri = `data:audio/wav;base64,${generateRingtoneWavBase64()}`;
      const ringtonePlayer = createAudioPlayer({ uri: ringtoneUri });
      ringtonePlayerRef.current = ringtonePlayer;
      ringtonePlayer.play();
    } catch (e) {
      console.log('Ringtone playback error:', e);
    }
  };

  const handleAcceptCall = async () => {
    stopAudioPlayers();
    setIsIncomingCall(false);
    setCallActive(true);
    setIsSpeaker(true);

    if (savedSettings) {
      if (callMode === 'online' && networkStatus.isOnline) {
        await playSarvamAudioForScript(savedSettings);
      } else {
        await playOfflineBundledAudio(savedSettings);
      }
    }
  };

  const playOfflineBundledAudio = async (settings: CallFriendSettings) => {
    setIsPlayingAudio(true);
    try {
      const audioAsset = getOfflineAudioSource(settings.voice_gender, settings.language_code);
      const player = createAudioPlayer(audioAsset);
      ttsPlayerRef.current = player;
      player.play();
    } catch (err: any) {
      console.error('Offline audio playback failed:', err);
    } finally {
      setIsPlayingAudio(false);
    }
  };

  const playSarvamAudioForScript = async (settings: CallFriendSettings) => {
    setIsPlayingAudio(true);
    try {
      const ttsData = await sakhiApi.generateCallFriendTts(
        settings.script,
        settings.language_code,
        undefined,
        settings.source_language_code,
        settings.voice_gender
      );

      if (ttsData?.audio_base64) {
        const audioUri = `data:audio/wav;base64,${ttsData.audio_base64}`;
        const player = createAudioPlayer({ uri: audioUri });
        ttsPlayerRef.current = player;
        player.play();
      }
    } catch (err: any) {
      console.error('Sarvam TTS online call generation failed, switching to offline fallback:', err);
      // Seamless offline fallback if online TTS fails
      await playOfflineBundledAudio(settings);
    } finally {
      setIsPlayingAudio(false);
    }
  };

  const toggleMute = () => {
    if (ttsPlayerRef.current) {
      if (isMuted) {
        ttsPlayerRef.current.volume = 1.0;
        setIsMuted(false);
      } else {
        ttsPlayerRef.current.volume = 0.0;
        setIsMuted(true);
      }
    } else {
      setIsMuted(!isMuted);
    }
  };

  const toggleSpeaker = async () => {
    setIsSpeaker(!isSpeaker);
    try {
      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
      });
    } catch (e) {}
  };

  const handleSearch = async (categoryName: string) => {
    setSelectedCategory(categoryName);
  };

  const handleNavigateNow = () => {
    if (resultCoords) {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${resultCoords.lat},${resultCoords.lon}`;
      Linking.openURL(url);
    }
    reset();
  };

  const reset = () => {
    stopAudioPlayers();
    setLoading(false);
    setSelectedCategory(null);
    setShowSetupNeeded(false);
    setShowModeSelection(false);
    setIsIncomingCall(false);
    setCallActive(false);
    setIsPlayingAudio(false);
    onClose();
  };

  const renderOptions = () => (
    <View style={styles.optionsContainer}>
      <TouchableOpacity style={styles.optionCard} onPress={() => handleSearch('Washroom')}>
        <View style={styles.iconContainer}>
          <Ionicons name="water-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3" style={{ color: '#1F2937' }}>Find Washroom</SakhiText>
          <SakhiText variant="subtext" color="secondary">Locate nearby clean & safe restrooms</SakhiText>
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={styles.optionCard} onPress={() => handleSearch('Medical Clinic')}>
        <View style={styles.iconContainer}>
          <Ionicons name="medkit-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3" style={{ color: '#1F2937' }}>Find Medical Clinic</SakhiText>
          <SakhiText variant="subtext" color="secondary">Locate 24/7 clinics and emergency care</SakhiText>
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={styles.optionCard} onPress={handleCallFriendTrigger}>
        <View style={styles.iconContainer}>
          <Ionicons name="call-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3" style={{ color: '#1F2937' }}>Call a Friend</SakhiText>
          <SakhiText variant="subtext" color="secondary">Simulate a real incoming call with AI voice</SakhiText>
        </View>
      </TouchableOpacity>
    </View>
  );

  const renderSetupNeeded = () => (
    <View style={styles.setupNeededContainer}>
      <View style={styles.setupIconWrapper}>
        <Ionicons name="settings-outline" size={36} color="#DC2626" />
      </View>
      <SakhiText variant="h2" style={styles.setupTitle}>Pre-Journey Setup Required</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.setupDesc}>
        You haven't configured your Call a Friend settings yet. Set your caller name, language, voice, script, and duration before starting your journey.
      </SakhiText>

      <SakhiButton
        title="Configure Setup Now"
        onPress={() => {
          setShowSetupNeeded(false);
          setShowSetupModal(true);
        }}
        style={{ width: '100%' }}
      />
    </View>
  );

  const renderModeSelection = () => (
    <View style={styles.setupNeededContainer}>
      <View style={[styles.setupIconWrapper, { backgroundColor: callMode === 'online' ? '#EFF6FF' : '#FEF2F2' }]}>
        <Ionicons name={callMode === 'online' ? "wifi-outline" : "cloud-offline-outline"} size={36} color={callMode === 'online' ? "#2563EB" : "#DC2626"} />
      </View>
      
      <SakhiText variant="h2" style={styles.setupTitle}>Call a Friend Safety Mode</SakhiText>
      
      {/* Network Status Indicator Badge */}
      <View style={[styles.networkBadge, { backgroundColor: networkStatus.isOnline ? '#ECFDF5' : '#FEF2F2', borderColor: networkStatus.isOnline ? '#6EE7B7' : '#FCA5A5' }]}>
        <View style={[styles.networkDot, { backgroundColor: networkStatus.isOnline ? '#10B981' : '#EF4444' }]} />
        <SakhiText variant="subtext" style={{ color: networkStatus.isOnline ? '#065F46' : '#991B1B', fontWeight: 'bold' }}>
          {networkStatus.isOnline ? "Internet Available" : "No Internet Connection - Offline Mode Selected"}
        </SakhiText>
      </View>

      {/* Mode Selection Buttons */}
      <View style={styles.modeRow}>
        <TouchableOpacity
          style={[
            styles.modeBtn,
            callMode === 'online' && styles.modeBtnActiveOnline,
            !networkStatus.isOnline && styles.modeBtnDisabled
          ]}
          disabled={!networkStatus.isOnline}
          onPress={() => setCallMode('online')}
        >
          <Ionicons name="sparkles" size={20} color={!networkStatus.isOnline ? "#9CA3AF" : callMode === 'online' ? "#2563EB" : "#4B5563"} />
          <SakhiText variant="body" style={[styles.modeBtnText, callMode === 'online' && styles.modeBtnTextActiveOnline, !networkStatus.isOnline && { color: "#9CA3AF" }]}>
            Online Sarvam AI
          </SakhiText>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.modeBtn,
            callMode === 'offline' && styles.modeBtnActiveOffline
          ]}
          onPress={() => setCallMode('offline')}
        >
          <Ionicons name="shield-checkmark" size={20} color={callMode === 'offline' ? "#DC2626" : "#4B5563"} />
          <SakhiText variant="body" style={[styles.modeBtnText, callMode === 'offline' && styles.modeBtnTextActiveOffline]}>
            Offline Bundled
          </SakhiText>
        </TouchableOpacity>
      </View>

      {/* Configuration Summary Card */}
      <View style={styles.summaryCard}>
        <SakhiText variant="subtext" style={styles.summaryHeader}>Configured Profile:</SakhiText>
        <View style={styles.summaryRow}>
          <SakhiText variant="caption" color="secondary">Caller: <SakhiText variant="body" style={{fontWeight:'bold'}}>{savedSettings?.caller_name}</SakhiText></SakhiText>
          <SakhiText variant="caption" color="secondary">Voice: <SakhiText variant="body" style={{fontWeight:'bold'}}>{savedSettings?.voice_gender}</SakhiText></SakhiText>
        </View>
        <View style={styles.summaryRow}>
          <SakhiText variant="caption" color="secondary">
            Lang: <SakhiText variant="body" style={{fontWeight:'bold'}}>{savedSettings?.language_code === 'en-IN' ? 'English' : savedSettings?.language_code === 'hi-IN' ? 'Hindi' : 'Marathi'}</SakhiText>
          </SakhiText>
          <SakhiText variant="caption" color="secondary">Duration: <SakhiText variant="body" style={{fontWeight:'bold'}}>{savedSettings?.duration_minutes} min</SakhiText></SakhiText>
        </View>
        {callMode === 'offline' && (
          <SakhiText variant="subtext" style={{ color: '#DC2626', marginTop: 4, fontStyle: 'italic' }}>
            * Uses pre-recorded bundled safety voice recording (100% offline).
          </SakhiText>
        )}
      </View>

      <SakhiButton
        title="Start Call Now"
        onPress={startCallFromModeSelection}
        style={{ width: '100%', marginTop: 8 }}
      />
    </View>
  );

  const renderIncomingCall = () => (
    <View style={styles.incomingCallContainer}>
      <View style={styles.pulseAvatar}>
        <Ionicons name="person" size={48} color="#DC2626" />
      </View>
      <SakhiText variant="h1" style={styles.callerTitle}>{savedSettings?.caller_name || 'Bro'}</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callingSubtitle}>Incoming Safety Call...</SakhiText>

      <View style={styles.callActionRow}>
        <TouchableOpacity style={styles.declineBtn} onPress={reset}>
          <Ionicons name="call" size={28} color="#FFFFFF" style={styles.declineIcon} />
        </TouchableOpacity>

        <TouchableOpacity style={styles.acceptBtn} onPress={handleAcceptCall}>
          <Ionicons name="call" size={28} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
      <View style={styles.actionTextRow}>
        <SakhiText variant="caption" color="secondary">Decline</SakhiText>
        <SakhiText variant="caption" color="secondary">Accept</SakhiText>
      </View>
    </View>
  );

  const renderActiveCall = () => (
    <View style={styles.activeCallContainer}>
      <View style={styles.callAvatar}>
        <Ionicons name="person" size={38} color="#4B5563" />
      </View>
      <SakhiText variant="h2" style={styles.callerName}>{savedSettings?.caller_name || 'Bro'}</SakhiText>
      <SakhiText variant="h3" style={styles.callTimer}>{formatTime(callElapsedSeconds)}</SakhiText>
      <SakhiText variant="subtext" color="secondary" style={styles.callSubtitle}>
        {callMode === 'online' ? 'Sarvam AI Voice Connected' : 'Offline Safety Voice Connected'}
      </SakhiText>

      <View style={styles.controlsRow}>
        <TouchableOpacity style={[styles.controlBtn, isMuted && styles.controlBtnActive]} onPress={toggleMute}>
          <Ionicons name={isMuted ? "mic-off" : "mic"} size={22} color={isMuted ? "#DC2626" : "#374151"} />
          <SakhiText variant="caption" style={{ marginTop: 4, color: isMuted ? "#DC2626" : "#374151" }}>
            {isMuted ? "Muted" : "Mute"}
          </SakhiText>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.controlBtn, isSpeaker && styles.controlBtnActive]} onPress={toggleSpeaker}>
          <Ionicons name={isSpeaker ? "volume-high" : "volume-medium"} size={22} color={isSpeaker ? "#DC2626" : "#374151"} />
          <SakhiText variant="caption" style={{ marginTop: 4, color: isSpeaker ? "#DC2626" : "#374151" }}>
            {isSpeaker ? "Speaker" : "Earpiece"}
          </SakhiText>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.endCallBtn} onPress={reset}>
        <Ionicons name="call" size={26} color="#FFFFFF" style={styles.endCallIcon} />
      </TouchableOpacity>
      <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>End Call</SakhiText>
    </View>
  );

  const renderResult = () => (
    <View style={{ flex: 1 }}>
      <AmenitySearch 
        category={selectedCategory!}
        onNavigate={(destCoords, originCoords) => {
          let url = `https://www.google.com/maps/dir/?api=1&origin=${originCoords.latitude},${originCoords.longitude}&destination=${destCoords.latitude},${destCoords.longitude}&travelmode=walking`;
          Linking.openURL(url);
          reset();
        }}
      />
    </View>
  );

  return (
    <>
      <Modal visible={visible} animationType="slide" transparent={true}>
        <View style={styles.overlay}>
          <View style={[styles.modalView, selectedCategory ? styles.modalViewFullScreen : null]}>
            <View style={styles.header}>
              <SakhiText variant="h2" style={styles.headerTitle}>
                {selectedCategory ? selectedCategory : 'Quick Assistance'}
              </SakhiText>
              <TouchableOpacity onPress={reset} style={styles.closeBtnWrapper}>
                <Ionicons name="close" size={24} color="#6B7280" />
              </TouchableOpacity>
            </View>

            {(loading || checkingSettings) && (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#DC2626" />
                <SakhiText variant="body" style={{ marginTop: 12 }}>Checking safety setup...</SakhiText>
              </View>
            )}

            {!loading && !checkingSettings && selectedCategory && renderResult()}
            {!loading && !checkingSettings && !selectedCategory && !showSetupNeeded && !showModeSelection && !isIncomingCall && !callActive && renderOptions()}
            {!loading && !checkingSettings && showSetupNeeded && renderSetupNeeded()}
            {!loading && !checkingSettings && showModeSelection && renderModeSelection()}
            {!loading && !checkingSettings && isIncomingCall && renderIncomingCall()}
            {!loading && !checkingSettings && callActive && renderActiveCall()}
          </View>
        </View>
      </Modal>

      <CallFriendSetupModal
        visible={showSetupModal}
        onClose={() => setShowSetupModal(false)}
        onSaved={handleCallFriendTrigger}
      />
    </>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(17, 24, 39, 0.6)',
    justifyContent: 'flex-end',
  },
  modalView: {
    backgroundColor: '#FFFFFF',
    padding: 24,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    minHeight: width * 0.8,
  },
  modalViewFullScreen: {
    flex: 1,
    marginTop: 40,
    width: '100%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerTitle: {
    color: '#1F2937',
  },
  closeBtnWrapper: {
    padding: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  optionsContainer: {
    gap: 12,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  optionTextContainer: {
    flex: 1,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  setupNeededContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  setupIconWrapper: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  setupTitle: {
    color: '#1F2937',
    marginBottom: 8,
  },
  setupDesc: {
    textAlign: 'center',
    marginBottom: 16,
  },
  networkBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  networkDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  modeRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
    width: '100%',
  },
  modeBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 12,
    backgroundColor: '#F9FAFB',
    gap: 6,
  },
  modeBtnActiveOnline: {
    borderColor: '#2563EB',
    backgroundColor: '#EFF6FF',
  },
  modeBtnActiveOffline: {
    borderColor: '#DC2626',
    backgroundColor: '#FEF2F2',
  },
  modeBtnDisabled: {
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
    opacity: 0.6,
  },
  modeBtnText: {
    color: '#374151',
    fontWeight: '600',
    fontSize: 14,
  },
  modeBtnTextActiveOnline: {
    color: '#2563EB',
  },
  modeBtnTextActiveOffline: {
    color: '#DC2626',
  },
  summaryCard: {
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    padding: 12,
    marginBottom: 16,
    gap: 4,
  },
  summaryHeader: {
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 4,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  incomingCallContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  pulseAvatar: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  callerTitle: {
    color: '#1F2937',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  callingSubtitle: {
    marginBottom: 32,
  },
  callActionRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '80%',
    marginBottom: 8,
  },
  actionTextRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '80%',
  },
  declineBtn: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#EF4444',
    justifyContent: 'center',
    alignItems: 'center',
  },
  declineIcon: {
    transform: [{ rotate: '135deg' }],
  },
  acceptBtn: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#10B981',
    justifyContent: 'center',
    alignItems: 'center',
  },
  activeCallContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  callAvatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  callerName: {
    color: '#1F2937',
    marginBottom: 2,
  },
  callTimer: {
    color: '#DC2626',
    marginVertical: 4,
  },
  callSubtitle: {
    marginBottom: 20,
  },
  controlsRow: {
    flexDirection: 'row',
    gap: 24,
    marginBottom: 24,
  },
  controlBtn: {
    width: 70,
    height: 60,
    borderRadius: 14,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlBtnActive: {
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
    borderWidth: 1,
  },
  endCallBtn: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#DC2626',
    justifyContent: 'center',
    alignItems: 'center',
  },
  endCallIcon: {
    transform: [{ rotate: '135deg' }],
  },
  resultContainer: {
    alignItems: 'center',
  },
  resultIconWrapper: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#FEE2E2',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultCategory: {
    color: '#1F2937',
  },
  resultMockBadge: {
    marginBottom: 16,
  },
  resultCard: {
    width: '100%',
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderColor: '#FCA5A5',
    marginBottom: 20,
  },
  actionBtn: {
    width: '100%',
    marginBottom: 12,
  },
  searchAgainBtn: {
    paddingVertical: 8,
  },
});



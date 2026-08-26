import React, { useState, useRef, useEffect } from 'react';
import { Modal, View, TouchableOpacity, StyleSheet, ActivityIndicator, Dimensions, Linking, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiCard } from './ui/SakhiCard';
import { createAudioPlayer, setAudioModeAsync, AudioPlayer } from 'expo-audio';
import { sakhiApi, CallFriendSettings } from '../api/sakhiApi';
import CallFriendSetupModal from './CallFriendSetupModal';

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
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [resultCoords, setResultCoords] = useState<{lat: number, lon: number} | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Call a Friend state
  const [savedSettings, setSavedSettings] = useState<CallFriendSettings | null>(null);
  const [checkingSettings, setCheckingSettings] = useState(false);
  const [showSetupNeeded, setShowSetupNeeded] = useState(false);
  const [showSetupModal, setShowSetupModal] = useState(false);

  const [isIncomingCall, setIsIncomingCall] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [callElapsedSeconds, setCallElapsedSeconds] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  
  // Call Controls
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaker, setIsSpeaker] = useState(true);

  const ringtonePlayerRef = useRef<AudioPlayer | null>(null);
  const ttsPlayerRef = useRef<AudioPlayer | null>(null);

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
    try {
      const settings = await sakhiApi.getCallFriendSettings();
      if (!settings) {
        setShowSetupNeeded(true);
      } else {
        setSavedSettings(settings);
        startIncomingCall(settings);
      }
    } catch (err: any) {
      console.error('Failed to load call settings:', err);
      Alert.alert('Call Error', 'Could not load your saved Call a Friend configuration.');
    } finally {
      setCheckingSettings(false);
    }
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
      await playSarvamAudioForScript(savedSettings);
    }
  };

  const handleDeclineCall = () => {
    stopAudioPlayers();
    reset();
  };

  const toggleSpeaker = async () => {
    const nextSpeaker = !isSpeaker;
    setIsSpeaker(nextSpeaker);
    try {
      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
      });
    } catch (e) {
      console.log('Speaker toggle error:', e);
    }
  };

  const playSarvamAudioForScript = async (settings: CallFriendSettings) => {
    try {
      setIsPlayingAudio(true);
      const speakerName = settings.speaker || (settings.voice_gender === 'Female' ? 'ratan' : 'shubh');
      
      const ttsData = await sakhiApi.generateCallFriendTts(
        settings.script,
        settings.language_code,
        speakerName
      );

      await setAudioModeAsync({
        playsInSilentMode: true,
        shouldPlayInBackground: true,
      });

      if (ttsPlayerRef.current) {
        ttsPlayerRef.current.pause();
        ttsPlayerRef.current.remove();
        ttsPlayerRef.current = null;
      }

      const audioUri = `data:audio/wav;base64,${ttsData.audio_base64}`;
      const player = createAudioPlayer({ uri: audioUri });
      ttsPlayerRef.current = player;
      player.play();
    } catch (err: any) {
      console.error('TTS playback error:', err);
      Alert.alert('Sarvam AI Audio Error', err.message || 'Failed to play Sarvam AI TTS audio');
    } finally {
      setIsPlayingAudio(false);
    }
  };

  const handleSearch = async (category: string) => {
    setSelectedCategory(category);
    setLoading(true);
    try {
      const typeMap: Record<string, string> = {
        'Washroom': 'washroom',
        'Medical Clinic': 'hospital',
        'Police Station': 'police',
      };
      const amenityType = typeMap[category] || 'washroom';
      
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/amenities/nearest?lat=28.631&lon=77.219&type=${amenityType}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setResult(`Nearest ${category}: ${data.name}\n?? ${data.distance_m}m away | ?? ${Math.ceil(data.distance_m / 80)} min walk`);
        if (data.latitude && data.longitude) {
          setResultCoords({ lat: data.latitude, lon: data.longitude });
        }
      } else {
        setResult(`Nearest ${category}: Data unavailable`);
        setResultCoords(null);
      }
    } catch (e) {
      setResult(`Nearest ${category}: Could not reach server`);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    stopAudioPlayers();
    setResult(null);
    setResultCoords(null);
    setSelectedCategory(null);
    setShowSetupNeeded(false);
    setIsIncomingCall(false);
    setCallActive(false);
    setCallElapsedSeconds(0);
    setIsPlayingAudio(false);
    setIsMuted(false);
    setIsSpeaker(true);
    onClose();
  };

  const handleNavigateNow = async () => {
    if (!resultCoords) {
      Alert.alert('Error', 'Location coordinates are missing. Please try searching again.');
      reset();
      return;
    }
    const originLat = 28.6328;
    const originLon = 77.2197;
    const destLat = resultCoords.lat;
    const destLon = resultCoords.lon;
    
    const url = `https://www.google.com/maps/dir/?api=1&origin=${originLat},${originLon}&destination=${destLat},${destLon}&travelmode=walking`;
    try {
      await Linking.openURL(url);
    } catch (error) {
      Alert.alert('Error', 'Could not open Google Maps. Please ensure it is installed.');
    }
    reset();
  };

  const renderOptions = () => (
    <View style={styles.optionsContainer}>
      <TouchableOpacity style={styles.optionCard} onPress={() => handleSearch('Washroom')}>
        <View style={styles.iconContainer}>
          <Ionicons name="water-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3">Washroom</SakhiText>
          <SakhiText variant="subtext" color="secondary">Find a nearby washroom</SakhiText>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
      </TouchableOpacity>

      <TouchableOpacity style={styles.optionCard} onPress={() => handleSearch('Medical Clinic')}>
        <View style={styles.iconContainer}>
          <Ionicons name="medkit-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3">Medical</SakhiText>
          <SakhiText variant="subtext" color="secondary">Find nearby medical help</SakhiText>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
      </TouchableOpacity>

      <TouchableOpacity style={styles.optionCard} onPress={() => handleSearch('Police Station')}>
        <View style={styles.iconContainer}>
          <Ionicons name="shield-checkmark-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3">Police</SakhiText>
          <SakhiText variant="subtext" color="secondary">Find nearby police assistance</SakhiText>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
      </TouchableOpacity>

      <TouchableOpacity style={styles.optionCard} onPress={handleCallFriendTrigger}>
        <View style={styles.iconContainer}>
          <Ionicons name="call-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3">Call a Friend</SakhiText>
          <SakhiText variant="subtext" color="secondary">Start your saved safety check-in call</SakhiText>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
      </TouchableOpacity>
    </View>
  );

  const renderSetupNeeded = () => (
    <View style={styles.setupNeededContainer}>
      <View style={styles.setupIconWrapper}>
        <Ionicons name="alert-circle-outline" size={48} color="#DC2626" />
      </View>
      <SakhiText variant="h2" style={styles.setupTitle}>Call Setup Required</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.setupDesc}>
        Set up Call a Friend before starting your journey to configure your caller name, language, and script.
      </SakhiText>
      <SakhiButton
        title="Open Call Setup"
        onPress={() => {
          setShowSetupNeeded(false);
          setShowSetupModal(true);
        }}
        style={{ width: '100%', marginTop: 12 }}
      />
    </View>
  );

  const renderIncomingCall = () => (
    <View style={styles.incomingCallContainer}>
      <View style={styles.pulseAvatar}>
        <Ionicons name="person" size={48} color="#DC2626" />
      </View>
      <SakhiText variant="h1" style={styles.callerTitle}>{savedSettings?.caller_name || 'Friend'}</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callingSubtitle}>Incoming safety check-in call...</SakhiText>

      <View style={styles.callActionRow}>
        <TouchableOpacity style={styles.declineBtn} onPress={handleDeclineCall}>
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

  const renderActiveCall = () => {
    const totalMinutes = savedSettings?.duration_minutes || 2;
    return (
      <View style={styles.activeCallContainer}>
        <View style={styles.callAvatar}>
          <Ionicons name="person" size={44} color="#374151" />
        </View>
        <SakhiText variant="h2" style={styles.callerName}>{savedSettings?.caller_name || 'Friend'}</SakhiText>
        <SakhiText variant="h1" style={styles.callTimer}>
          {formatTime(callElapsedSeconds)} / {totalMinutes < 10 ? '0' : ''}{totalMinutes}:00
        </SakhiText>
        <SakhiText variant="subtext" color="secondary" style={styles.callSubtitle}>
          {isPlayingAudio ? "Sarvam AI Speaking..." : "Call Active"}
        </SakhiText>

        <View style={styles.controlsRow}>
          <TouchableOpacity style={[styles.controlBtn, isMuted && styles.controlBtnActive]} onPress={() => setIsMuted(!isMuted)}>
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
  };

  const renderResult = () => (
    <View style={styles.resultContainer}>
      <View style={styles.resultIconWrapper}>
        <Ionicons
          name={selectedCategory === 'Washroom' ? 'water-outline' : selectedCategory === 'Medical Clinic' ? 'medkit-outline' : 'shield-checkmark-outline'}
          size={32}
          color="#DC2626"
        />
      </View>
      <SakhiText variant="h3" style={styles.resultCategory}>Found {selectedCategory}</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.resultMockBadge}>Demo result</SakhiText>

      <SakhiCard style={styles.resultCard}>
        <SakhiText variant="h3" style={{ textAlign: 'center', marginBottom: 12 }}>{result}</SakhiText>
      </SakhiCard>

      <SakhiButton
        title="Navigate Now"
        onPress={handleNavigateNow}
        style={styles.actionBtn}
      />

      <TouchableOpacity style={styles.searchAgainBtn} onPress={reset}>
        <SakhiText variant="body" color="secondary">Search Again</SakhiText>
      </TouchableOpacity>
    </View>
  );

  return (
    <>
      <Modal visible={visible} animationType="slide" transparent={true}>
        <View style={styles.overlay}>
          <View style={styles.modalView}>
            <View style={styles.header}>
              <SakhiText variant="h2" style={styles.headerTitle}>Quick Assistance</SakhiText>
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

            {!loading && !checkingSettings && result && renderResult()}
            {!loading && !checkingSettings && !result && !showSetupNeeded && !isIncomingCall && !callActive && renderOptions()}
            {!loading && !checkingSettings && showSetupNeeded && renderSetupNeeded()}
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
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#FEF2F2',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  setupTitle: {
    color: '#1F2937',
    marginBottom: 8,
  },
  setupDesc: {
    textAlign: 'center',
    marginBottom: 16,
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
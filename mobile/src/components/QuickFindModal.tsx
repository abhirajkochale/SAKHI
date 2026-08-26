import React, { useState, useEffect } from 'react';
import { Modal, View, TouchableOpacity, StyleSheet, ActivityIndicator, Dimensions, Linking, Platform, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiCard } from './ui/SakhiCard';
import { setAudioModeAsync, useAudioPlayer } from 'expo-audio';
import { sakhiApi } from '../api/sakhiApi';

const { width } = Dimensions.get('window');

interface Props {
  visible: boolean;
  onClose: () => void;
  initialCategory?: string | null;
}

export default function QuickFindModal({ visible, onClose, initialCategory }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [resultCoords, setResultCoords] = useState<{lat: number, lon: number} | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  
  const [isSettingUpCall, setIsSettingUpCall] = useState(false);
  const [callLanguage, setCallLanguage] = useState('English');
  const [callDuration, setCallDuration] = useState(2);
  const [callActive, setCallActive] = useState(false);
  const [callElapsedSeconds, setCallElapsedSeconds] = useState(0);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // `expo-audio` is included in the Expo Go runtime used by this project.
  // Starting with no source lets us replace it with the base64 audio returned
  // by the TTS endpoint when the user starts a simulated call.
  const audioPlayer = useAudioPlayer(null);

  useEffect(() => {
    if (visible && initialCategory) {
      if (initialCategory === 'Call a Friend') {
        setIsSettingUpCall(true);
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
          if (next >= callDuration * 60) {
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
  }, [callActive, callDuration]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const playSarvamAudio = async () => {
    try {
      setIsPlayingAudio(true);
      const langCode = callLanguage === 'Hindi' ? 'hi-IN' : 'en-IN';
      const sampleText = callLanguage === 'Hindi'
        ? "??????, ?? ???? ???? ??? ?? ?? ????? ?? ??? ???? ?? ??? ?? ?? ???? ?? ???????? ????? ?? ????"
        : "Hey, where are you? I just wanted to check if you've reached safely.";

      const ttsData = await sakhiApi.generateCallFriendTts(sampleText, langCode, 'shubh');

      await setAudioModeAsync({
        playsInSilentMode: true,
        interruptionMode: 'duckOthers',
      });

      audioPlayer.replace({ uri: `data:audio/wav;base64,${ttsData.audio_base64}` });
      audioPlayer.play();
    } catch (err: any) {
      console.error('TTS playback error:', err);
      Alert.alert('Sarvam AI Audio Error', err.message || 'Failed to play Sarvam AI TTS audio');
    } finally {
      setIsPlayingAudio(false);
    }
  };

  const handleStartCall = async () => {
    setIsSettingUpCall(false);
    setCallActive(true);
    await playSarvamAudio();
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
    audioPlayer.pause();
    audioPlayer.replace(null);
    setResult(null);
    setResultCoords(null);
    setSelectedCategory(null);
    setIsSettingUpCall(false);
    setCallActive(false);
    setCallElapsedSeconds(0);
    setIsPlayingAudio(false);
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

      <TouchableOpacity style={styles.optionCard} onPress={() => setIsSettingUpCall(true)}>
        <View style={styles.iconContainer}>
          <Ionicons name="call-outline" size={24} color="#DC2626" />
        </View>
        <View style={styles.optionTextContainer}>
          <SakhiText variant="h3">Call a Friend</SakhiText>
          <SakhiText variant="subtext" color="secondary">Create a simulated call</SakhiText>
        </View>
        <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
      </TouchableOpacity>
    </View>
  );

  const renderCallSetup = () => (
    <View style={styles.callSetupContainer}>
      <SakhiText variant="h2" style={styles.callSetupTitle}>Call a Friend</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callSetupDesc}>Plays Sarvam AI Bulbul V3 voice note to simulate a realistic check-in call.</SakhiText>

      <SakhiText variant="h3" style={styles.label}>Select Language:</SakhiText>
      <View style={styles.row}>
        {['English', 'Hindi'].map((lang) => (
          <TouchableOpacity key={lang} style={[styles.toggleBtn, callLanguage === lang && styles.toggleBtnActive]} onPress={() => setCallLanguage(lang)}>
            <SakhiText variant="body" style={[styles.toggleBtnText, callLanguage === lang && styles.toggleBtnTextActive]}>{lang}</SakhiText>
          </TouchableOpacity>
        ))}
      </View>

      <SakhiText variant="h3" style={styles.label}>Select Duration:</SakhiText>
      <View style={styles.row}>
        {[2, 5, 10].map((mins) => (
          <TouchableOpacity key={mins} style={[styles.toggleBtn, callDuration === mins && styles.toggleBtnActive]} onPress={() => setCallDuration(mins)}>
            <SakhiText variant="body" style={[styles.toggleBtnText, callDuration === mins && styles.toggleBtnTextActive]}>{mins} min</SakhiText>
          </TouchableOpacity>
        ))}
      </View>

      <SakhiButton
        title={isPlayingAudio ? "Generating Voice..." : "Start Call"}
        onPress={handleStartCall}
        style={styles.startCallBtn}
        disabled={isPlayingAudio}
        loading={isPlayingAudio}
      />
    </View>
  );

  const renderActiveCall = () => (
    <View style={styles.activeCallContainer}>
      <View style={styles.callAvatar}>
        <Ionicons name="person" size={40} color="#9CA3AF" />
      </View>
      <SakhiText variant="h2" style={styles.callerName}>Sarvam AI Voice Assistant</SakhiText>
      <SakhiText variant="h1" style={styles.callStatus}>{formatTime(callElapsedSeconds)} / {callDuration < 10 ? '0' : ''}{callDuration}:00</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callSubtitle}>
        {isPlayingAudio ? "Generating Sarvam AI Bulbul V3 Speech..." : `Playing ${callLanguage} Sarvam AI audio...`}
      </SakhiText>

      <TouchableOpacity style={styles.endCallBtn} onPress={reset}>
        <Ionicons name="call" size={24} color="#FFFFFF" style={styles.endCallIcon} />
      </TouchableOpacity>
      <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>End Call</SakhiText>
    </View>
  );

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
    <Modal visible={visible} animationType="slide" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <SakhiText variant="h2" style={styles.headerTitle}>Quick Assistance</SakhiText>
            <TouchableOpacity onPress={reset} style={styles.closeBtnWrapper}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#DC2626" />
              <SakhiText variant="body" style={{ marginTop: 12 }}>Searching nearby safety amenities...</SakhiText>
            </View>
          )}

          {!loading && result && renderResult()}
          {!loading && !result && !isSettingUpCall && !callActive && renderOptions()}
          {!loading && isSettingUpCall && renderCallSetup()}
          {!loading && callActive && renderActiveCall()}
        </View>
      </View>
    </Modal>
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
  callSetupContainer: {
    gap: 16,
  },
  callSetupTitle: {
    color: '#1F2937',
  },
  callSetupDesc: {
    marginBottom: 8,
  },
  label: {
    marginTop: 4,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 12,
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  toggleBtnActive: {
    borderColor: '#DC2626',
    backgroundColor: '#FEF2F2',
  },
  toggleBtnText: {
    color: '#374151',
  },
  toggleBtnTextActive: {
    color: '#DC2626',
    fontWeight: 'bold',
  },
  startCallBtn: {
    marginTop: 12,
  },
  activeCallContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  callAvatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  callerName: {
    color: '#1F2937',
    marginBottom: 4,
  },
  callStatus: {
    color: '#DC2626',
    marginVertical: 8,
  },
  callSubtitle: {
    marginBottom: 24,
  },
  endCallBtn: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#DC2626',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 4,
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  endCallIcon: {
    transform: [{ rotate: '135deg' }],
  },
});

import React, { useState } from 'react';
import { Modal, View, TouchableOpacity, StyleSheet, ActivityIndicator, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiCard } from './ui/SakhiCard';

const { width } = Dimensions.get('window');

interface Props {
  visible: boolean;
  onClose: () => void;
  initialCategory?: string | null;
}

export default function QuickFindModal({ visible, onClose, initialCategory }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const [isSettingUpCall, setIsSettingUpCall] = useState(false);
  const [callLanguage, setCallLanguage] = useState('English');
  const [callDuration, setCallDuration] = useState(2);
  const [callActive, setCallActive] = useState(false);

  React.useEffect(() => {
    if (visible && initialCategory && !selectedCategory) {
      handleSearch(initialCategory);
    }
  }, [visible, initialCategory]);

  const handleSearch = (category: string) => {
    setSelectedCategory(category);
    setLoading(true);
    // Simulate network delay to find nearest amenity
    setTimeout(() => {
      setLoading(false);
      setResult(`Nearest ${category}: 280m | 🚶 4 min walk`);
    }, 1500);
  };

  const reset = () => {
    setResult(null);
    setSelectedCategory(null);
    setIsSettingUpCall(false);
    setCallActive(false);
    onClose();
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
      <SakhiText variant="h2" style={styles.callSetupTitle}>Fake "Call a Friend"</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callSetupDesc}>Plays a voice note to make it seem like you are on a call.</SakhiText>
      
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
        title="Start Fake Call" 
        onPress={() => { setIsSettingUpCall(false); setCallActive(true); }}
        style={styles.startCallBtn}
      />
    </View>
  );

  const renderActiveCall = () => (
    <View style={styles.activeCallContainer}>
      <View style={styles.callAvatar}>
        <Ionicons name="person" size={40} color="#9CA3AF" />
      </View>
      <SakhiText variant="h2" style={styles.callerName}>Unknown Caller</SakhiText>
      <SakhiText variant="h1" style={styles.callStatus}>00:14 / {callDuration}:00</SakhiText>
      <SakhiText variant="body" color="secondary" style={styles.callSubtitle}>Playing {callLanguage} voice notes...</SakhiText>
      
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
        onPress={reset} 
        style={styles.navigateBtn}
      />
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <View>
              <SakhiText variant="h2" style={styles.title}>Quick Find</SakhiText>
              {!result && !isSettingUpCall && !callActive && (
                <SakhiText variant="body" color="secondary">Find useful help near you.</SakhiText>
              )}
            </View>
            <TouchableOpacity onPress={reset} style={styles.closeBtnWrapper}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {!result && !isSettingUpCall && !callActive && renderOptions()}
          {isSettingUpCall && renderCallSetup()}
          {callActive && renderActiveCall()}
          {result && renderResult()}

          {loading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color="#DC2626" />
              <SakhiText variant="body" style={styles.loadingText}>Locating nearest {selectedCategory}...</SakhiText>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { 
    flex: 1, 
    backgroundColor: 'rgba(17, 24, 39, 0.6)', 
    justifyContent: 'flex-end' 
  },
  modalView: { 
    backgroundColor: '#FFFFFF', 
    padding: 24, 
    borderTopLeftRadius: 24, 
    borderTopRightRadius: 24, 
    minHeight: 350, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: -4 }, 
    shadowOpacity: 0.1, 
    shadowRadius: 12, 
    elevation: 20 
  },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'flex-start', 
    marginBottom: 24 
  },
  title: { 
    color: '#1F2937', 
    marginBottom: 4 
  },
  closeBtnWrapper: { 
    padding: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  optionsContainer: { 
    gap: 12 
  },
  optionCard: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: '#FFFFFF', 
    padding: 16, 
    borderRadius: 16, 
    borderWidth: 1, 
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  iconContainer: { 
    width: 48, 
    height: 48, 
    borderRadius: 24, 
    backgroundColor: '#FEF2F2', 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginRight: 16 
  },
  optionTextContainer: { 
    flex: 1 
  },
  resultContainer: { 
    alignItems: 'center', 
    paddingVertical: 12 
  },
  resultIconWrapper: {
    width: 64, 
    height: 64, 
    borderRadius: 32, 
    backgroundColor: '#FEF2F2', 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginBottom: 16 
  },
  resultCategory: { 
    color: '#374151', 
    marginBottom: 4 
  },
  resultMockBadge: {
    fontStyle: 'italic',
    marginBottom: 24,
  },
  resultCard: {
    width: '100%',
    paddingVertical: 24,
    marginBottom: 24,
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
  },
  navigateBtn: { 
    width: '100%', 
  },
  loadingOverlay: { 
    ...StyleSheet.absoluteFill, 
    backgroundColor: 'rgba(255, 255, 255, 0.9)', 
    justifyContent: 'center', 
    alignItems: 'center', 
    borderTopLeftRadius: 24, 
    borderTopRightRadius: 24 
  },
  loadingText: { 
    marginTop: 16, 
    color: '#4B5563', 
    fontWeight: '500' 
  },
  callSetupContainer: { 
    paddingVertical: 8 
  },
  callSetupTitle: { 
    color: '#1F2937', 
    marginBottom: 8 
  },
  callSetupDesc: { 
    marginBottom: 24 
  },
  label: { 
    color: '#374151', 
    marginBottom: 12, 
    marginTop: 8 
  },
  row: { 
    flexDirection: 'row', 
    gap: 12, 
    marginBottom: 16 
  },
  toggleBtn: { 
    flex: 1, 
    paddingVertical: 14, 
    borderWidth: 1, 
    borderColor: '#D1D5DB', 
    borderRadius: 12, 
    alignItems: 'center', 
    backgroundColor: '#FFFFFF' 
  },
  toggleBtnActive: { 
    borderColor: '#DC2626', 
    backgroundColor: '#FEF2F2' 
  },
  toggleBtnText: { 
    color: '#4B5563', 
    fontWeight: '600' 
  },
  toggleBtnTextActive: { 
    color: '#DC2626' 
  },
  startCallBtn: { 
    marginTop: 24 
  },
  activeCallContainer: { 
    alignItems: 'center', 
    paddingVertical: 32 
  },
  callAvatar: { 
    width: 96, 
    height: 96, 
    borderRadius: 48, 
    backgroundColor: '#F3F4F6', 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginBottom: 24 
  },
  callerName: { 
    color: '#1F2937', 
    marginBottom: 12 
  },
  callStatus: { 
    color: '#374151', 
    marginBottom: 8, 
    fontVariant: ['tabular-nums'] 
  },
  callSubtitle: { 
    fontStyle: 'italic', 
    marginBottom: 48 
  },
  endCallBtn: { 
    backgroundColor: '#DC2626', 
    width: 64, 
    height: 64, 
    borderRadius: 32, 
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  endCallIcon: {
    transform: [{ rotate: '135deg' }]
  }
});

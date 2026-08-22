import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';

interface Props {
  visible: boolean;
  onClose: () => void;
}

export default function QuickFindModal({ visible, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const [isSettingUpCall, setIsSettingUpCall] = useState(false);
  const [callLanguage, setCallLanguage] = useState('English');
  const [callDuration, setCallDuration] = useState(2);
  const [callActive, setCallActive] = useState(false);

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

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <Text style={styles.title}>Quick Find</Text>
            <TouchableOpacity onPress={reset}>
              <Text style={styles.closeBtn}>✕</Text>
            </TouchableOpacity>
          </View>

          {!result && !isSettingUpCall && !callActive ? (
            <View style={styles.optionsContainer}>
              <TouchableOpacity style={styles.optionBtn} onPress={() => handleSearch('Washroom')}>
                <Text style={styles.icon}>🚻</Text>
                <Text style={styles.optionText}>Need a washroom?</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.optionBtn} onPress={() => handleSearch('Medical Clinic')}>
                <Text style={styles.icon}>🏥</Text>
                <Text style={styles.optionText}>Need medical help?</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.optionBtn} onPress={() => handleSearch('Police Station')}>
                <Text style={styles.icon}>🚓</Text>
                <Text style={styles.optionText}>Need police assistance?</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.optionBtn, { borderColor: '#d946ef', backgroundColor: '#fdf4ff' }]} onPress={() => setIsSettingUpCall(true)}>
                <Text style={styles.icon}>📞</Text>
                <Text style={[styles.optionText, { color: '#a21caf' }]}>Fake "Call a Friend"</Text>
              </TouchableOpacity>
            </View>
          ) : isSettingUpCall ? (
            <View style={styles.callSetupContainer}>
              <Text style={styles.callSetupTitle}>Simulate a Phone Call</Text>
              <Text style={styles.callSetupDesc}>Plays a voice note to make it seem like you are on a call.</Text>
              
              <Text style={styles.label}>Select Language:</Text>
              <View style={styles.row}>
                {['English', 'Hindi'].map((lang) => (
                  <TouchableOpacity key={lang} style={[styles.toggleBtn, callLanguage === lang && styles.toggleBtnActive]} onPress={() => setCallLanguage(lang)}>
                    <Text style={[styles.toggleBtnText, callLanguage === lang && styles.toggleBtnTextActive]}>{lang}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={styles.label}>Select Duration:</Text>
              <View style={styles.row}>
                {[2, 5, 10].map((mins) => (
                  <TouchableOpacity key={mins} style={[styles.toggleBtn, callDuration === mins && styles.toggleBtnActive]} onPress={() => setCallDuration(mins)}>
                    <Text style={[styles.toggleBtnText, callDuration === mins && styles.toggleBtnTextActive]}>{mins} min</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.startCallBtn} onPress={() => { setIsSettingUpCall(false); setCallActive(true); }}>
                <Text style={styles.startCallText}>Start Fake Call Now</Text>
              </TouchableOpacity>
            </View>
          ) : callActive ? (
            <View style={styles.activeCallContainer}>
              <View style={styles.callAvatar}><Text style={styles.callAvatarText}>📞</Text></View>
              <Text style={styles.callerName}>Unknown Caller</Text>
              <Text style={styles.callStatus}>00:14 / {callDuration}:00</Text>
              <Text style={styles.callSubtitle}>Playing {callLanguage} voice notes...</Text>
              <TouchableOpacity style={styles.endCallBtn} onPress={reset}>
                <Text style={styles.endCallText}>End Call</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.resultContainer}>
              <Text style={styles.resultCategory}>Found {selectedCategory}</Text>
              <Text style={styles.resultText}>{result}</Text>
              <TouchableOpacity style={styles.navigateBtn} onPress={reset}>
                <Text style={styles.navigateText}>Navigate Now</Text>
              </TouchableOpacity>
            </View>
          )}

          {loading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color="#2563eb" />
              <Text style={styles.loadingText}>Locating nearest {selectedCategory}...</Text>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalView: { backgroundColor: '#fff', padding: 24, borderTopLeftRadius: 20, borderTopRightRadius: 20, minHeight: 300, shadowColor: '#000', shadowOffset: { width: 0, height: -4 }, shadowOpacity: 0.1, shadowRadius: 10, elevation: 10 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#1f2937' },
  closeBtn: { fontSize: 24, color: '#9ca3af', padding: 4 },
  optionsContainer: { gap: 12 },
  optionBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#f3f4f6', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#e5e7eb' },
  icon: { fontSize: 24, marginRight: 16 },
  optionText: { fontSize: 16, fontWeight: '600', color: '#4b5563' },
  resultContainer: { alignItems: 'center', paddingVertical: 20 },
  resultCategory: { fontSize: 16, color: '#6b7280', marginBottom: 8 },
  resultText: { fontSize: 20, fontWeight: 'bold', color: '#1f2937', marginBottom: 24 },
  navigateBtn: { backgroundColor: '#2563eb', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 12, width: '100%', alignItems: 'center' },
  navigateText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  loadingOverlay: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(255,255,255,0.9)', justifyContent: 'center', alignItems: 'center', borderTopLeftRadius: 20, borderTopRightRadius: 20 },
  loadingText: { marginTop: 12, fontSize: 14, color: '#4b5563', fontWeight: '500' },
  callSetupContainer: { paddingVertical: 10 },
  callSetupTitle: { fontSize: 20, fontWeight: 'bold', color: '#1f2937', marginBottom: 4 },
  callSetupDesc: { fontSize: 14, color: '#6b7280', marginBottom: 20 },
  label: { fontSize: 16, fontWeight: '600', color: '#374151', marginBottom: 10, marginTop: 10 },
  row: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  toggleBtn: { flex: 1, paddingVertical: 12, borderWidth: 1, borderColor: '#d1d5db', borderRadius: 8, alignItems: 'center', backgroundColor: '#f9fafb' },
  toggleBtnActive: { borderColor: '#d946ef', backgroundColor: '#fdf4ff' },
  toggleBtnText: { fontSize: 15, color: '#4b5563', fontWeight: '600' },
  toggleBtnTextActive: { color: '#a21caf' },
  startCallBtn: { backgroundColor: '#d946ef', paddingVertical: 14, borderRadius: 12, alignItems: 'center', marginTop: 20 },
  startCallText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  activeCallContainer: { alignItems: 'center', paddingVertical: 20 },
  callAvatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#fdf4ff', justifyContent: 'center', alignItems: 'center', marginBottom: 16, borderWidth: 2, borderColor: '#d946ef' },
  callAvatarText: { fontSize: 40 },
  callerName: { fontSize: 24, fontWeight: 'bold', color: '#1f2937', marginBottom: 8 },
  callStatus: { fontSize: 18, color: '#4b5563', marginBottom: 8, fontVariant: ['tabular-nums'] },
  callSubtitle: { fontSize: 14, color: '#6b7280', fontStyle: 'italic', marginBottom: 30 },
  endCallBtn: { backgroundColor: '#ef4444', paddingVertical: 14, paddingHorizontal: 40, borderRadius: 30, alignItems: 'center', width: '100%' },
  endCallText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});

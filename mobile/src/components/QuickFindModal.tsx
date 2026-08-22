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

          {!result ? (
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
  loadingOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(255,255,255,0.9)', justifyContent: 'center', alignItems: 'center', borderTopLeftRadius: 20, borderTopRightRadius: 20 },
  loadingText: { marginTop: 12, fontSize: 14, color: '#4b5563', fontWeight: '500' }
});

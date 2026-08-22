import React, { useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet, TextInput, ActivityIndicator } from 'react-native';
import { sakhiApi } from '../api/sakhiApi';

interface Props {
  visible: boolean;
  onClose: () => void;
  segmentId: string;
  latitude: number;
  longitude: number;
}

export default function ReportIncidentModal({ visible, onClose, segmentId, latitude, longitude }: Props) {
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState('Suspicious Activity');
  const [description, setDescription] = useState('');

  const submitIncident = async () => {
    setLoading(true);
    try {
      await sakhiApi.submitIncident({
        segment_id: segmentId,
        event_type: category,
        severity: category === 'Suspicious Activity' ? 60 : 40,
        description,
        latitude,
        longitude
      });
      alert('Report Submitted! This area\'s risk score has been dynamically updated.');
      onClose();
    } catch (err: any) {
      alert('Error submitting report: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.modalView}>
          <Text style={styles.title}>Report an Incident</Text>
          
          <Text style={styles.label}>Category</Text>
          <View style={styles.buttonGroup}>
            <TouchableOpacity 
              style={[styles.catButton, category === 'Suspicious Activity' && styles.catActive]}
              onPress={() => setCategory('Suspicious Activity')}
            >
              <Text style={category === 'Suspicious Activity' ? styles.catTextActive : styles.catText}>Suspicious Activity</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.catButton, category === 'Streetlight Out' && styles.catActive]}
              onPress={() => setCategory('Streetlight Out')}
            >
              <Text style={category === 'Streetlight Out' ? styles.catTextActive : styles.catText}>Streetlight Out</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.label}>Description</Text>
          <TextInput 
            style={styles.input}
            multiline
            placeholder="Details about what you saw..."
            value={description}
            onChangeText={setDescription}
          />

          <View style={styles.footer}>
            <TouchableOpacity style={styles.cancelBtn} onPress={onClose}>
              <Text style={styles.cancelText}>Cancel</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.submitBtn} onPress={submitIncident} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>Submit Report</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  modalView: { backgroundColor: '#fff', padding: 20, borderRadius: 12 },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 20, color: '#1f2937' },
  label: { fontSize: 14, fontWeight: 'bold', color: '#4b5563', marginBottom: 8 },
  buttonGroup: { flexDirection: 'row', gap: 10, marginBottom: 20 },
  catButton: { padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#d1d5db' },
  catActive: { backgroundColor: '#ef4444', borderColor: '#ef4444' },
  catText: { color: '#4b5563' },
  catTextActive: { color: '#fff', fontWeight: 'bold' },
  input: { borderWidth: 1, borderColor: '#d1d5db', borderRadius: 8, padding: 12, height: 100, textAlignVertical: 'top', marginBottom: 20 },
  footer: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10 },
  cancelBtn: { padding: 12 },
  cancelText: { color: '#6b7280', fontWeight: 'bold' },
  submitBtn: { backgroundColor: '#2563eb', padding: 12, borderRadius: 8, minWidth: 100, alignItems: 'center' },
  submitText: { color: '#fff', fontWeight: 'bold' }
});

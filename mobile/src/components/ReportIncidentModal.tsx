import React, { useState } from 'react';
import { Modal, View, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { sakhiApi } from '../api/sakhiApi';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiInput } from './ui/SakhiInput';

interface Props {
  visible: boolean;
  onClose: () => void;
  segmentId: string;
  latitude: number;
  longitude: number;
}

export default function ReportIncidentModal({ visible, onClose, segmentId, latitude, longitude }: Props) {
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState<'Suspicious Activity' | 'Streetlight Out'>('Suspicious Activity');
  const [description, setDescription] = useState('');
  
  // Custom in-app status state: 'idle' | 'success' | 'error'
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleClose = () => {
    // Reset state on close
    setSubmitStatus('idle');
    setCategory('Suspicious Activity');
    setDescription('');
    setErrorMessage('');
    onClose();
  };

  const submitIncident = async () => {
    setLoading(true);
    setSubmitStatus('idle');
    try {
      await sakhiApi.submitIncident({
        segment_id: segmentId,
        event_type: category,
        severity: category === 'Suspicious Activity' ? 60 : 40,
        description,
        latitude,
        longitude
      });
      setSubmitStatus('success');
    } catch (err: any) {
      setSubmitStatus('error');
      setErrorMessage(err.message || 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const renderSuccess = () => (
    <View style={styles.statusContainer}>
      <View style={styles.successIconWrapper}>
        <Ionicons name="checkmark-circle" size={64} color="#10B981" />
      </View>
      <SakhiText variant="h2" style={{ marginBottom: 8, textAlign: 'center' }}>Report submitted</SakhiText>
      <SakhiText variant="body" color="secondary" style={{ textAlign: 'center', marginBottom: 32 }}>
        Your report has been sent for this route.
      </SakhiText>
      <SakhiButton title="Done" onPress={handleClose} />
    </View>
  );

  const renderError = () => (
    <View style={styles.statusContainer}>
      <View style={styles.errorIconWrapper}>
        <Ionicons name="alert-circle" size={64} color="#8B1E1E" />
      </View>
      <SakhiText variant="h2" style={{ marginBottom: 8, textAlign: 'center' }}>Submission Failed</SakhiText>
      <SakhiText variant="body" color="secondary" style={{ textAlign: 'center', marginBottom: 32 }}>
        {errorMessage}
      </SakhiText>
      <SakhiButton title="Try Again" onPress={() => setSubmitStatus('idle')} style={{ marginBottom: 12 }} />
      <SakhiButton title="Cancel" variant="secondary" onPress={handleClose} />
    </View>
  );

  const renderForm = () => (
    <View style={{ flexShrink: 1 }}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 20 }}>
        <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <SakhiText variant="h2" style={styles.title}>Report a safety issue</SakhiText>
          <SakhiText variant="body" color="secondary">Help improve safety information for this route.</SakhiText>
        </View>
        <TouchableOpacity onPress={handleClose} style={styles.closeBtnWrapper}>
          <Ionicons name="close" size={24} color="#6B7280" />
        </TouchableOpacity>
      </View>

      <SakhiText variant="h3" style={styles.sectionTitle}>What happened?</SakhiText>
      <View style={styles.buttonGroup}>
        <TouchableOpacity 
          style={[styles.catCard, category === 'Suspicious Activity' && styles.catActive]}
          onPress={() => setCategory('Suspicious Activity')}
        >
          <Ionicons 
            name="warning" 
            size={24} 
            color={category === 'Suspicious Activity' ? '#8B1E1E' : '#9CA3AF'} 
            style={{ marginBottom: 8 }}
          />
          <SakhiText variant="body" style={category === 'Suspicious Activity' ? styles.catTextActive : styles.catText}>
            Suspicious Activity
          </SakhiText>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.catCard, category === 'Streetlight Out' && styles.catActive]}
          onPress={() => setCategory('Streetlight Out')}
        >
          <Ionicons 
            name="bulb" 
            size={24} 
            color={category === 'Streetlight Out' ? '#8B1E1E' : '#9CA3AF'} 
            style={{ marginBottom: 8 }}
          />
          <SakhiText variant="body" style={category === 'Streetlight Out' ? styles.catTextActive : styles.catText}>
            Streetlight Out
          </SakhiText>
        </TouchableOpacity>
      </View>

      <SakhiInput
        label="Additional details (optional)"
        placeholder="Tell us what you noticed..."
        multiline
        value={description}
        onChangeText={setDescription}
        style={styles.input}
      />

      <View style={styles.locationContext}>
        <Ionicons name="location-sharp" size={16} color="#6B7280" />
        <SakhiText variant="caption" color="secondary" style={{ marginLeft: 4 }}>
          Report linked to your current route segment
        </SakhiText>
      </View>
      </ScrollView>

      <View style={styles.footer}>
        <View style={{ flex: 1, marginRight: 12 }}>
          <SakhiButton title="Cancel" variant="secondary" onPress={handleClose} disabled={loading} />
        </View>
        <View style={{ flex: 1 }}>
          <SakhiButton 
            title={loading ? "Sending..." : "Submit Report"} 
            onPress={submitIncident} 
            disabled={loading} 
          />
        </View>
      </View>
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <KeyboardAvoidingView 
        style={styles.overlay} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.modalView}>
          {submitStatus === 'success' && renderSuccess()}
          {submitStatus === 'error' && renderError()}
          {submitStatus === 'idle' && renderForm()}
        </View>
      </KeyboardAvoidingView>
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
    minHeight: 400, 
    maxHeight: '90%',
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: -4 }, 
    shadowOpacity: 0.1, 
    shadowRadius: 12, 
    elevation: 20 
  },
  formContainer: {
    flex: 1,
  },
  statusContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 32,
  },
  successIconWrapper: {
    marginBottom: 16,
  },
  errorIconWrapper: {
    marginBottom: 16,
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
    marginLeft: 16,
  },
  sectionTitle: {
    marginBottom: 12,
  },
  buttonGroup: { 
    flexDirection: 'row', 
    gap: 12, 
    marginBottom: 24 
  },
  catCard: { 
    flex: 1,
    padding: 16, 
    borderRadius: 16, 
    borderWidth: 1, 
    borderColor: '#F3F4F6',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.02,
    shadowRadius: 4,
    elevation: 1,
  },
  catActive: { 
    backgroundColor: '#FDF2F2', 
    borderColor: '#8B1E1E' 
  },
  catText: { 
    color: '#4B5563',
    textAlign: 'center',
    fontWeight: '500',
  },
  catTextActive: { 
    color: '#8B1E1E', 
    fontWeight: '600',
    textAlign: 'center',
  },
  input: { 
    height: 100, 
    textAlignVertical: 'top',
  },
  locationContext: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 32,
  },
  footer: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
  }
});

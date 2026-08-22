import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView, Switch, ActivityIndicator, Alert } from 'react-native';
import { WashroomResponse } from '../types/api';
import { sakhiApi } from '../api/sakhiApi';

interface WashroomFacilityCardProps {
  visible: boolean;
  onClose: () => void;
  washroom: WashroomResponse | null;
  distance: number;
}

export default function WashroomFacilityCard({ visible, onClose, washroom, distance }: WashroomFacilityCardProps) {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [isOpen, setIsOpen] = useState(true);
  const [cleanliness, setCleanliness] = useState('Clean');
  const [safety, setSafety] = useState('Safe');
  const [accessible, setAccessible] = useState(false);

  if (!visible || !washroom) return null;

  const getFreshnessText = () => {
    if (!washroom.last_verified_timestamp) {
      return "⚠️ Status not recently verified.";
    }
    const lastVerified = new Date(washroom.last_verified_timestamp);
    const now = new Date();
    const diffHours = (now.getTime() - lastVerified.getTime()) / (1000 * 60 * 60);

    if (diffHours < 24) {
      const displayHours = Math.max(1, Math.round(diffHours));
      return `✓ Verified by ${washroom.verified_count} users. Last reported: ${displayHours} hours ago.`;
    } else {
      const displayDays = Math.round(diffHours / 24);
      return `⚠️ Status not recently verified. Last verified: ${displayDays} days ago.`;
    }
  };

  const handleSubmitFeedback = async () => {
    setSubmitting(true);
    try {
      await sakhiApi.submitWashroomFeedback(washroom.id, {
        is_open: isOpen,
        cleanliness: cleanliness,
        safety: safety,
        accessible: accessible
      });
      Alert.alert('Success', 'Thank you for keeping the community safe and informed!');
      setShowFeedbackForm(false);
    } catch (err) {
      console.error(err);
      Alert.alert('Error', 'Failed to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderOptionSelector = (label: string, value: string, options: string[], onChange: (val: string) => void) => (
    <View style={styles.formGroup}>
      <Text style={styles.formLabel}>{label}</Text>
      <View style={styles.optionsRow}>
        {options.map((opt) => (
          <TouchableOpacity
            key={opt}
            style={[styles.optionBtn, value === opt && styles.optionBtnActive]}
            onPress={() => onChange(opt)}
          >
            <Text style={[styles.optionText, value === opt && styles.optionTextActive]}>{opt}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <TouchableOpacity style={styles.overlay} activeOpacity={1} onPress={onClose} />
      <View style={styles.sheetContainer}>
        <View style={styles.handleBar} />
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.header}>🚻 Washroom — {distance} m</Text>
          <Text style={styles.address}>{washroom.name}</Text>
          {washroom.address && <Text style={styles.addressSub}>{washroom.address}</Text>}
          
          <View style={styles.freshnessContainer}>
            <Text style={styles.freshnessText}>{getFreshnessText()}</Text>
          </View>

          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Status</Text>
              <Text style={[styles.statusValue, washroom.is_open ? styles.textGreen : styles.textRed]}>
                {washroom.is_open ? '🟢 Open' : '🔴 Closed'}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Cleanliness</Text>
              <Text style={[styles.statusValue, washroom.cleanliness === 'Clean' ? styles.textGreen : (washroom.cleanliness === 'Average' ? styles.textAmber : styles.textRed)]}>
                {washroom.cleanliness === 'Clean' ? '🟢 ' : (washroom.cleanliness === 'Average' ? '🟡 ' : '🔴 ')}
                {washroom.cleanliness}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Safety</Text>
              <Text style={[styles.statusValue, washroom.safety === 'Safe' ? styles.textGreen : (washroom.safety === 'Concern' ? styles.textAmber : styles.textRed)]}>
                {washroom.safety === 'Safe' ? '🟢 ' : (washroom.safety === 'Concern' ? '🟡 ' : '🔴 ')}
                {washroom.safety}
              </Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>Accessible</Text>
              <Text style={[styles.statusValue, washroom.accessible ? styles.textGreen : styles.textRed]}>
                {washroom.accessible ? '🟢 Yes' : '🔴 No'}
              </Text>
            </View>
          </View>

          {!showFeedbackForm ? (
            <TouchableOpacity style={styles.feedbackButton} onPress={() => setShowFeedbackForm(true)}>
              <Text style={styles.feedbackButtonText}>Provide Feedback</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.formContainer}>
              <Text style={styles.formTitle}>Your Review</Text>
              
              <View style={styles.formGroupRow}>
                <Text style={styles.formLabel}>Is it Open?</Text>
                <Switch value={isOpen} onValueChange={setIsOpen} trackColor={{ false: '#d1d5db', true: '#10b981' }} thumbColor="#fff" />
              </View>
              
              {renderOptionSelector('Cleanliness', cleanliness, ['Clean', 'Average', 'Dirty'], setCleanliness)}
              {renderOptionSelector('Safety', safety, ['Safe', 'Concern', 'Unsafe'], setSafety)}
              
              <View style={styles.formGroupRow}>
                <Text style={styles.formLabel}>Wheelchair Accessible?</Text>
                <Switch value={accessible} onValueChange={setAccessible} trackColor={{ false: '#d1d5db', true: '#10b981' }} thumbColor="#fff" />
              </View>

              <View style={styles.formActions}>
                <TouchableOpacity style={styles.cancelButton} onPress={() => setShowFeedbackForm(false)}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.submitButton} onPress={handleSubmitFeedback} disabled={submitting}>
                  {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitButtonText}>Submit</Text>}
                </TouchableOpacity>
              </View>
            </View>
          )}

        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  sheetContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
    paddingBottom: 30,
    marginTop: 'auto', // Pushes it to bottom
    elevation: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
  },
  handleBar: {
    width: 40,
    height: 5,
    backgroundColor: '#d1d5db',
    borderRadius: 3,
    alignSelf: 'center',
    marginVertical: 12,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  header: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 4,
  },
  address: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '600',
  },
  addressSub: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  freshnessContainer: {
    backgroundColor: '#f3f4f6',
    padding: 10,
    borderRadius: 8,
    marginVertical: 14,
  },
  freshnessText: {
    fontSize: 13,
    color: '#4b5563',
    fontStyle: 'italic',
  },
  statusGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statusItem: {
    width: '48%',
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
  },
  statusLabel: {
    fontSize: 12,
    color: '#6b7280',
    textTransform: 'uppercase',
    fontWeight: 'bold',
    marginBottom: 6,
  },
  statusValue: {
    fontSize: 15,
    fontWeight: 'bold',
  },
  textGreen: { color: '#059669' },
  textAmber: { color: '#d97706' },
  textRed: { color: '#dc2626' },
  
  feedbackButton: {
    backgroundColor: '#7c3aed',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  feedbackButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  
  formContainer: {
    marginTop: 16,
    borderTopWidth: 1,
    borderColor: '#e5e7eb',
    paddingTop: 16,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  formGroupRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  formGroup: {
    marginBottom: 16,
  },
  formLabel: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#4b5563',
    marginBottom: 8,
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  optionBtn: {
    flex: 1,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#f9fafb',
  },
  optionBtnActive: {
    borderColor: '#7c3aed',
    backgroundColor: '#ede9fe',
  },
  optionText: {
    fontSize: 14,
    color: '#4b5563',
    fontWeight: '600',
  },
  optionTextActive: {
    color: '#6d28d9',
  },
  formActions: {
    flexDirection: 'row',
    marginTop: 20,
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#e5e7eb',
  },
  cancelButtonText: {
    color: '#4b5563',
    fontWeight: 'bold',
    fontSize: 16,
  },
  submitButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    backgroundColor: '#10b981',
  },
  submitButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  }
});

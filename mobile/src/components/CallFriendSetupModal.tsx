import React, { useState, useEffect } from 'react';
import { Modal, View, StyleSheet, TouchableOpacity, TextInput, ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { sakhiApi, CallFriendSettings } from '../api/sakhiApi';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

const DEFAULT_SCRIPTS: Record<string, string> = {
  'en-IN': "Hey, where are you? I was just checking if you've reached safely. Stay on the line with me until you reach your destination.",
  'hi-IN': "??????, ?? ???? ???? ??? ?? ?? ????? ?? ??? ???? ?? ??? ?? ?? ???? ?? ???????? ????? ?? ???? ?? ?? ?? ?? ???? ????? ????, ???? ??? ???? ?? ?? ?????",
  'mr-IN': "???????, ?????? ???? ????? ?????? ???????? ???????? ?? ?? ???????????? ?? ??? ???? ????. ?????? ??? ???????????? ???????? ???? ????.",
};

export default function CallFriendSetupModal({ visible, onClose, onSaved }: Props) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [callerName, setCallerName] = useState('Bro');
  const [customName, setCustomName] = useState('');
  const [languageCode, setLanguageCode] = useState('en-IN');
  const [voiceGender, setVoiceGender] = useState<'Male' | 'Female'>('Male');
  const [script, setScript] = useState(DEFAULT_SCRIPTS['en-IN']);
  const [durationMinutes, setDurationMinutes] = useState<number>(2);

  useEffect(() => {
    if (visible) {
      loadExistingSettings();
    }
  }, [visible]);

  const loadExistingSettings = async () => {
    setLoading(true);
    try {
      const existing = await sakhiApi.getCallFriendSettings();
      if (existing) {
        if (['Bro', 'Mom', 'Love', 'Friend'].includes(existing.caller_name)) {
          setCallerName(existing.caller_name);
          setCustomName('');
        } else {
          setCallerName('Custom');
          setCustomName(existing.caller_name);
        }
        setLanguageCode(existing.language_code || 'en-IN');
        setVoiceGender(existing.voice_gender === 'Female' ? 'Female' : 'Male');
        setScript(existing.script || DEFAULT_SCRIPTS[existing.language_code || 'en-IN']);
        setDurationMinutes(existing.duration_minutes || 2);
      }
    } catch (err: any) {
      console.log('Error loading Call a Friend settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = (code: string) => {
    setLanguageCode(code);
    // If current script matches a default script or is empty, auto update to selected language default script
    if (!script || Object.values(DEFAULT_SCRIPTS).includes(script)) {
      setScript(DEFAULT_SCRIPTS[code] || DEFAULT_SCRIPTS['en-IN']);
    }
  };

  const handleSave = async () => {
    const finalCallerName = callerName === 'Custom' ? customName.trim() : callerName;
    if (!finalCallerName) {
      Alert.alert('Validation Error', 'Please specify a caller name.');
      return;
    }

    if (!script.trim()) {
      Alert.alert('Validation Error', 'Please enter a valid call script.');
      return;
    }

    if (script.length > 2500) {
      Alert.alert('Validation Error', 'Script cannot exceed 2500 characters.');
      return;
    }

    setSaving(true);
    try {
      await sakhiApi.saveCallFriendSettings({
        caller_name: finalCallerName,
        language_code: languageCode,
        voice_gender: voiceGender,
        script: script.trim(),
        duration_minutes: durationMinutes,
      });

      Alert.alert('Success', 'Call a Friend setup saved to your account!');
      if (onSaved) onSaved();
      onClose();
    } catch (err: any) {
      console.error('Failed to save Call a Friend settings:', err);
      Alert.alert('Save Error', err.response?.data?.detail || 'Failed to save setup. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.overlay}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <SakhiText variant="h2" style={{ color: '#1F2937' }}>Call a Friend Setup</SakhiText>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingWrapper}>
              <ActivityIndicator size="large" color="#DC2626" />
              <SakhiText variant="body" style={{ marginTop: 12 }}>Loading your saved setup...</SakhiText>
            </View>
          ) : (
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.formContainer}>
              {/* 1. Caller Name */}
              <SakhiText variant="h3" style={styles.label}>1. Caller Name</SakhiText>
              <View style={styles.rowGrid}>
                {['Bro', 'Mom', 'Love', 'Friend'].map((name) => (
                  <TouchableOpacity
                    key={name}
                    style={[styles.chipBtn, callerName === name && styles.chipBtnActive]}
                    onPress={() => { setCallerName(name); setCustomName(''); }}
                  >
                    <SakhiText variant="body" style={[styles.chipText, callerName === name && styles.chipTextActive]}>{name}</SakhiText>
                  </TouchableOpacity>
                ))}
                <TouchableOpacity
                  style={[styles.chipBtn, callerName === 'Custom' && styles.chipBtnActive]}
                  onPress={() => setCallerName('Custom')}
                >
                  <SakhiText variant="body" style={[styles.chipText, callerName === 'Custom' && styles.chipTextActive]}>Custom</SakhiText>
                </TouchableOpacity>
              </View>

              {callerName === 'Custom' && (
                <TextInput
                  style={styles.textInput}
                  placeholder="Enter caller name (e.g. Rahul, Sister)"
                  value={customName}
                  onChangeText={setCustomName}
                  maxLength={30}
                />
              )}

              {/* 2. Language */}
              <SakhiText variant="h3" style={styles.label}>2. Language</SakhiText>
              <View style={styles.rowGrid}>
                {[
                  { code: 'en-IN', label: 'English' },
                  { code: 'hi-IN', label: 'Hindi' },
                  { code: 'mr-IN', label: 'Marathi' },
                ].map((item) => (
                  <TouchableOpacity
                    key={item.code}
                    style={[styles.toggleBtn, languageCode === item.code && styles.toggleBtnActive]}
                    onPress={() => handleLanguageChange(item.code)}
                  >
                    <SakhiText variant="body" style={[styles.toggleBtnText, languageCode === item.code && styles.toggleBtnTextActive]}>{item.label}</SakhiText>
                  </TouchableOpacity>
                ))}
              </View>

              {/* 3. Voice Gender */}
              <SakhiText variant="h3" style={styles.label}>3. Voice</SakhiText>
              <View style={styles.rowGrid}>
                {['Male', 'Female'].map((gender) => (
                  <TouchableOpacity
                    key={gender}
                    style={[styles.toggleBtn, voiceGender === gender && styles.toggleBtnActive]}
                    onPress={() => setVoiceGender(gender as 'Male' | 'Female')}
                  >
                    <SakhiText variant="body" style={[styles.toggleBtnText, voiceGender === gender && styles.toggleBtnTextActive]}>{gender}</SakhiText>
                  </TouchableOpacity>
                ))}
              </View>

              {/* 4. Script */}
              <View style={styles.labelRow}>
                <SakhiText variant="h3" style={styles.label}>4. Script</SakhiText>
                <SakhiText variant="subtext" color="secondary">{script.length}/2500 chars</SakhiText>
              </View>
              <TextInput
                style={[styles.textInput, styles.multilineInput]}
                placeholder="Enter what your friend will say..."
                value={script}
                onChangeText={setScript}
                multiline={true}
                numberOfLines={4}
                maxLength={2500}
              />

              {/* 5. Duration */}
              <SakhiText variant="h3" style={styles.label}>5. Duration</SakhiText>
              <View style={styles.rowGrid}>
                {[2, 5, 10].map((mins) => (
                  <TouchableOpacity
                    key={mins}
                    style={[styles.toggleBtn, durationMinutes === mins && styles.toggleBtnActive]}
                    onPress={() => setDurationMinutes(mins)}
                  >
                    <SakhiText variant="body" style={[styles.toggleBtnText, durationMinutes === mins && styles.toggleBtnTextActive]}>{mins} min</SakhiText>
                  </TouchableOpacity>
                ))}
              </View>

              <SakhiButton
                title={saving ? "Saving Setup..." : "Save Call Setup"}
                onPress={handleSave}
                loading={saving}
                disabled={saving}
                style={styles.saveBtn}
              />
            </ScrollView>
          )}
        </View>
      </KeyboardAvoidingView>
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
    maxHeight: '88%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  closeBtn: {
    padding: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  loadingWrapper: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  formContainer: {
    gap: 16,
    paddingBottom: 24,
  },
  label: {
    marginTop: 4,
    color: '#374151',
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  chipBtn: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#F9FAFB',
  },
  chipBtnActive: {
    borderColor: '#DC2626',
    backgroundColor: '#FEF2F2',
  },
  chipText: {
    color: '#4B5563',
  },
  chipTextActive: {
    color: '#DC2626',
    fontWeight: '600',
  },
  toggleBtn: {
    flex: 1,
    minWidth: '28%',
    paddingVertical: 12,
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
  textInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 12,
    padding: 12,
    fontSize: 15,
    backgroundColor: '#FAFAFA',
    color: '#1F2937',
  },
  multilineInput: {
    minHeight: 90,
    textAlignVertical: 'top',
  },
  saveBtn: {
    marginTop: 12,
  },
});
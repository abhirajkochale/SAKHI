import React, { useEffect, useState } from 'react';
import { Modal, View, StyleSheet, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform, Alert, ScrollView, TextInput } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { supabase } from '../api/supabase';
import { sakhiApi } from '../api/sakhiApi';
import { User } from '@supabase/supabase-js';
import * as WebBrowser from 'expo-web-browser';

WebBrowser.maybeCompleteAuthSession();

interface Props {
  visible: boolean;
  onClose: () => void;
}

export default function ProfileModal({ visible, onClose }: Props) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isVerified, setIsVerified] = useState(false);
  const [isDemoVerified, setIsDemoVerified] = useState(false);
  const [authState, setAuthState] = useState<'profile' | 'enter_aadhaar' | 'enter_otp'>('profile');
  const [aadhaarInput, setAadhaarInput] = useState('');
  const [otpInput, setOtpInput] = useState('');
  const [referenceId, setReferenceId] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const userData = await sakhiApi.getCurrentUser();
        if (userData && userData.identity_status === 'VERIFIED') {
          setIsVerified(true);
          setIsDemoVerified(false);
        } else if (userData && userData.identity_status === 'VERIFIED_DEMO') {
          setIsVerified(true);
          setIsDemoVerified(true);
        } else {
          setIsVerified(false);
          setIsDemoVerified(false);
        }
      } catch (err) {
        console.warn('Failed to fetch user profile:', err);
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchUserProfile();
      }
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchUserProfile();
      } else {
        setIsVerified(false);
        setIsDemoVerified(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: 'sakhi://auth/callback',
          skipBrowserRedirect: true,
        },
      });

      if (error) throw error;
      if (!data?.url) throw new Error('No OAuth URL returned');

      const res = await WebBrowser.openAuthSessionAsync(
        data.url,
        'sakhi://auth/callback'
      );

      if (res.type === 'success' && res.url) {
        const url = res.url;
        const fragment = url.split('#')[1];
        if (fragment) {
          const params = Object.fromEntries(
            fragment.split('&').map(p => p.split('=').map(decodeURIComponent))
          );
          if (params.access_token) {
            const { error: sessionError } = await supabase.auth.setSession({
              access_token: params.access_token,
              refresh_token: params.refresh_token,
            });
            if (sessionError) throw sessionError;
          }
        }

        const queryString = url.split('?')[1]?.split('#')[0];
        if (queryString) {
          const params = Object.fromEntries(
            queryString.split('&').map(p => p.split('=').map(decodeURIComponent))
          );
          if (params.code) {
            const { error: codeError } = await supabase.auth.exchangeCodeForSession(params.code);
            if (codeError) throw codeError;
          }
        }
      }
    } catch (err: any) {
      Alert.alert('Sign In Error', err?.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    Alert.alert(
      "Sign out of SAKHI?",
      "Are you sure you want to sign out?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Sign Out",
          style: "destructive",
          onPress: async () => {
            setLoading(true);
            try {
              const { error } = await supabase.auth.signOut();
              if (error) throw error;
              setUser(null);
              setIsVerified(false);
              setIsDemoVerified(false);
              resetVerificationState();
            } catch (err: any) {
              Alert.alert('Sign Out Error', err?.message || 'Failed to sign out properly.');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };

  const resetVerificationState = () => {
    setAuthState('profile');
    setAadhaarInput('');
    setOtpInput('');
    setReferenceId('');
  };

  const handleDemoVerify = async () => {
    const digitsOnly = aadhaarInput.replace(/\D/g, "");
    if (digitsOnly.length !== 12) {
      Alert.alert('Invalid Aadhaar', 'Please enter a valid 12-digit demo Aadhaar number.');
      return;
    }
    setActionLoading(true);
    const startTime = Date.now();
    try {
      await sakhiApi.verifyAadhaarDemo(digitsOnly);
      setIsVerified(true);
      setIsDemoVerified(true);
      resetVerificationState();
    } catch (err: any) {
      Alert.alert('Demo Verification Error', sakhiApi.getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendOtp = async () => {
    const digitsOnly = aadhaarInput.replace(/\D/g, "");
    if (digitsOnly.length !== 12) {
      Alert.alert('Invalid Aadhaar', 'Please enter a valid 12-digit Aadhaar number.');
      return;
    }
    setActionLoading(true);
    try {
      const res = await sakhiApi.initAadhaarVerification(digitsOnly);
      setReferenceId(res.reference_id);
      setAuthState('enter_otp');
    } catch (err: any) {
      Alert.alert('Verification Error', sakhiApi.getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otpInput.length !== 6) {
      Alert.alert('Invalid OTP', 'Please enter a valid 6-digit OTP.');
      return;
    }
    setActionLoading(true);
    try {
      await sakhiApi.verifyAadhaarOtp(referenceId, otpInput);
      setIsVerified(true);
      resetVerificationState();
    } catch (err: any) {
      Alert.alert('Verification Error', sakhiApi.getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const renderVerificationFlow = () => {
    if (authState === 'enter_aadhaar') {
      const digitsOnly = aadhaarInput.replace(/\D/g, "");
      const isButtonDisabled = actionLoading || digitsOnly.length !== 12;
      
      return (
        <ScrollView style={styles.flexShrink} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <SakhiText variant="h2" style={styles.title}>Demo verification for hackathon</SakhiText>
          <SakhiText variant="body" color="secondary" style={styles.subtitle}>
            Enter the designated test Aadhaar number to simulate verification. Real OTP-based Aadhaar verification is planned for production.
          </SakhiText>
          
          <TextInput
            style={styles.inputField}
            placeholder="12-digit Aadhaar Number"
            keyboardType="numeric"
            maxLength={12}
            value={aadhaarInput}
            onChangeText={setAadhaarInput}
            editable={!actionLoading}
            secureTextEntry={false}
          />

          <SakhiButton
            title={actionLoading ? "Verifying..." : "Verify Identity"}
            onPress={handleDemoVerify}
            style={{ marginTop: 24, width: '100%' }}
            disabled={isButtonDisabled}
            loading={actionLoading}
          />
          <SakhiButton
            title="Cancel"
            variant="secondary"
            onPress={resetVerificationState}
            style={{ marginTop: 12, width: '100%' }}
            disabled={actionLoading}
          />
        </ScrollView>
      );
    }

    if (authState === 'enter_otp') {
      return (
        <ScrollView style={styles.flexShrink} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <SakhiText variant="h2" style={styles.title}>Enter OTP</SakhiText>
          <SakhiText variant="body" color="secondary" style={styles.subtitle}>
            Enter the 6-digit OTP sent to your Aadhaar-linked mobile number.
          </SakhiText>
          
          <TextInput
            style={styles.inputField}
            placeholder="6-digit OTP"
            keyboardType="numeric"
            maxLength={6}
            value={otpInput}
            onChangeText={setOtpInput}
            editable={!actionLoading}
          />

          <SakhiButton
            title={actionLoading ? "Verifying..." : "Verify Identity"}
            onPress={handleVerifyOtp}
            style={{ marginTop: 24, width: '100%' }}
            disabled={actionLoading || otpInput.length !== 6}
          />
          <SakhiButton
            title="Cancel"
            variant="secondary"
            onPress={resetVerificationState}
            style={{ marginTop: 12, width: '100%' }}
            disabled={actionLoading}
          />
        </ScrollView>
      );
    }
    return null;
  };

  const renderContent = () => {
    if (loading) {
      return (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4F46E5" />
        </View>
      );
    }

    if (!user) {
      return (
        <ScrollView style={styles.flexShrink} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={styles.iconWrapper}>
            <Ionicons name="person-circle-outline" size={80} color="#9CA3AF" />
          </View>
          <SakhiText variant="h2" style={styles.title}>Sign In to SAKHI</SakhiText>
          <SakhiText variant="body" color="secondary" style={styles.subtitle}>
            Sign in to report incidents and help improve safety for everyone.
          </SakhiText>
          <SakhiButton
            title="Continue with Google"
            onPress={handleGoogleSignIn}
            style={{ marginTop: 24 }}
          />
        </ScrollView>
      );
    }

    if (authState !== 'profile') {
      return renderVerificationFlow();
    }

    return (
      <ScrollView style={styles.flexShrink} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        <View style={styles.iconWrapper}>
          <Ionicons name={isVerified ? "checkmark-circle" : "person-circle"} size={80} color={isVerified ? "#10B981" : "#4F46E5"} />
        </View>
        <SakhiText variant="h2" style={styles.title}>{user.user_metadata?.full_name || user.email?.split('@')[0] || 'User'}</SakhiText>
        <SakhiText variant="body" color="secondary" style={styles.subtitle}>{user.email}</SakhiText>

        <View style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <SakhiText variant="h3">Account Status</SakhiText>
            <View style={isVerified ? styles.badgeVerified : styles.badgeNormal}>
              <SakhiText variant="caption" style={{ color: isVerified ? '#047857' : '#4F46E5', fontWeight: 'bold' }}>
                {isVerified ? 'VERIFIED USER' : 'NORMAL USER'}
              </SakhiText>
            </View>
          </View>
          
          {!isVerified ? (
            <>
              <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>
                Verify your identity to become a trusted safety reporter.
              </SakhiText>
              <SakhiButton
                title="Verify Identity"
                variant="secondary"
                onPress={() => setAuthState('enter_aadhaar')}
                style={{ marginTop: 16 }}
              />
            </>
          ) : (
            <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>
              {isDemoVerified ? 'Demo identity verification. Production scope: real Aadhaar OTP verification.' : 'Identity verified via Aadhaar sandbox.'}
            </SakhiText>
          )}
        </View>

        <SakhiButton
          title="Sign Out"
          variant="secondary"
          onPress={handleSignOut}
          style={{ marginTop: 24, marginBottom: 16 }}
        />
      </ScrollView>
    );
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <KeyboardAvoidingView style={styles.overlay} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.modalView}>
          <View style={styles.header}>
            <SakhiText variant="h2" style={styles.headerTitle}>Profile</SakhiText>
            <TouchableOpacity onPress={onClose} style={styles.closeBtnWrapper}>
              <Ionicons name="close" size={24} color="#6B7280" />
            </TouchableOpacity>
          </View>
          {renderContent()}
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
    flexShrink: 1,
    backgroundColor: '#FFFFFF',
    padding: 24,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    minHeight: '60%',
    maxHeight: '90%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  flexShrink: {
    flexShrink: 1,
    width: '100%',
  },
  headerTitle: {
    color: '#1F2937',
  },
  closeBtnWrapper: {
    padding: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    alignItems: 'center',
    paddingBottom: 24,
  },
  iconWrapper: {
    marginBottom: 16,
  },
  title: {
    color: '#1F2937',
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 8,
  },
  statusCard: {
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 16,
    marginTop: 24,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  badgeNormal: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeVerified: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  inputField: {
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1F2937',
    marginTop: 24,
    textAlign: 'center',
    letterSpacing: 2,
  },
});

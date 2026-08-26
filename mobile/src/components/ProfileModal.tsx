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
  const [actionLoading, setActionLoading] = useState(false);
  
  const [showVerifyFlow, setShowVerifyFlow] = useState(false);
  const [demoIdInput, setDemoIdInput] = useState('');

  const syncUserProfileWithDb = async (sessionUser: User | null) => {
    // Always reset local state first
    setIsVerified(false);

    if (!sessionUser) return;

    try {
      // SINGLE SOURCE OF TRUTH: Fetch identity_status directly from backend database
      const profile = await sakhiApi.getCurrentUser();
      if (profile && profile.identity_status === 'VERIFIED') {
        setIsVerified(true);
      } else {
        setIsVerified(false);
      }
    } catch (e) {
      console.log('Error fetching DB user profile:', e);
      setIsVerified(false);
    }
  };

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        setLoading(true);
        const { data: { session } } = await supabase.auth.getSession();
        const currentAuthUser = session?.user ?? null;
        setUser(currentAuthUser);
        
        if (currentAuthUser) {
          await syncUserProfileWithDb(currentAuthUser);
        }
      } catch (error) {
        console.error('Profile fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    if (visible) {
      fetchUserProfile();
    }
  }, [visible]);

  useEffect(() => {
    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
      const currentAuthUser = session?.user ?? null;
      setUser(currentAuthUser);
      if (currentAuthUser) {
        await syncUserProfileWithDb(currentAuthUser);
      } else {
        setIsVerified(false);
      }
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const handleSignIn = async () => {
    try {
      setActionLoading(true);
      const isDev = process.env.EXPO_PUBLIC_APP_ENV === 'development';
      const redirectUri = isDev ? 'sakhi-dev://auth/callback' : 'sakhi://auth/callback';

      const res = await WebBrowser.openAuthSessionAsync(
        `${process.env.EXPO_PUBLIC_SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(redirectUri)}`,
        redirectUri
      );

      if (res.type === 'success' && res.url) {
        let queryString = '';
        if (res.url.includes('?')) {
          queryString = res.url.split('?')[1].split('#')[0];
        } else if (res.url.includes('#')) {
          queryString = res.url.split('#')[1];
        }

        const urlParams = new URLSearchParams(queryString);
        const code = urlParams.get('code');
        const errorDesc = urlParams.get('error_description');

        if (errorDesc) {
          throw new Error(errorDesc);
        }

        if (code) {
          const { data: sessionData, error: sessionError } = await supabase.auth.exchangeCodeForSession(code);
          if (sessionError) throw sessionError;
        } else {
          const accessToken = urlParams.get('access_token');
          const refreshToken = urlParams.get('refresh_token');

          if (accessToken && refreshToken) {
            await supabase.auth.setSession({
              access_token: accessToken,
              refresh_token: refreshToken,
            });
          } else {
             throw new Error('No authorization code found in the callback URL.');
          }
        }
      } else if (res.type !== 'cancel') {
          throw new Error('Authentication was not successful.');
      }
    } catch (error: any) {
      Alert.alert('Sign In Error', error.message || 'An error occurred during sign in');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      setActionLoading(true);
      await supabase.auth.signOut();
      setUser(null);
      setIsVerified(false);
      setShowVerifyFlow(false);
      setDemoIdInput('');
    } catch (error) {
      console.error('Signout error:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDemoVerify = async () => {
    const trimmedCode = demoIdInput.trim();
    if (!/^\d{12}$/.test(trimmedCode)) {
      Alert.alert('Invalid Demo ID', 'Please enter a valid 12-digit numeric demo ID.');
      return;
    }

    try {
      setActionLoading(true);
      
      // Update database public.users table via backend API
      const updatedProfile = await sakhiApi.verifyDemo(trimmedCode);
      
      if (updatedProfile && updatedProfile.identity_status === 'VERIFIED') {
        setIsVerified(true);
        setShowVerifyFlow(false);
        setDemoIdInput('');
        Alert.alert('Verification Successful', 'Your identity status is now VERIFIED in the database.');
      } else {
        throw new Error('Database status update returned non-verified status.');
      }
    } catch (error: any) {
      console.error('Demo verification error:', error);
      Alert.alert('Verification Failed', error.response?.data?.detail || error.message || 'Failed to update database verification status.');
      setIsVerified(false);
    } finally {
      setActionLoading(false);
    }
  };

  const renderVerifyFlow = () => {
    return (
      <ScrollView style={styles.flexShrink} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        <SakhiText variant="h2" style={styles.title}>Demo Identity Verification</SakhiText>
        <SakhiText variant="body" color="secondary" style={styles.subtitle}>
          Enter a 12-digit demo ID to set your identity status to VERIFIED in the backend database.
        </SakhiText>
        
        <TextInput
          style={styles.inputField}
          placeholder="Enter 12-digit Demo ID"
          keyboardType="number-pad"
          maxLength={12}
          value={demoIdInput}
          onChangeText={setDemoIdInput}
        />

        <SakhiButton
          title={actionLoading ? "Verifying..." : "Verify Identity"}
          onPress={handleDemoVerify}
          style={{ marginTop: 24, width: '100%' }}
          disabled={actionLoading}
          loading={actionLoading}
        />
        <SakhiButton
          title="Cancel"
          variant="secondary"
          onPress={() => setShowVerifyFlow(false)}
          style={{ marginTop: 12, width: '100%' }}
          disabled={actionLoading}
        />
      </ScrollView>
    );
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
            title={actionLoading ? "Signing In..." : "Continue with Google"}
            onPress={handleSignIn}
            style={{ marginTop: 24, width: '100%' }}
            disabled={actionLoading}
            loading={actionLoading}
          />
        </ScrollView>
      );
    }

    if (showVerifyFlow) {
      return renderVerifyFlow();
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
                onPress={() => setShowVerifyFlow(true)}
                style={{ marginTop: 16 }}
              />
            </>
          ) : (
            <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>
              Identity verified.
            </SakhiText>
          )}
        </View>

        <SakhiButton
          title={actionLoading ? "Signing Out..." : "Sign Out"}
          variant="secondary"
          onPress={handleSignOut}
          style={{ marginTop: 24, marginBottom: 16, width: '100%' }}
          disabled={actionLoading}
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
    letterSpacing: 1,
  },
});
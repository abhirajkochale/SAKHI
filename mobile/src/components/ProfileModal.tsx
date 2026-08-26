import React, { useEffect, useState } from 'react';
import { Modal, View, StyleSheet, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform, Alert, ScrollView } from 'react-native';
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

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        setUser(session?.user ?? null);
        
        if (session?.user) {
          try {
            const profile = await sakhiApi.getCurrentUser();
            if (profile.identity_provider) {
              setIsVerified(true);
            }
          } catch (profileError) {
            console.log('User profile not fully initialized yet.');
          }
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

  const handleSignIn = async () => {
    try {
      setActionLoading(true);
      
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: (process.env.EXPO_PUBLIC_APP_ENV === 'development' ? 'sakhi-dev://auth/callback' : 'sakhi://auth/callback'),
          skipBrowserRedirect: true,
        },
      });

      if (!data?.url) throw new Error('No OAuth URL returned');

      const res = await WebBrowser.openAuthSessionAsync(
        data.url,
        (process.env.EXPO_PUBLIC_APP_ENV === 'development' ? 'sakhi-dev://auth/callback' : 'sakhi://auth/callback')
      );

      if (res.type === 'success' && res.url) {
        const urlParams = new URLSearchParams(res.url.split('#')[1]);
        const accessToken = urlParams.get('access_token');
        const refreshToken = urlParams.get('refresh_token');

        if (accessToken && refreshToken) {
          await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });
          const { data: { session } } = await supabase.auth.getSession();
          setUser(session?.user ?? null);
          
          if (session?.user) {
            try {
              const profile = await sakhiApi.getCurrentUser();
              if (profile.identity_provider) setIsVerified(true);
            } catch (e) {}
          }
        }
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
    } catch (error) {
      console.error('Signout error:', error);
    } finally {
      setActionLoading(false);
    }
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
                onPress={() => Alert.alert('Verification', 'Optional future identity-verification enhancement — not implemented.')}
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
});
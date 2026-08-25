import React, { useEffect, useState } from 'react';
import { Modal, View, StyleSheet, TouchableOpacity, ActivityIndicator, KeyboardAvoidingView, Platform, Alert, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { supabase } from '../api/supabase';
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

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
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
        // Supabase returns tokens in the URL fragment (#access_token=...&refresh_token=...)
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

        // Also check query params (?code=...)
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
        {
          text: "Cancel",
          style: "cancel"
        },
        {
          text: "Sign Out",
          style: "destructive",
          onPress: async () => {
            setLoading(true);
            try {
              const { error } = await supabase.auth.signOut();
              if (error) throw error;
              setUser(null); // Optimistically clear state
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
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
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

    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.iconWrapper}>
          <Ionicons name="person-circle" size={80} color="#4F46E5" />
        </View>
        <SakhiText variant="h2" style={styles.title}>{user.user_metadata?.full_name || user.email?.split('@')[0] || 'User'}</SakhiText>
        <SakhiText variant="body" color="secondary" style={styles.subtitle}>{user.email}</SakhiText>

        <View style={styles.statusCard}>
          <View style={styles.statusHeader}>
            <SakhiText variant="h3">Account Status</SakhiText>
            <View style={styles.badgeNormal}>
              <SakhiText variant="caption" style={{ color: '#4F46E5', fontWeight: 'bold' }}>NORMAL USER</SakhiText>
            </View>
          </View>
          <SakhiText variant="subtext" color="secondary" style={{ marginTop: 8 }}>
            Verify your identity to become a trusted safety reporter.
          </SakhiText>
          <SakhiButton
            title="Verify Identity"
            variant="secondary"
            onPress={() => Alert.alert('Coming Soon', 'Aadhaar verification will be added in Phase 2.')}
            style={{ marginTop: 16 }}
          />
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
});

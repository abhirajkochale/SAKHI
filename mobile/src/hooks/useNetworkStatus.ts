import { useState, useEffect } from 'react';
import { NativeModules } from 'react-native';

export interface NetworkStatus {
  isConnected: boolean;
  isInternetReachable: boolean | null;
  isOnline: boolean;
}

export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>({
    isConnected: true,
    isInternetReachable: true,
    isOnline: true,
  });

  useEffect(() => {
    // Prevent top-level module evaluation crash if RNCNetInfo native module is missing from the binary
    if (!NativeModules.RNCNetInfo) {
      return;
    }

    try {
      const NetInfo = require('@react-native-community/netinfo').default;
      if (!NetInfo || typeof NetInfo.fetch !== 'function') return;

      const unsubscribe = NetInfo.addEventListener((state: any) => {
        if (!state) return;
        const isOnline = Boolean(state.isConnected && state.isInternetReachable !== false);
        setStatus({
          isConnected: Boolean(state.isConnected),
          isInternetReachable: state.isInternetReachable,
          isOnline,
        });
      });

      NetInfo.fetch().then((state: any) => {
        if (!state) return;
        const isOnline = Boolean(state.isConnected && state.isInternetReachable !== false);
        setStatus({
          isConnected: Boolean(state.isConnected),
          isInternetReachable: state.isInternetReachable,
          isOnline,
        });
      }).catch(() => {});

      return () => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      };
    } catch (e) {
      console.warn('NetInfo load error:', e);
    }
  }, []);

  return status;
}

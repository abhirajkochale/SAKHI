import { useState, useEffect } from 'react';
import NetInfo from '@react-native-community/netinfo';

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
    const unsubscribe = NetInfo.addEventListener(state => {
      const isOnline = Boolean(state.isConnected && state.isInternetReachable !== false);
      setStatus({
        isConnected: Boolean(state.isConnected),
        isInternetReachable: state.isInternetReachable,
        isOnline,
      });
    });

    // Initial check
    NetInfo.fetch().then(state => {
      const isOnline = Boolean(state.isConnected && state.isInternetReachable !== false);
      setStatus({
        isConnected: Boolean(state.isConnected),
        isInternetReachable: state.isInternetReachable,
        isOnline,
      });
    });

    return () => unsubscribe();
  }, []);

  return status;
}

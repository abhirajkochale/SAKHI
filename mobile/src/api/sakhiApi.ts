import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location, WashroomResponse } from '../types/api';
import { supabase } from './supabase';

// Use Expo environment variable or fallback to localhost
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';


const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(async config => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export const sakhiApi = {
  getErrorMessage: (error: unknown): string => {
    if (axios.isAxiosError(error)) {
      return `API request failed: ${error.config?.method?.toUpperCase()} ${error.config?.url} (${error.code || error.message})`;
    }
    return 'Unable to analyze this journey. Please check both locations and try again.';
  },

  getWashrooms: async (latitude: number, longitude: number, radiusKm: number = 5.0): Promise<WashroomResponse[]> => {
    const response = await apiClient.get<{ washrooms: WashroomResponse[] }>('/washrooms', {
      params: { lat: latitude, lon: longitude, radius_m: radiusKm * 1000 }
    });
    return response.data.washrooms;
  },

  submitWashroomFeedback: async (
    washroomId: string,
    feedback: { is_open: boolean; cleanliness: string; safety: string; accessible: boolean }
  ): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post(`/washrooms/${washroomId}/feedback`, feedback);
    return response.data;
  },

  createJourney: async (origin: Location, destination: Location, departureTime?: string): Promise<JourneyResponse> => {
    const response = await apiClient.post<JourneyResponse>('/journeys/', {
      origin,
      destination,
      departure_time: departureTime,
    });
    return response.data;
  },

  updateContext: async (journeyId: string, event: ContextUpdateEvent): Promise<ContextUpdateResponse> => {
    const response = await apiClient.post<ContextUpdateResponse>(`/journeys/${journeyId}/context-update`, event);
    return response.data;
  },

  submitIncident: async (incident: { segment_id: string; event_type: string; severity: number; latitude: number; longitude: number; description?: string }): Promise<any> => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined;
    const response = await apiClient.post('/incidents/', incident, { headers });
    return response.data;
  },

  triggerSos: async (journeyId: string | null, location: Location): Promise<any> => {
    const response = await axios.post(`${BASE_URL}/emergency/sos`, {
      journey_id: journeyId,
      latitude: location.latitude,
      longitude: location.longitude,
      trigger_source: 'manual',
    });
    return response.data;
  },

  initAadhaarVerification: async (aadhaarNumber: string): Promise<{ reference_id: string }> => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined;
    const response = await apiClient.post('/kyc/aadhaar/init', { aadhaar_number: aadhaarNumber }, { headers });
    return response.data;
  },

  verifyAadhaarOtp: async (referenceId: string, otp: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post('/kyc/aadhaar/verify', { reference_id: referenceId, otp });
    return response.data;
  },

  verifyAadhaarDemo: async (aadhaarNumber: string): Promise<{ status: string; display_name: string }> => {
    const response = await apiClient.post('/kyc/aadhaar/demo', { aadhaar_number: aadhaarNumber });
    return response.data;
  },

  getCurrentUser: async (): Promise<any> => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined;
    const response = await apiClient.get('/users/me', { headers });
    return response.data;
  }
};


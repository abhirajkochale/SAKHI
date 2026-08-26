import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location, WashroomResponse } from '../types/api';
import { supabase } from './supabase';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface CallFriendSettings {
  id?: string;
  user_id?: string;
  caller_name: string;
  source_language_code?: string;
  language_code: string;
  voice_gender: 'Male' | 'Female';
  speaker?: string;
  script: string;
  duration_minutes: number;
}

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
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

  getOsmAmenities: async (lat: number, lon: number, category: 'washroom' | 'police' | 'medical', radius_m: number = 1000): Promise<{ id: string; name: string; address?: string; latitude: number; longitude: number; distance_m: number; opening_hours?: string; phone?: string; source: string; rating?: number | null; rating_count?: number; is_open?: boolean; cleanliness?: string; safety?: string; accessible?: boolean }[]> => {
    try {
      const response = await apiClient.get('/osm-amenities/nearby', { params: { lat, lon, category, radius_m } });
      if (response.data && Array.isArray(response.data)) {
        return response.data;
      }
      return [];
    } catch (e) {
      console.warn(`Failed to fetch OSM amenities for ${category}`, e);
      return [];
    }
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

  getCurrentUser: async (): Promise<any> => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined;
    const response = await apiClient.get('/users/me', { headers });
    return response.data;
  },

  verifyDemo: async (demoCode: string): Promise<any> => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined;
    const response = await apiClient.post('/users/me/verify-demo', { demo_code: demoCode }, { headers });
    return response.data;
  },

  generateCallFriendTts: async (
    text: string = "Hey, where are you? I just wanted to check if you've reached safely.",
    languageCode: string = "en-IN",
    speaker?: string,
    sourceLanguageCode?: string,
    voiceGender: string = "Female"
  ): Promise<{ audio_base64: string; format: string; model: string; translated_text?: string }> => {
    const response = await apiClient.post('/call-friend/tts', {
      text,
      source_language_code: sourceLanguageCode || languageCode,
      language_code: languageCode,
      voice_gender: voiceGender,
      speaker: speaker || undefined,
    });
    return response.data;
  },

  getCallFriendSettings: async (): Promise<CallFriendSettings | null> => {
    try {
      const response = await apiClient.get<CallFriendSettings>('/call-friend/settings');
      return response.data;
    } catch (err: any) {
      if (axios.isAxiosError(err) && (err.response?.status === 404 || err.response?.status === 444)) {
        return null;
      }
      throw err;
    }
  },

  saveCallFriendSettings: async (settings: CallFriendSettings): Promise<CallFriendSettings> => {
    const response = await apiClient.post<CallFriendSettings>('/call-friend/settings', settings);
    return response.data;
  }
};

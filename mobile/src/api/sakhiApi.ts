import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location, PublicToilet } from '../types/api';

// Use Expo environment variable or fallback to localhost
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';


const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sakhiApi = {
  getErrorMessage: (error: unknown): string => {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') return detail;
      if (error.code === 'ECONNABORTED') return 'The journey request timed out. Please try again.';
      if (!error.response) return 'Cannot reach the SAKHI backend. Check that it is running and the device can access it.';
    }
    return 'Unable to analyze this journey. Please check both locations and try again.';
  },

  getPublicToilets: async (): Promise<PublicToilet[]> => {
    const response = await apiClient.get<PublicToilet[]>('/amenities/public-toilets');
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

  triggerSos: async (journeyId: string | null, location: Location): Promise<any> => {
    const response = await axios.post(`${BASE_URL}/emergency/sos`, {
      journey_id: journeyId,
      latitude: location.latitude,
      longitude: location.longitude,
      trigger_source: 'manual',
    });
    return response.data;
  }
};

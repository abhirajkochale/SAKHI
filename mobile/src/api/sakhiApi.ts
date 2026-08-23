import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location, WashroomResponse } from '../types/api';

// Use Expo environment variable or fallback to localhost
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
console.log('AXIOS BASE URL IS:', BASE_URL);


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
    const response = await apiClient.post('/incidents/', incident);
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


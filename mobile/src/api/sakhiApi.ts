import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location } from '../types/api';

// Use Expo environment variable or fallback to localhost
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sakhiApi = {
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
  }
};

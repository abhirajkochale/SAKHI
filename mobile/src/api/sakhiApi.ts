import axios from 'axios';
import { JourneyResponse, ContextUpdateEvent, ContextUpdateResponse, Location, Amenity } from '../types/api';

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

  getNearbyAmenities: async (lat: number, lon: number, radiusM: number = 1000, type: string = 'TOILET'): Promise<Amenity[]> => {
    const response = await apiClient.get<Amenity[]>('/amenities/nearby', {
      params: {
        latitude: lat,
        longitude: lon,
        radius_m: radiusM,
        type,
      },
    });
    return response.data;
  },

  getAmenitiesAlongRoute: async (routeCoords: Location[], deviationM: number = 200, type: string = 'TOILET'): Promise<Amenity[]> => {
    const response = await apiClient.post<Amenity[]>('/amenities/along-route', {
      route_coords: routeCoords,
      deviation_distance_m: deviationM,
      type,
    });
    return response.data;
  },
};

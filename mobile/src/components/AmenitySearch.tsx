import React, { useState, useEffect } from 'react';
import { View, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SakhiText } from './ui/SakhiText';
import { sakhiApi } from '../api/sakhiApi';
import { Location, WashroomResponse } from '../types/api';
import WashroomFacilityCard from './WashroomFacilityCard';

const CP_LOCATIONS = [
  { name: 'Rajiv Chowk Metro Station', coords: { latitude: 28.6328, longitude: 77.2197 } },
  { name: 'Connaught Place Inner Circle', coords: { latitude: 28.6315, longitude: 77.2167 } },
  { name: 'Janpath Market', coords: { latitude: 28.6265, longitude: 77.2195 } },
  { name: 'Palika Bazaar', coords: { latitude: 28.6308, longitude: 77.2185 } },
  { name: 'Parliament Street', coords: { latitude: 28.6253, longitude: 77.2144 } },
  { name: 'Barakhamba Road', coords: { latitude: 28.6340, longitude: 77.2260 } },
  { name: 'Mandi House Metro', coords: { latitude: 28.6258, longitude: 77.2337 } },
];

interface Props {
  category: string;
  onNavigate: (destCoords: Location, originCoords: Location) => void;
}

export default function AmenitySearch({ category, onNavigate }: Props) {
  const [selectedLocation, setSelectedLocation] = useState<typeof CP_LOCATIONS[0] | null>(null);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Results
  const [places, setPlaces] = useState<{ id: string; name: string; address?: string; latitude: number; longitude: number; distance_m: number; opening_hours?: string; phone?: string; source: string; verified_count?: number; last_verified_timestamp?: string; is_open?: boolean; cleanliness?: string; safety?: string; accessible?: boolean; rating?: number | null; rating_count?: number }[]>([]);
  
  // Feedback Modal State
  const [selectedWashroom, setSelectedWashroom] = useState<any | null>(null);

  const getTheme = () => {
    if (category === 'Washroom') return { bg: '#F3E8FF', text: '#7E22CE', title: 'Washrooms', sub: 'Find nearby public washrooms', icon: 'water' as const };
    if (category === 'Medical Clinic') return { bg: '#FCE7F3', text: '#DB2777', title: 'Medical Clinics', sub: 'Find nearby clinics and hospitals', icon: 'add' as const };
    if (category === 'Police Station') return { bg: '#ECFDF5', text: '#059669', title: 'Police Stations', sub: 'Find nearby police stations', icon: 'shield-checkmark' as const };
    return { bg: '#F3F4F6', text: '#374151', title: 'Facilities', sub: 'Find nearby facilities', icon: 'search' as const };
  };

  const theme = getTheme();

  useEffect(() => {
    if (selectedLocation) {
      fetchFacilities(selectedLocation.coords);
    }
  }, [selectedLocation]);

  const fetchFacilities = async (coords: Location) => {
    setLoading(true);
    setErrorMsg(null);
    setPlaces([]);

    try {
      const categoryParam = category === 'Washroom' ? 'washroom' : category === 'Medical Clinic' ? 'medical' : 'police';
      const data = await sakhiApi.getOsmAmenities(coords.latitude, coords.longitude, categoryParam);
      setPlaces(data);
    } catch (err) {
      setErrorMsg('Unable to load nearby facilities. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderPlaces = () => {
    if (places.length === 0) return <SakhiText variant="body" color="secondary" style={styles.emptyText}>No facilities found within 1 km.</SakhiText>;
    
    return places.map((place, index) => {
      const isWashroom = category === 'Washroom';
      
      return (
      <TouchableOpacity 
        key={place.id || index.toString()} 
        style={styles.facilityCard}
        onPress={() => {
          if (isWashroom) {
            setSelectedWashroom({
              id: place.id,
              name: place.name,
              latitude: place.latitude,
              longitude: place.longitude,
              address: place.address,
              verified_count: place.rating_count || 0,
              is_open: place.is_open,
              cleanliness: place.cleanliness,
              safety: place.safety,
              accessible: place.accessible,
            });
          }
        }}
        disabled={!isWashroom}
      >
        <View style={[styles.facilityIconBox, { backgroundColor: theme.bg }]}>
          <Ionicons name={theme.icon} size={24} color={theme.text} />
        </View>
        <View style={styles.facilityInfo}>
          <SakhiText variant="body" style={styles.facilityName}>{place.name}</SakhiText>
          {place.address && <SakhiText variant="caption" color="secondary" style={styles.facilityAddress}>{place.address}</SakhiText>}
          
          {isWashroom && (
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
              {place.rating !== undefined && place.rating !== null ? (
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <Ionicons name="star" size={12} color="#D97706" style={{ marginRight: 2 }} />
                  <SakhiText variant="caption" style={{ color: '#D97706', fontWeight: 'bold' }}>
                    {place.rating}
                  </SakhiText>
                  <SakhiText variant="caption" color="secondary"> • {place.rating_count} ratings</SakhiText>
                </View>
              ) : (
                <SakhiText variant="caption" color="secondary" style={{ fontStyle: 'italic' }}>
                  No ratings yet
                </SakhiText>
              )}
            </View>
          )}

          <View style={styles.facilityMetaRow}>
            {place.opening_hours && <SakhiText variant="caption" color="secondary"><Ionicons name="time-outline" size={12} /> {place.opening_hours} • </SakhiText>}
            {place.phone && <SakhiText variant="caption" color="secondary"><Ionicons name="call-outline" size={12} /> {place.phone} • </SakhiText>}
            <SakhiText variant="caption" color="secondary"> {place.distance_m}m away</SakhiText>
          </View>
        </View>
        <TouchableOpacity style={styles.navBtn} onPress={() => onNavigate({ latitude: place.latitude, longitude: place.longitude }, selectedLocation!.coords)}>
          <Ionicons name="navigate-circle-outline" size={32} color={theme.text} />
        </TouchableOpacity>
      </TouchableOpacity>
    )});
  };

  return (
    <View style={styles.container}>
      <WashroomFacilityCard 
        visible={!!selectedWashroom}
        washroom={selectedWashroom}
        distance={selectedWashroom ? places.find(p => p.id === selectedWashroom.id)?.distance_m || 0 : 0}
        onClose={() => setSelectedWashroom(null)}
        onFeedbackSubmitted={() => fetchFacilities(selectedLocation!.coords)}
      />
      <View style={styles.header}>
        <SakhiText variant="h2" style={styles.title}>{theme.title}</SakhiText>
        <SakhiText variant="subtext" color="secondary" style={styles.subtitle}>{theme.sub}</SakhiText>
      </View>

      <View style={styles.locationSection}>
        <SakhiText variant="caption" color="secondary" style={{ marginBottom: 4 }}>Search near location:</SakhiText>
        <TouchableOpacity 
          style={styles.locationDropdown} 
          onPress={() => setShowLocationPicker(!showLocationPicker)}
        >
          <Ionicons name="location-outline" size={20} color="#8B1E1E" style={{ marginRight: 8 }} />
          <SakhiText variant="body" style={{ flex: 1, color: selectedLocation ? '#1F2937' : '#9CA3AF' }}>
            {selectedLocation ? selectedLocation.name : 'Select a location to search'}
          </SakhiText>
          <Ionicons name="chevron-down" size={20} color="#6B7280" />
        </TouchableOpacity>

        {showLocationPicker && (
          <View style={styles.pickerMenu}>
            <ScrollView style={{ maxHeight: 180 }} nestedScrollEnabled>
              {CP_LOCATIONS.map((loc, idx) => (
                <TouchableOpacity 
                  key={idx} 
                  style={styles.pickerItem} 
                  onPress={() => { setSelectedLocation(loc); setShowLocationPicker(false); }}
                >
                  <Ionicons name="location-outline" size={16} color="#8B1E1E" style={{ marginRight: 8 }} />
                  <SakhiText variant="body" style={{ color: '#1F2937' }}>{loc.name}</SakhiText>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}
      </View>

      <View style={styles.resultsSection}>
        {!selectedLocation ? (
          <View style={styles.emptyStateBox}>
            <Ionicons name="map-outline" size={48} color="#E5E7EB" />
            <SakhiText variant="body" color="secondary" style={{ marginTop: 12 }}>Please select a location above to see nearby facilities.</SakhiText>
          </View>
        ) : loading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={theme.text} />
            <SakhiText variant="body" color="secondary" style={{ marginTop: 12 }}>Finding nearby facilities...</SakhiText>
          </View>
        ) : errorMsg ? (
          <SakhiText variant="body" style={{ color: '#DC2626', textAlign: 'center', marginTop: 24 }}>{errorMsg}</SakhiText>
        ) : (
          <ScrollView style={styles.resultsScroll} showsVerticalScrollIndicator={false}>
            {renderPlaces()}
          </ScrollView>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    color: '#1F2937',
    marginBottom: 4,
  },
  subtitle: {
    textAlign: 'center',
  },
  locationSection: {
    marginBottom: 20,
    zIndex: 10,
  },
  locationDropdown: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: '#F9FAFB',
  },
  pickerMenu: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    marginTop: 4,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    position: 'absolute',
    top: 68,
    left: 0,
    right: 0,
    zIndex: 20,
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  resultsSection: {
    flex: 1,
    minHeight: 200,
  },
  emptyStateBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 32,
  },
  resultsScroll: {
    flex: 1,
  },
  facilityCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  facilityIconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  facilityInfo: {
    flex: 1,
    marginRight: 12,
  },
  facilityName: {
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  facilityAddress: {
    lineHeight: 16,
    marginBottom: 4,
  },
  facilityMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  navBtn: {
    padding: 4,
  }
});

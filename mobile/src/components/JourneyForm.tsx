import React, { useState } from 'react';
import { View, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { Location } from '../types/api';
import { SakhiText } from './ui/SakhiText';
import { Ionicons } from '@expo/vector-icons';

// Real Connaught Place pilot locations from verified datasets
const CP_LOCATIONS: { name: string; coords: Location }[] = [
  { name: 'Rajiv Chowk Metro Station', coords: { latitude: 28.6328, longitude: 77.2197 } },
  { name: 'Connaught Place Inner Circle', coords: { latitude: 28.6315, longitude: 77.2167 } },
  { name: 'Janpath Market', coords: { latitude: 28.6265, longitude: 77.2195 } },
  { name: 'Palika Bazaar', coords: { latitude: 28.6308, longitude: 77.2185 } },
  { name: 'Parliament Street', coords: { latitude: 28.6253, longitude: 77.2144 } },
  { name: 'Barakhamba Road', coords: { latitude: 28.6340, longitude: 77.2260 } },
  { name: 'Mandi House Metro', coords: { latitude: 28.6258, longitude: 77.2337 } },
];

interface Props {
  onAnalyze: (origin: Location, destination: Location, originName: string, destName: string) => void;
  loading: boolean;
  compact?: boolean;
  initialOriginText?: string;
  initialDestinationText?: string;
  initialOrigin?: Location | null;
  initialDestination?: Location | null;
}

export default function JourneyForm({ 
  onAnalyze, 
  loading, 
  compact = false,
  initialOriginText = '',
  initialDestinationText = '',
  initialOrigin = null,
  initialDestination = null
}: Props) {
  const [originText, setOriginText] = useState(initialOriginText);
  const [destinationText, setDestinationText] = useState(initialDestinationText);
  const [origin, setOrigin] = useState<Location | null>(initialOrigin);
  const [destination, setDestination] = useState<Location | null>(initialDestination);
  const [error, setError] = useState<string | null>(null);
  const [showOriginPicker, setShowOriginPicker] = useState(false);
  const [showDestPicker, setShowDestPicker] = useState(false);

  const selectOrigin = (loc: typeof CP_LOCATIONS[0]) => {
    setOriginText(loc.name);
    setOrigin(loc.coords);
    setShowOriginPicker(false);
    setError(null);
  };

  const selectDestination = (loc: typeof CP_LOCATIONS[0]) => {
    setDestinationText(loc.name);
    setDestination(loc.coords);
    setShowDestPicker(false);
    setError(null);
  };

  const handleAnalyze = async () => {
    setError(null);
    if (!origin || !destination) {
      setError("Please select both origin and destination from the list.");
      return;
    }
    if (origin.latitude === destination.latitude && origin.longitude === destination.longitude) {
      setError("Origin and destination cannot be the same.");
      return;
    }
    onAnalyze(origin, destination, originText, destinationText);
  };

  const swapLocations = () => {
    const tempText = originText;
    setOriginText(destinationText);
    setDestinationText(tempText);
    const tempLoc = origin;
    setOrigin(destination);
    setDestination(tempLoc);
  };

  const LocationPicker = ({ onSelect, exclude }: { onSelect: (loc: typeof CP_LOCATIONS[0]) => void; exclude?: string }) => (
    <View style={styles.pickerDropdown}>
      <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled>
        {CP_LOCATIONS.filter(l => l.name !== exclude).map((loc) => (
          <TouchableOpacity key={loc.name} style={styles.pickerItem} onPress={() => onSelect(loc)}>
            <Ionicons name="location-outline" size={16} color="#8B1E1E" style={{ marginRight: 8 }} />
            <SakhiText variant="body" style={{ color: '#1F2937' }}>{loc.name}</SakhiText>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  if (compact) {
    return (
      <View style={styles.compactOuterContainer}>
        {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}
        <View style={styles.compactRow}>
          <View style={[styles.card, styles.compactCard]}>
            <View style={styles.compactGoogleLayout}>
              <View style={styles.compactIconCol}>
                <View style={styles.compactCircleIcon} />
                <Ionicons name="ellipsis-vertical" size={16} color="#9CA3AF" style={{marginVertical: 4}} />
                <View style={styles.compactPinIconOutline}>
                  <View style={styles.compactPinIconDot} />
                </View>
              </View>
              <View style={styles.compactInputCol}>
                <TouchableOpacity onPress={() => { setShowOriginPicker(!showOriginPicker); setShowDestPicker(false); }}>
                  <SakhiText style={[styles.compactInputText, !originText && { color: '#6B7280' }]}>
                    {originText || 'Choose starting point'}
                  </SakhiText>
                </TouchableOpacity>
                <View style={styles.compactDivider} />
                <TouchableOpacity onPress={() => { setShowDestPicker(!showDestPicker); setShowOriginPicker(false); }}>
                  <SakhiText style={[styles.compactInputText, !destinationText && { color: '#6B7280' }]}>
                    {destinationText || 'Choose destination'}
                  </SakhiText>
                </TouchableOpacity>
              </View>
              <View style={styles.compactActionCol}>
                <TouchableOpacity style={{padding: 4}} onPress={swapLocations}>
                  <Ionicons name="swap-vertical" size={24} color="#8B1E1E" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
          <TouchableOpacity 
            style={styles.compactSearchBtn} 
            onPress={handleAnalyze}
            disabled={!origin || !destination || loading}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Ionicons name="search" size={24} color="#ffffff" />
            )}
          </TouchableOpacity>
        </View>
        {showOriginPicker && <LocationPicker onSelect={selectOrigin} exclude={destinationText} />}
        {showDestPicker && <LocationPicker onSelect={selectDestination} exclude={originText} />}
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <View style={styles.headerContainer}>
        <SakhiText variant="h2" style={styles.titleText}>Plan your journey</SakhiText>
        <SakhiText variant="body" style={styles.subtitleText}>Enter your locations to find the safest route.</SakhiText>
      </View>

      {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}

      <View style={styles.inputsWrapper}>
        {/* Left indicators & connector line */}
        <View style={styles.indicatorCol}>
          <View style={styles.originDot} />
          <View style={styles.connectorLine} />
          <Ionicons name="location" size={20} color="#991B1B" />
        </View>

        {/* Input Boxes Column */}
        <View style={styles.fieldsCol}>
          {/* FROM Box */}
          <TouchableOpacity 
            style={[styles.inputBox, showOriginPicker && styles.inputBoxActive]} 
            onPress={() => { setShowOriginPicker(!showOriginPicker); setShowDestPicker(false); }}
          >
            <View style={styles.inputInnerContent}>
              <SakhiText variant="caption" style={styles.fieldLabel}>From</SakhiText>
              <SakhiText style={[styles.fieldValue, !originText && styles.placeholderValue]}>
                {originText || 'Enter starting location'}
              </SakhiText>
            </View>
            <Ionicons name="navigate-outline" size={20} color="#64748B" />
          </TouchableOpacity>
          {showOriginPicker && <LocationPicker onSelect={selectOrigin} exclude={destinationText} />}

          {/* Spacer */}
          <View style={{ height: 12 }} />

          {/* TO Box */}
          <TouchableOpacity 
            style={[styles.inputBox, showDestPicker && styles.inputBoxActive]} 
            onPress={() => { setShowDestPicker(!showDestPicker); setShowOriginPicker(false); }}
          >
            <View style={styles.inputInnerContent}>
              <SakhiText variant="caption" style={styles.fieldLabel}>To</SakhiText>
              <SakhiText style={[styles.fieldValue, !destinationText && styles.placeholderValue]}>
                {destinationText || 'Enter destination'}
              </SakhiText>
            </View>
          </TouchableOpacity>
          {showDestPicker && <LocationPicker onSelect={selectDestination} exclude={originText} />}
        </View>

        {/* Swap Button (Floating on the right) */}
        <TouchableOpacity style={styles.swapBtn} onPress={swapLocations}>
          <Ionicons name="swap-vertical" size={20} color="#8B1E1E" />
        </TouchableOpacity>
      </View>

      {/* Primary CTA */}
      <TouchableOpacity 
        style={[styles.primaryCTA, (!origin || !destination) && styles.disabledCTA]} 
        onPress={handleAnalyze}
        disabled={!origin || !destination || loading}
      >
        {loading ? (
          <ActivityIndicator color="#ffffff" />
        ) : (
          <SakhiText style={styles.ctaText}>FIND SAFEST ROUTE</SakhiText>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 4,
    width: '100%',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  headerContainer: {
    marginBottom: 16,
  },
  titleText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  subtitleText: {
    fontSize: 13,
    color: '#6B7280',
  },
  error: {
    marginBottom: 12,
    textAlign: 'center',
  },
  inputsWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    position: 'relative',
  },
  indicatorCol: {
    width: 28,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    marginRight: 8,
  },
  originDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#991B1B',
  },
  connectorLine: {
    width: 0,
    height: 36,
    borderLeftWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: '#CBD5E1',
    marginVertical: 4,
  },
  fieldsCol: {
    flex: 1,
    marginRight: 16,
  },
  inputBox: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 56,
  },
  inputBoxActive: {
    borderColor: '#8B1E1E',
  },
  inputInnerContent: {
    flex: 1,
  },
  fieldLabel: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 2,
  },
  fieldValue: {
    fontSize: 15,
    color: '#1F2937',
    fontWeight: '500',
  },
  placeholderValue: {
    color: '#94A3B8',
  },
  swapBtn: {
    position: 'absolute',
    right: 0,
    top: '50%',
    marginTop: -20,
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#8B1E1E',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  primaryCTA: {
    backgroundColor: '#8B1E1E', // Dark Maroon
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabledCTA: {
    backgroundColor: '#C56A6A',
  },
  ctaText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  compactOuterContainer: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  compactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
  },
  compactSearchBtn: {
    backgroundColor: '#8B1E1E',
    marginLeft: 8,
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#8B1E1E',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
  },
  compactCard: {
    flex: 1,
    borderRadius: 16,
    padding: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 0,
    marginHorizontal: 0,
  },
  compactGoogleLayout: {
    flexDirection: 'row',
  },
  compactIconCol: {
    width: 32,
    alignItems: 'center',
    paddingTop: 8,
  },
  compactCircleIcon: {
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: '#374151',
    backgroundColor: '#fff',
  },
  compactPinIconOutline: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1.5,
    borderColor: '#8B1E1E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactPinIconDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#8B1E1E',
  },
  compactInputCol: {
    flex: 1,
    paddingHorizontal: 8,
  },
  compactInputText: {
    fontSize: 15,
    color: '#1F2937',
    paddingVertical: 4,
    minHeight: 32,
  },
  compactDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 4,
  },
  compactActionCol: {
    width: 40,
    alignItems: 'center',
    paddingTop: 4,
  },
  pickerDropdown: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    marginTop: 4,
    marginBottom: 8,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
});

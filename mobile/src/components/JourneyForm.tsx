import React, { useState } from 'react';
import { View } from 'react-native';
import { Location } from '../types/api';
import { SakhiCard } from './ui/SakhiCard';
import { SakhiInput } from './ui/SakhiInput';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiText } from './ui/SakhiText';

interface Props {
  onAnalyze: (origin: Location, destination: Location) => void;
  loading: boolean;
}

export default function JourneyForm({ onAnalyze, loading }: Props) {
  const [originText, setOriginText] = useState('');
  const [destinationText, setDestinationText] = useState('');
  const [origin, setOrigin] = useState<Location | null>(null);
  const [destination, setDestination] = useState<Location | null>(null);
  const [geocodeLoading, setGeocodeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const geocodeAddress = async (address: string): Promise<Location | null> => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`, {
        headers: { 'User-Agent': 'SAKHI-Hackathon-App' }
      });
      const data = await res.json();
      if (data && data.length > 0) {
        return { latitude: parseFloat(data[0].lat), longitude: parseFloat(data[0].lon) };
      }
      return null;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    if (!originText || !destinationText) {
      setError("Please enter origin and destination addresses.");
      return;
    }
    
    let currentOrig = origin;
    let currentDest = destination;

    if (!currentOrig) {
      setGeocodeLoading(true);
      currentOrig = await geocodeAddress(originText);
      setGeocodeLoading(false);
      if (!currentOrig) {
        setError(`Could not find location for: ${originText}`);
        return;
      }
      setOrigin(currentOrig);
    }
    
    if (!currentDest) {
      setGeocodeLoading(true);
      currentDest = await geocodeAddress(destinationText);
      setGeocodeLoading(false);
      if (!currentDest) {
        setError(`Could not find location for: ${destinationText}`);
        return;
      }
      setDestination(currentDest);
    }
    
    onAnalyze(currentOrig, currentDest);
  };

  return (
    <SakhiCard elevated style={{ marginBottom: 16 }}>
      {error && <SakhiText color="danger" variant="caption" style={{ marginBottom: 12 }}>{error}</SakhiText>}

      <SakhiInput
        label="FROM"
        placeholder="Enter starting location..."
        value={originText}
        onChangeText={(t) => { setOriginText(t); setOrigin(null); }}
      />

      <SakhiInput
        label="TO"
        placeholder="Enter destination..."
        value={destinationText}
        onChangeText={(t) => { setDestinationText(t); setDestination(null); }}
      />

      <View style={{ marginTop: 8 }}>
        <SakhiButton 
          title="Find Safest Route" 
          variant="primary"
          onPress={handleAnalyze}
          disabled={!originText || !destinationText}
          loading={loading || geocodeLoading}
        />
      </View>
    </SakhiCard>
  );
}

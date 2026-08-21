import * as SQLite from 'expo-sqlite';
import { JourneyResponse } from '../types/api';

const dbPromise = SQLite.openDatabaseAsync('sakhi_cache.db').then(async (db) => {
  await db.execAsync(`
    CREATE TABLE IF NOT EXISTS cached_journeys (
      id TEXT PRIMARY KEY,
      data TEXT NOT NULL,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
  return db;
});

export const initDb = async () => {
  try {
    await dbPromise;
    console.log('Cache DB initialized');
  } catch (e) {
    console.error('Error initializing DB', e);
  }
};

export const cacheJourney = async (journey: JourneyResponse) => {
  try {
    const db = await dbPromise;
    const dataStr = JSON.stringify(journey);
    await db.runAsync(
      `INSERT OR REPLACE INTO cached_journeys (id, data, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)`,
      ['last_journey', dataStr] // we just need to keep the latest journey for the demo
    );
    console.log('Journey cached successfully');
  } catch (e) {
    console.error('Error caching journey', e);
  }
};

export const getCachedJourney = async (): Promise<JourneyResponse | null> => {
  try {
    const db = await dbPromise;
    const result = await db.getFirstAsync<{ data: string }>(`SELECT data FROM cached_journeys WHERE id = 'last_journey'`);
    if (result && result.data) {
      return JSON.parse(result.data) as JourneyResponse;
    }
    return null;
  } catch (e) {
    console.error('Error fetching cached journey', e);
    return null;
  }
};

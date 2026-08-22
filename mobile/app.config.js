const appConfig = require('./app.json');

const googleMapsApiKey = process.env.GOOGLE_MAPS_API_KEY;

if (!googleMapsApiKey) {
  throw new Error('GOOGLE_MAPS_API_KEY is required in mobile/.env to build the Android app.');
}

module.exports = {
  ...appConfig.expo,
  android: {
    ...appConfig.expo.android,
    package: 'com.shounak.sakhi',
  },
  plugins: [
    [
      'react-native-maps',
      {
        androidGoogleMapsApiKey: googleMapsApiKey,
      },
    ],
  ],
};

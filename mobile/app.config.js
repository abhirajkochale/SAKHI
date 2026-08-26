const IS_DEV = process.env.EXPO_PUBLIC_APP_ENV === 'development';

module.exports = {
  name: IS_DEV ? "SAKHI Dev" : "SAKHI",
  slug: "mobile",
  scheme: IS_DEV ? "sakhi-dev" : "sakhi",
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "light",
  ios: {
    supportsTablet: true
  },
  android: {
    adaptiveIcon: {
      backgroundColor: "#E6F4FE",
      foregroundImage: "./assets/android-icon-foreground.png",
      backgroundImage: "./assets/android-icon-background.png",
      monochromeImage: "./assets/android-icon-monochrome.png"
    },
    predictiveBackGestureEnabled: false,
    package: IS_DEV ? "com.sakhi.app.dev" : "com.anonymous.mobile"
  },
  web: {
    favicon: "./assets/favicon.png"
  },
  plugins: [
    "expo-font",
    ["expo-audio", { recordAudioAndroid: false, enableBackgroundPlayback: false }],
    "expo-secure-store",
    "expo-web-browser"
  ]
};

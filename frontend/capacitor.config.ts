import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.oncoai.app',
  appName: 'OncoAI',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
  android: {
    backgroundColor: '#050B1A',
    // The WebView origin is https://localhost; a plain-http dev backend
    // (http://10.0.2.2:8000) is "mixed content". Allowed for dev builds only:
    // release builds run `ONCOAI_RELEASE=1 npx cap sync android` and must use an https API.
    allowMixedContent: process.env.ONCOAI_RELEASE !== '1',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      launchAutoHide: true,
      backgroundColor: '#050B1A',
      showSpinner: false,
      androidScaleType: 'CENTER_INSIDE',
      splashFullScreen: false,
      splashImmersive: false,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#050B1A',
      overlaysWebView: false,
    },
    LocalNotifications: {
      smallIcon: 'ic_stat_oncoai',
      iconColor: '#22D3EE',
    },
  },
};

export default config;

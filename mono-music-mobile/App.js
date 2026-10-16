import React, { useRef, useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  BackHandler,
  Platform,
  SafeAreaView,
  StatusBar as RNStatusBar
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { WebView } from 'react-native-webview';

const MOBILE_PLAYER_URL = 'https://mono-music-778r.vercel.app/mobile';

export default function App() {
  const webViewRef = useRef(null);
  const [canGoBack, setCanGoBack] = useState(false);

  useEffect(() => {
    if (Platform.OS === 'android') {
      const onBackPress = () => {
        if (canGoBack && webViewRef.current) {
          webViewRef.current.goBack();
          return true;
        }
        return false;
      };

      const subscription = BackHandler.addEventListener('hardwareBackPress', onBackPress);
      return () => subscription.remove();
    }
  }, [canGoBack]);

  const renderLoadingView = () => (
    <View style={styles.loadingContainer}>
      <View style={styles.recordCircle}>
        <View style={styles.recordInner} />
      </View>
      <Text style={styles.loadingTitle}>mono Music</Text>
      <Text style={styles.loadingSubtitle}>AUTHENTIC TELUGU AUDIO ENGINE (2000–2026)</Text>
      <ActivityIndicator size="small" color="#faf9f5" style={{ marginTop: 20 }} />
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#111111" />
      <WebView
        ref={webViewRef}
        source={{ uri: MOBILE_PLAYER_URL }}
        style={styles.webview}
        allowsInlineMediaPlayback={true}
        mediaPlaybackRequiresUserAction={false}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        cacheEnabled={true}
        allowFileAccess={true}
        allowsFullscreenVideo={true}
        scalesPageToFit={true}
        startInLoadingState={true}
        renderLoading={renderLoadingView}
        onNavigationStateChange={(navState) => setCanGoBack(navState.canGoBack)}
        applicationNameForUserAgent="monoMusicApp/1.0.0"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111111',
    paddingTop: Platform.OS === 'android' ? RNStatusBar.currentHeight : 0,
  },
  webview: {
    flex: 1,
    backgroundColor: '#111111',
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#111111',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999,
  },
  recordCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#1a1a1a',
    borderWidth: 2,
    borderColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  recordInner: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#faf9f5',
  },
  loadingTitle: {
    color: '#faf9f5',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 22,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  loadingSubtitle: {
    color: '#888888',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 10,
    letterSpacing: 1,
    marginTop: 6,
  },
});

import AsyncStorage from "@react-native-async-storage/async-storage";

const CONSENT_KEY = "crossdressing_app_consent_v1";

export async function hasGivenConsent(): Promise<boolean> {
  const value = await AsyncStorage.getItem(CONSENT_KEY);
  return value === "true";
}

export async function recordConsent(): Promise<void> {
  await AsyncStorage.setItem(CONSENT_KEY, "true");
}

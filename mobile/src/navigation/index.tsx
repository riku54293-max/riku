import React from "react";
import { View, ActivityIndicator } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";
import { hasGivenConsent } from "../consent";
import ConsentScreen from "../screens/ConsentScreen";
import HomeScreen from "../screens/HomeScreen";
import StyleScreen from "../screens/StyleScreen";
import ResultScreen from "../screens/ResultScreen";

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  const [initialRouteName, setInitialRouteName] = React.useState<"Consent" | "Home" | null>(null);

  React.useEffect(() => {
    hasGivenConsent().then((consented) => {
      setInitialRouteName(consented ? "Home" : "Consent");
    });
  }, []);

  if (initialRouteName === null) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator size="large" color="#e8548a" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={initialRouteName} screenOptions={{ headerTitleAlign: "center" }}>
        <Stack.Screen name="Consent" component={ConsentScreen} options={{ title: "ご利用にあたって", headerBackVisible: false }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: "写真を選択" }} />
        <Stack.Screen name="Style" component={StyleScreen} options={{ title: "スタイル選択" }} />
        <Stack.Screen name="Result" component={ResultScreen} options={{ title: "結果" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

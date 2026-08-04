import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";
import HomeScreen from "../screens/HomeScreen";
import StyleScreen from "../screens/StyleScreen";
import ResultScreen from "../screens/ResultScreen";

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerTitleAlign: "center" }}>
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: "写真を選択" }} />
        <Stack.Screen name="Style" component={StyleScreen} options={{ title: "スタイル選択" }} />
        <Stack.Screen name="Result" component={ResultScreen} options={{ title: "結果" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

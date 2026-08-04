import React from "react";
import { View, Text, Image, TouchableOpacity, StyleSheet } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";

type Props = NativeStackScreenProps<RootStackParamList, "Result">;

export default function ResultScreen({ route, navigation }: Props) {
  const { resultImage } = route.params;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>変換結果</Text>
      <Image source={{ uri: resultImage }} style={styles.result} resizeMode="contain" />
      <TouchableOpacity
        style={styles.button}
        onPress={() => navigation.navigate("Home")}
      >
        <Text style={styles.buttonText}>もう一度作る</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 16 },
  result: { width: "100%", aspectRatio: 3 / 4, borderRadius: 12, marginBottom: 24, backgroundColor: "#eee" },
  button: {
    backgroundColor: "#e8548a",
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  buttonText: { color: "#fff", fontWeight: "600", fontSize: 16 },
});

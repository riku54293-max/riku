import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert, Image } from "react-native";
import * as ImagePicker from "expo-image-picker";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

export default function HomeScreen({ navigation }: Props) {
  const [previewUri, setPreviewUri] = React.useState<string | null>(null);

  const pickFromLibrary = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("権限が必要です", "写真ライブラリへのアクセスを許可してください");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
      allowsEditing: true,
      aspect: [3, 4],
    });
    if (!result.canceled && result.assets[0]) {
      setPreviewUri(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("権限が必要です", "カメラへのアクセスを許可してください");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      quality: 0.9,
      allowsEditing: true,
      aspect: [3, 4],
    });
    if (!result.canceled && result.assets[0]) {
      setPreviewUri(result.assets[0].uri);
    }
  };

  const proceed = () => {
    if (!previewUri) return;
    navigation.navigate("Style", { photoUri: previewUri });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>写真を選択してください</Text>
      <Text style={styles.subtitle}>
        ご本人の写真のみアップロードできます。アップロードされた写真はセキュリティスキャンと
        再エンコードを経てから処理されます。
      </Text>

      {previewUri && <Image source={{ uri: previewUri }} style={styles.preview} />}

      <TouchableOpacity style={styles.button} onPress={takePhoto}>
        <Text style={styles.buttonText}>カメラで撮影</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={pickFromLibrary}>
        <Text style={styles.buttonText}>ライブラリから選択</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.primaryButton, !previewUri && styles.disabledButton]}
        onPress={proceed}
        disabled={!previewUri}
      >
        <Text style={styles.buttonText}>スタイルを選ぶ</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: "center", gap: 12 },
  title: { fontSize: 22, fontWeight: "700", textAlign: "center" },
  subtitle: { fontSize: 13, color: "#666", textAlign: "center", marginBottom: 16 },
  preview: { width: "100%", aspectRatio: 3 / 4, borderRadius: 12, marginBottom: 16 },
  button: {
    backgroundColor: "#f2a6c1",
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  primaryButton: { backgroundColor: "#e8548a", marginTop: 8 },
  disabledButton: { opacity: 0.4 },
  buttonText: { color: "#fff", fontWeight: "600", fontSize: 16 },
});

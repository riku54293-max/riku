import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";
import { recordConsent } from "../consent";

type Props = NativeStackScreenProps<RootStackParamList, "Consent">;

function CheckboxRow({
  checked,
  onToggle,
  label,
}: {
  checked: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <TouchableOpacity style={styles.checkboxRow} onPress={onToggle}>
      <View style={[styles.checkbox, checked && styles.checkboxChecked]}>
        {checked && <Text style={styles.checkmark}>✓</Text>}
      </View>
      <Text style={styles.checkboxLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

export default function ConsentScreen({ navigation }: Props) {
  const [isAdult, setIsAdult] = React.useState(false);
  const [isOwnPhoto, setIsOwnPhoto] = React.useState(false);

  const canProceed = isAdult && isOwnPhoto;

  const proceed = async () => {
    if (!canProceed) return;
    await recordConsent();
    navigation.replace("Home");
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>ご利用にあたって</Text>
      <Text style={styles.body}>
        このアプリは、アップロードされた写真にAIでメイク・ヘア・スタイリングを施した画像を
        生成します。ご利用前に以下をご確認ください。
      </Text>
      <Text style={styles.bullet}>・アップロードできるのはご自身の写真のみです</Text>
      <Text style={styles.bullet}>・生成された画像には透かしとAI生成である旨のメタデータが付与されます</Text>
      <Text style={styles.bullet}>・アップロードされた写真と生成画像は処理完了後に削除されます</Text>

      <View style={styles.checkboxGroup}>
        <CheckboxRow checked={isAdult} onToggle={() => setIsAdult((v) => !v)} label="私は18歳以上です" />
        <CheckboxRow
          checked={isOwnPhoto}
          onToggle={() => setIsOwnPhoto((v) => !v)}
          label="アップロードする写真は私自身のものであり、第三者の写真は使用しません"
        />
      </View>

      <TouchableOpacity
        style={[styles.button, !canProceed && styles.buttonDisabled]}
        onPress={proceed}
        disabled={!canProceed}
      >
        <Text style={styles.buttonText}>同意して始める</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingTop: 64, paddingBottom: 48 },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 16, textAlign: "center" },
  body: { fontSize: 14, color: "#444", lineHeight: 20, marginBottom: 12 },
  bullet: { fontSize: 13, color: "#555", marginBottom: 6 },
  checkboxGroup: { marginTop: 24, marginBottom: 24, gap: 16 },
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: "#e8548a",
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: { backgroundColor: "#e8548a" },
  checkmark: { color: "#fff", fontSize: 14, fontWeight: "700" },
  checkboxLabel: { flex: 1, fontSize: 14, color: "#222" },
  button: {
    backgroundColor: "#e8548a",
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  buttonDisabled: { opacity: 0.4 },
  buttonText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});

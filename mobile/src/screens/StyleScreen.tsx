import React from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList, TransformationParams } from "../types";
import OptionPicker from "../components/OptionPicker";
import { transformPhoto } from "../api/client";

type Props = NativeStackScreenProps<RootStackParamList, "Style">;

const MAKEUP_STYLES = ["清楚系ナチュラル", "韓国系(オルチャン)", "モード系", "ゴージャス", "パーティー"];
const HAIR_LENGTHS = ["ショート", "ボブ", "ミディアム", "ロング"];
const UNDERTONES = ["イエベ春", "イエベ秋", "ブルベ夏", "ブルベ冬"];
const STYLE_CONCEPTS = ["清楚系", "モード系", "ロリータ系", "OL系", "カジュアル系", "ゴージャス系"];

// パーソナルカラー(シーズン)に応じたメイク・ヘアカラーのデフォルト値
const SEASON_DEFAULTS: Record<string, Partial<TransformationParams>> = {
  イエベ春: { eyeshadowPalette: "コーラル×アイボリー", lipColor: "コーラルピンク", hairColor: "暖かみのあるブラウン" },
  イエベ秋: { eyeshadowPalette: "テラコッタ×ブラウン", lipColor: "ブリックレッド", hairColor: "カーキブラウン" },
  ブルベ夏: { eyeshadowPalette: "ラベンダー×グレージュ", lipColor: "ローズピンク", hairColor: "アッシュブラウン" },
  ブルベ冬: { eyeshadowPalette: "モノトーン×ボルドー", lipColor: "ボルドーレッド", hairColor: "ダークアッシュ" },
};

export default function StyleScreen({ route, navigation }: Props) {
  const { photoUri } = route.params;
  const [makeupStyle, setMakeupStyle] = React.useState(MAKEUP_STYLES[0]);
  const [hairLength, setHairLength] = React.useState(HAIR_LENGTHS[2]);
  const [undertone, setUndertone] = React.useState(UNDERTONES[0]);
  const [styleConcept, setStyleConcept] = React.useState(STYLE_CONCEPTS[0]);
  const [loading, setLoading] = React.useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const params: Partial<TransformationParams> = {
        makeupStyle,
        hairLength,
        undertone,
        styleConcept,
        ...SEASON_DEFAULTS[undertone],
      };
      const resultImage = await transformPhoto(photoUri, params);
      navigation.navigate("Result", { resultImage });
    } catch (error) {
      Alert.alert("エラー", error instanceof Error ? error.message : "変換に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>スタイルを選択</Text>

      <OptionPicker label="メイクスタイル" options={MAKEUP_STYLES} value={makeupStyle} onChange={setMakeupStyle} />
      <OptionPicker label="髪の長さ" options={HAIR_LENGTHS} value={hairLength} onChange={setHairLength} />
      <OptionPicker label="パーソナルカラー" options={UNDERTONES} value={undertone} onChange={setUndertone} />
      <OptionPicker label="全体コンセプト" options={STYLE_CONCEPTS} value={styleConcept} onChange={setStyleConcept} />

      <TouchableOpacity style={styles.submitButton} onPress={submit} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>変換する</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, paddingBottom: 48 },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 20, textAlign: "center" },
  submitButton: {
    backgroundColor: "#e8548a",
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
    marginTop: 8,
  },
  submitText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});

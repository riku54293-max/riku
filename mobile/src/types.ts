export interface TransformationParams {
  skinFinish: string;
  browStyle: string;
  eyeshadowPalette: string;
  eyelinerShape: string;
  cheekPosition: string;
  lipColor: string;
  lipFinish: string;
  makeupStyle: string;
  hairLength: string;
  hairColor: string;
  undertone: string;
  styleConcept: string;
}

export interface DetectedPersonalColor {
  season: string;
  confidence: number;
}

export type RootStackParamList = {
  Consent: undefined;
  Home: undefined;
  Style: { photoUri: string };
  Result: { resultImage: string; detectedPersonalColor?: DetectedPersonalColor };
};

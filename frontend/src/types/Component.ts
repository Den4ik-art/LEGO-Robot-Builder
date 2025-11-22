// src/types/Component.ts
export interface LegoComponent {
  id: number;
  name: string;
  category: string;
  price: number;
  weight: number;

  // те, що вже було
  efficiency?: number;
  torque?: number;
  speed?: number;
  stability?: number;
  image?: string;

  // опційні розширені поля (з бекенда)
  lego_number?: string;
  family?: string;
  system_type?: string;
  color?: string;
  material?: string;

  geometry?: any;
  connectors?: any[];
  roles?: string[];
  primary_role?: string;

  mechanical?: any;
  electronics?: any;
  constraints?: any;
  compatibility?: any;
  scores?: any;
  inventory?: any;

  domain?: string;
}

// Новий, розширений запит конфігурації
export interface ConfigRequest {
  functions: string[];
  subFunctions?: Record<string, string>;
  budget: number;
  weight: number;
  priority: string;
  sensors: string[];

  // 🔽 Нові поля опитування (такі ж, як у бекенда)

  terrain?: "indoor" | "outdoor_flat" | "offroad" | "water_pool";
  sizeClass?: "small" | "medium" | "large";
  maxDimensions?: {
    lengthStuds?: number;
    widthStuds?: number;
    heightPlates?: number;
  };

  complexityLevel?: 1 | 2 | 3;
  powerProfile?: "long_runtime" | "balanced" | "performance";

  decorationLevel?: "minimal" | "normal" | "rich";
  preferredColors?: string[];

  ownedSets?: string[];
  useOnlyOwnedParts?: boolean;
}

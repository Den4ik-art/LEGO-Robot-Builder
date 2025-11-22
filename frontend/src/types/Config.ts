import type { LegoComponent } from "./Component";

export interface LegoConfigRequest {
  maxWeight: number;
  maxBudget: number;
  requiredFunctions: string[];
}

export interface LegoConfigResponse {
  optimalSet: LegoComponent[];
  totalWeight: number;
  totalPrice: number;
  efficiencyScore: number;
}

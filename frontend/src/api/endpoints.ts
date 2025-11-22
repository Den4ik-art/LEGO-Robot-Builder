import { apiFetch } from "./client";
import { API_BASE_URL } from "./config";
import type { LegoComponent } from "../types/Component";
import type { LegoConfigRequest, LegoConfigResponse } from "../types/Config";

export async function getComponents(): Promise<LegoComponent[]> {
  return apiFetch(`${API_BASE_URL}/components`);
}

export async function generateConfig(data: LegoConfigRequest): Promise<LegoConfigResponse> {
  return apiFetch(`${API_BASE_URL}/config`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

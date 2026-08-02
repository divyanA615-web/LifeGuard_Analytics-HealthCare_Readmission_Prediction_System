import axios, { AxiosInstance } from "axios";

const apiBase =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.DEV ? "/v1" : "/v1");

// Ensure no trailing slash mismatch
const normalizedBase = apiBase.endsWith("/")
  ? apiBase.slice(0, -1)
  : apiBase;

export const api: AxiosInstance = axios.create({
  baseURL: normalizedBase,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("lifeguard_auth_token");
  if (token && config.headers) {
    (config.headers as Record<string, string>)["Authorization"] =
      `Bearer ${token}`;
  }
  return config;
});

export interface PredictResponse {
  request_id: string;
  patient_token: string;
  risk_proba: number;
  risk_label: "LOW" | "MEDIUM" | "HIGH";
  explanation: { feature: string; value: number; contribution: number }[];
  model_version: string;
  latency_ms: number;
  humane_explanation?: string;
  similar_patients?: { patient_token: string; similarity: number }[];
}

export const predictPatient = (payload: unknown) =>
  api.post<PredictResponse>("/predict", payload).then((r) => r.data);

export const fetchHistory = (token: string, limit = 20) =>
  api
    .get<{ patient_token: string; predictions: unknown[] }>(`/patients/${token}/history`, {
      params: { limit },
    })
    .then((r) => r.data);

export const submitFeedback = (
  prediction_id: number,
  payload?: unknown
) => {
  const body =
    payload && typeof payload === "object" && !Array.isArray(payload)
      ? { prediction_id, ...(payload as Record<string, unknown>) }
      : { prediction_id };
  return api.post("/feedback", body).then((r) => r.data);
};

export const fetchModelInfo = () =>
  api.get("/model/info").then((r) => r.data);

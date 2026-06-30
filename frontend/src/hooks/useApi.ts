import axios, { AxiosInstance } from "axios";

const apiBase = import.meta.env.VITE_API_BASE ?? "/v1";

export const api: AxiosInstance = axios.create({
  baseURL: apiBase,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const headers: Record<string, string> = {};
  config.headers = config.headers ?? {};
  Object.entries(headers).forEach(
    ([k, v]) => ((config.headers as Record<string, string>)[k] = v)
  );
  return config;
});

export interface PredictResponse {
  request_id: string;
  patient_token: string;
  risk_proba: number;
  risk_label: "LOW" | "MEDIUM" | "HIGH": string | "HIGH";
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

export const submitFeedback = (prediction_id: number, payload: unknown) =>
  api.post("/feedback", { prediction_id, ...payload }).then((r) => r.data);

export const fetchModelInfo = () =>
  api.get("/model/info").then((r) => r.data);

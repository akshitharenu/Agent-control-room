import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const getRuns = () => API.get("/runs/");
export const getRunDetail = (id: string) => API.get(`/runs/${id}`);
export const deleteRun = (id: string) => API.delete(`/runs/${id}`);
export const getReplay = (id: string) => API.get(`/replay/${id}`);
export const getQuality = (id: string) => API.get(`/quality/${id}`);
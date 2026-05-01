import axios from "axios";

const API = axios.create({
  baseURL: "https://agent-backend-ym1n.onrender.com",
});

export const getRuns = () => API.get("/runs/");
export const getRunDetail = (id: string) => API.get(`/runs/${id}`);
export const deleteRun = (id: string) => API.delete(`/runs/${id}`);
export const getReplay = (id: string) => API.get(`/replay/${id}`);
export const getQuality = (id: string) => API.get(`/quality/${id}`);
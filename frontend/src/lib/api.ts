import axios from "axios";

// Fallback to localhost:8000/api if the env var is not set
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Helper to get the root backend URL (e.g., http://localhost:8000)
// This is useful for prepending to relative image paths returned by the backend
export const getBackendRoot = () => {
  return API_BASE_URL.replace(/\/api$/, "");
};

export default api;

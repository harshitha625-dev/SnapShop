import { useState } from "react";
import api from "@/lib/api";
import toast from "react-hot-toast";

interface SearchPayload {
  image_url:   string;
  image_hash:  string;
  max_results?: number;
}

export default function useImageSearch() {
  const [results, setResults] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const search = async (payload: SearchPayload, category: string = "") => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const { data } = await api.post("/search", {
        ...payload,
        max_results: payload.max_results ?? 20,
        category: category || undefined,
      });
      setResults(data);
      if (data.cached) toast("⚡ Instant — served from cache");
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Search failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const searchByText = async (query: string, category: string = "", max_results = 20) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const { data } = await api.post("/search/text", {
        query,
        max_results,
        category: category || undefined,
      });
      setResults(data);
      if (data.cached) toast("⚡ Instant — served from cache");
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? "Text search failed";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return { results, loading, error, search, searchByText };
}
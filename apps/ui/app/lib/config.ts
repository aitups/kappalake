export const CONFIG = {
  // Client-side URL (browser access) - Fallback for client components if needed
  PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  
  // Server-side URL (internal docker network)
  // Inside Docker, 'api' is the hostname of the service
  INTERNAL_API_URL: process.env.API_URL || "http://api:8000",
  
  ENDPOINTS: {
    GENERATE_PIPELINE: "/ai/generate_pipeline",
  },
};

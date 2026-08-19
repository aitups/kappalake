export const CONFIG = {
  // Client-side URL (browser access) - Fallback for client components if needed
  PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  
  // Server-side URL (internal docker network)
  // Inside Docker, 'api' is the hostname of the service
  INTERNAL_API_URL: process.env.API_URL || "http://api:8000",
  
  // Keycloak OIDC (browser-facing URL vs internal server URL)
  KC_CLIENT_ID: process.env.KC_CLIENT_ID || "kappalake-ui",
  KC_REDIRECT_URI: process.env.KC_REDIRECT_URI || "http://localhost:3001/api/auth/callback",
  KC_ISSUER: process.env.KC_ISSUER || "http://localhost:8180/realms/kappalake",
  KC_ISSUER_INTERNAL: process.env.KC_ISSUER_INTERNAL || "http://keycloak:8080/realms/kappalake",

  ENDPOINTS: {

    GENERATE_PIPELINE: "/ai/generate_pipeline",
    EXECUTE: "/ai/execute",
    AGENT_RUN: "/agent/run",
  },
};

import { CONFIG } from "../lib/config";

export default function LoginPage() {
  const params = new URLSearchParams({
    response_type: "code",
    client_id: CONFIG.KC_CLIENT_ID,
    redirect_uri: CONFIG.KC_REDIRECT_URI,
    scope: "openid profile email",
    state: "kappalake",
  });
  const authUrl = `${CONFIG.KC_ISSUER}/protocol/openid-connect/auth?${params.toString()}`;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-100">
      <div className="w-full max-w-md rounded-xl border bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">KappaLake</h1>
        <p className="mt-2 text-sm text-gray-500">Sign in to the data copilot</p>
        <a
          href={authUrl}
          className="mt-6 inline-flex h-11 w-full items-center justify-center rounded-md bg-blue-600 px-6 text-sm font-medium text-white hover:bg-blue-700"
        >
          Sign in with Keycloak
        </a>
        <p className="mt-4 text-xs text-gray-400">Demo user: demo / demo1234</p>
      </div>
    </main>
  );
}

import ChatInterface from "./components/ChatInterface";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-100">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex mb-8">
        <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
          KappaLake <span className="text-blue-600">Copilot</span>
          </h1>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <p className="text-gray-500">Powered by Trino & LLM</p>
        </div>
        </div>

      <ChatInterface />
      </main>
  );
}

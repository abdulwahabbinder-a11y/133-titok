const ERROR_MESSAGES = {
  invalid: "Invalid username or password. Please try again.",
  missing: "Please enter both username and password.",
  failed: "Login failed. Please try again.",
};

/**
 * Server-rendered login form — uses native HTML POST (no JavaScript required).
 */
export default function AdminLogin({ error }) {
  const errorMessage = ERROR_MESSAGES[error] || null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gray-900">
            <svg
              className="h-6 w-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Admin Portal</h1>
          <p className="mt-1 text-sm text-gray-500">Sign in to manage site configuration</p>
        </div>

        <form action="/api/admin/login" method="POST" className="space-y-4">
          <div>
            <label htmlFor="username" className="mb-1 block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              defaultValue="admin"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              required
              autoComplete="username"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              required
              autoComplete="current-password"
              placeholder="password123"
            />
          </div>

          {errorMessage && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{errorMessage}</p>
          )}

          <button
            type="submit"
            className="w-full rounded-lg bg-gray-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-gray-800"
          >
            Sign In
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-400">
          Default: admin / password123
        </p>
      </div>
    </div>
  );
}

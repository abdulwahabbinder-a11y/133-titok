import { isAuthenticated } from "@/lib/auth";
import { getAdminConfig } from "@/lib/config";
import AdminLogin from "@/components/AdminLogin";
import { AdminDashboard } from "@/components/AdminPanel";

export const dynamic = "force-dynamic";

/**
 * Admin portal — protected by a lightweight session gate reading from config.json.
 */
export default async function AdminPortalPage({ searchParams }) {
  const params = await searchParams;
  const authenticated = await isAuthenticated();

  if (!authenticated) {
    return <AdminLogin error={params?.error} />;
  }

  const initialConfig = { ...getAdminConfig(), adminPassword: "" };

  return <AdminDashboard initialConfig={initialConfig} />;
}

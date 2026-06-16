import { isAuthenticated } from "@/lib/auth";
import { getConfig } from "@/lib/config";
import { AdminLogin, AdminDashboard } from "@/components/AdminPanel";

export const dynamic = "force-dynamic";

/**
 * Admin portal — protected by a lightweight session gate reading from config.json.
 */
export default async function AdminPortalPage() {
  const authenticated = await isAuthenticated();

  if (!authenticated) {
    return <AdminLogin />;
  }

  const config = getConfig();

  const initialConfig = {
    googleAnalyticsId: config.googleAnalyticsId,
    searchConsoleMeta: config.searchConsoleMeta,
    adsTxtContent: config.adsTxtContent,
    topBannerAdCode: config.topBannerAdCode,
    bottomBannerAdCode: config.bottomBannerAdCode,
    adminUsername: config.adminUsername,
    adminPassword: "",
  };

  return <AdminDashboard initialConfig={initialConfig} />;
}

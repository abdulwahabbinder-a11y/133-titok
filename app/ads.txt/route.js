import { getConfig } from "@/lib/config";

export const dynamic = "force-dynamic";

/**
 * GET /ads.txt
 * Serves dynamic ads.txt content from the localized config file.
 */
export async function GET() {
  const { adsTxtContent } = getConfig();

  return new Response(adsTxtContent || "", {
    status: 200,
    headers: {
      "Content-Type": "text/plain",
    },
  });
}

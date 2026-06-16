import axios from "axios";
import { NextResponse } from "next/server";
import { getConfig } from "@/lib/config";
import {
  detectPlatform,
  normalizeUrl,
  getPlatformCredentials,
  resolveApiEndpoint,
  normalizeApiResponse,
} from "@/lib/platform";

export const dynamic = "force-dynamic";

const PLATFORM_LABELS = {
  tiktok: "TikTok",
  instagram: "Instagram",
  facebook: "Facebook",
};

/**
 * POST /api/download
 * Multi-platform downloader — routes to isolated API configs per social network.
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const { url } = body;

    if (!url?.trim()) {
      return NextResponse.json({ error: "Please paste a video URL." }, { status: 400 });
    }

    const platform = detectPlatform(url);

    if (!platform) {
      return NextResponse.json(
        {
          error:
            "Unsupported URL. Please provide a valid TikTok, Instagram, or Facebook video link.",
        },
        { status: 400 }
      );
    }

    const config = getConfig();
    const credentials = getPlatformCredentials(platform, config);
    const endpoint = resolveApiEndpoint(credentials.apiUrl, credentials.apiHost);

    if (!credentials.apiKey || !endpoint) {
      return NextResponse.json(
        {
          error: `${PLATFORM_LABELS[platform]} download is not configured. Please contact the administrator.`,
        },
        { status: 503 }
      );
    }

    const normalizedUrl = normalizeUrl(url);
    const apiHost = credentials.apiHost.replace(/^https?:\/\//, "");

    const response = await axios.get(endpoint, {
      params: { url: normalizedUrl, hd: "1" },
      headers: {
        "x-rapidapi-key": credentials.apiKey,
        "x-rapidapi-host": apiHost,
      },
      timeout: 30000,
    });

    const result = normalizeApiResponse(platform, response.data);

    if (!result) {
      return NextResponse.json(
        { error: "Unable to fetch video data. The link may be private or expired." },
        { status: 422 }
      );
    }

    if (!result.mp4 && !result.mp3) {
      return NextResponse.json(
        { error: "No downloadable media found for this video." },
        { status: 422 }
      );
    }

    return NextResponse.json(result);
  } catch (error) {
    const status = error.response?.status;
    const message =
      status === 429
        ? "Too many requests. Please wait a moment and try again."
        : status === 403
          ? "API access denied. Please verify platform API credentials in the admin panel."
          : "Failed to process the video. Please verify the URL and try again.";

    console.error("[/api/download]", error.message);
    return NextResponse.json({ error: message }, { status: status || 500 });
  }
}

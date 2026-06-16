import axios from "axios";
import { NextResponse } from "next/server";
import { isValidTikTokUrl, normalizeTikTokUrl } from "@/lib/tiktok";

export const dynamic = "force-dynamic";

/**
 * POST /api/download
 * Validates a TikTok URL and fetches video metadata via RapidAPI.
 */
export async function POST(request) {
  try {
    const body = await request.json();
    const { url } = body;

    if (!url || !isValidTikTokUrl(url)) {
      return NextResponse.json(
        { error: "Please provide a valid TikTok video URL." },
        { status: 400 }
      );
    }

    const apiKey = process.env.RAPIDAPI_KEY;
    const apiHost =
      process.env.RAPIDAPI_HOST || "tiktok-video-no-watermark2.p.rapidapi.com";

    if (!apiKey) {
      return NextResponse.json(
        { error: "Download service is not configured. Please contact the administrator." },
        { status: 503 }
      );
    }

    const normalizedUrl = normalizeTikTokUrl(url);

    const response = await axios.get(`https://${apiHost}/`, {
      params: { url: normalizedUrl, hd: "1" },
      headers: {
        "x-rapidapi-key": apiKey,
        "x-rapidapi-host": apiHost,
      },
      timeout: 30000,
    });

    const payload = response.data?.data || response.data;

    if (!payload) {
      return NextResponse.json(
        { error: "Unable to fetch video data. The link may be private or expired." },
        { status: 422 }
      );
    }

    const title = payload.title || payload.desc || "TikTok Video";
    const thumbnail = payload.cover || payload.origin_cover || payload.thumbnail || "";
    const mp4Url = payload.play || payload.hdplay || payload.wmplay || "";
    const mp3Url = payload.music || payload.music_info?.play || "";

    if (!mp4Url && !mp3Url) {
      return NextResponse.json(
        { error: "No downloadable media found for this video." },
        { status: 422 }
      );
    }

    return NextResponse.json({
      title,
      thumbnail,
      mp4: mp4Url,
      mp3: mp3Url,
    });
  } catch (error) {
    const status = error.response?.status;
    const message =
      status === 429
        ? "Too many requests. Please wait a moment and try again."
        : "Failed to process the video. Please verify the URL and try again.";

    console.error("[/api/download]", error.message);
    return NextResponse.json({ error: message }, { status: status || 500 });
  }
}

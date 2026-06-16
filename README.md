# TikTok Video Downloader

A production-ready, ultra-lightweight TikTok video downloader built with **Next.js (App Router)** and **Tailwind CSS**. Inspired by Ssstik.io — optimized for Google PageSpeed, AdSense compliance, and static-first rendering.

## Features

- **No-watermark MP4 & MP3 downloads** via RapidAPI integration
- **Localized JSON config** (`data/config.json`) for analytics, ads, and admin credentials
- **Dynamic `/ads.txt`** route for Google AdSense
- **Admin portal** at `/admin-portal` for managing all site settings
- **SEO-optimized** with FAQ schema markup, semantic HTML, and system fonts
- **Zero external font dependencies** — uses native system sans-serif stack

## Quick Start

```bash
npm install
cp .env.example .env.local
# Add your RapidAPI key to .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

| Variable | Description |
|---|---|
| `RAPIDAPI_KEY` | Your RapidAPI key for TikTok downloader |
| `RAPIDAPI_HOST` | API host (default: `tiktok-video-no-watermark2.p.rapidapi.com`) |
| `ADMIN_SESSION_SECRET` | Secret for signing admin session cookies |

## Admin Portal

Navigate to `/admin-portal` and sign in with the default credentials:

- **Username:** `admin`
- **Password:** `password123`

Change these immediately in production via the admin dashboard.

## Configuration

All site settings are stored in `data/config.json`:

- Google Analytics GA4 tracking ID
- Google Search Console verification meta content
- `ads.txt` plain-text content
- Top and bottom banner ad codes
- Admin credentials

## Deployment

```bash
npm run build
npm start
```

The app uses static-first rendering for the homepage SEO content with dynamic API routes for downloads and admin operations.

## License

MIT

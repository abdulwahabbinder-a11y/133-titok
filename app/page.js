import { getConfig } from "@/lib/config";
import DownloadForm from "@/components/DownloadForm";
import FAQ, { getFaqSchema } from "@/components/FAQ";
import Footer from "@/components/Footer";

const STEPS = [
  {
    step: "1",
    title: "Copy Link",
    description: "Open TikTok, tap Share on any video, and copy the video link.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
      </svg>
    ),
  },
  {
    step: "2",
    title: "Paste Here",
    description: "Paste the copied URL into the input field on this page.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v9.75c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
      </svg>
    ),
  },
  {
    step: "3",
    title: "Download",
    description: "Click Download and save the video in MP4 or MP3 format instantly.",
    icon: (
      <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
    ),
  },
];

const FEATURES = [
  {
    title: "No Watermark",
    description:
      "Download clean TikTok videos without the TikTok logo or username overlay. Perfect for reposting or personal archives.",
    icon: (
      <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: "Ultra HD Quality",
    description:
      "Get the highest available resolution directly from TikTok's CDN. Crystal-clear video and audio every time.",
    icon: (
      <svg className="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    title: "Unlimited Downloads",
    description:
      "No daily limits, no queues, no sign-up. Download as many TikTok videos and audio tracks as you need, completely free.",
    icon: (
      <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
  },
];

export default function HomePage() {
  const { topBannerAdCode, bottomBannerAdCode } = getConfig();

  return (
    <>
      {/* FAQ Rich Snippet JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(getFaqSchema()) }}
      />

      {/* Hero — First Fold */}
      <header className="bg-white px-4 pb-10 pt-12 shadow-sm">
        <div className="mx-auto max-w-3xl text-center">
          {/* Logo */}
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-emerald-500 shadow-lg">
            <svg className="h-9 w-9 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.78 1.52V6.76a4.85 4.85 0 01-1.01-.07z" />
            </svg>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">
            TikTok Video Downloader Without Watermark
          </h1>
          <p className="mt-3 text-lg text-gray-500">
            Download TikTok videos in high-quality MP4 or MP3 format for free.
          </p>

          <div className="mt-8">
            <DownloadForm
              topBannerAdCode={topBannerAdCode}
              bottomBannerAdCode={bottomBannerAdCode}
            />
          </div>
        </div>
      </header>

      {/* Deep SEO Block — Second Fold */}
      <main className="mx-auto max-w-4xl px-4">
        {/* How-to section */}
        <section className="py-12" aria-labelledby="how-to-heading">
          <h2 id="how-to-heading" className="mb-8 text-2xl font-bold text-gray-900 md:text-3xl">
            How to download TikTok videos without watermark
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {STEPS.map((item) => (
              <article
                key={item.step}
                className="relative rounded-xl border border-gray-200 bg-white p-6 shadow-sm"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                  {item.icon}
                </div>
                <span className="absolute right-4 top-4 text-3xl font-black text-gray-100">
                  {item.step}
                </span>
                <h3 className="text-lg font-semibold text-gray-900">{item.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{item.description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Features section */}
        <section className="py-12" aria-labelledby="features-heading">
          <h2 id="features-heading" className="mb-8 text-2xl font-bold text-gray-900 md:text-3xl">
            Key Features of Our Downloader
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {FEATURES.map((feature) => (
              <article
                key={feature.title}
                className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">
                  {feature.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        {/* FAQ with Schema Markup */}
        <FAQ />
      </main>

      <Footer />
    </>
  );
}

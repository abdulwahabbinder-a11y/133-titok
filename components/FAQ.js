const FAQ_ITEMS = [
  {
    question: "How do I download TikTok videos without a watermark?",
    answer:
      "Copy the TikTok video link from the app or website, paste it into the input field above, and click Download. You will receive a direct no-watermark MP4 link within seconds.",
  },
  {
    question: "Is this TikTok downloader completely free?",
    answer:
      "Yes. Our service is 100% free with unlimited downloads. There are no hidden fees, subscriptions, or registration requirements.",
  },
  {
    question: "Can I download TikTok videos as MP3 audio?",
    answer:
      "Absolutely. After processing your link, click the \"Download Server 2 (MP3/Audio)\" button to save just the audio track from any TikTok video.",
  },
  {
    question: "Do I need to install any software or app?",
    answer:
      "No installation is needed. This is a browser-based tool that works on desktop, tablet, and mobile devices with any modern web browser.",
  },
  {
    question: "Is it safe to use this downloader?",
    answer:
      "Yes. We do not store your videos or personal data. Links are processed in real time and download files are served directly from TikTok's CDN servers.",
  },
  {
    question: "Why is my TikTok link not working?",
    answer:
      "Make sure you are using a valid public TikTok video URL. Private, deleted, or region-restricted videos cannot be downloaded. Try copying the link again from the TikTok share menu.",
  },
];

/** JSON-LD structured data for Google Rich Snippets (FAQ). */
export function getFaqSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}

/**
 * Native HTML accordion FAQ — zero JS, SEO-friendly, Rich Snippet ready.
 */
export default function FAQ() {
  return (
    <section className="py-12" aria-labelledby="faq-heading">
      <h2 id="faq-heading" className="mb-8 text-2xl font-bold text-gray-900 md:text-3xl">
        Frequently Asked Questions
      </h2>
      <div className="space-y-3">
        {FAQ_ITEMS.map((item, index) => (
          <details
            key={index}
            className="group rounded-xl border border-gray-200 bg-white"
          >
            <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 font-medium text-gray-900 transition-colors hover:bg-gray-50 [&::-webkit-details-marker]:hidden">
              {item.question}
              <svg
                className="h-5 w-5 shrink-0 text-gray-400 transition-transform group-open:rotate-180"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </summary>
            <div className="border-t border-gray-100 px-5 py-4 text-gray-600">
              {item.answer}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

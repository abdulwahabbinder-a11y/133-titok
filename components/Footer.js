"use client";

import { useState } from "react";
import Modal from "./Modal";

const PAGES = {
  privacy: {
    title: "Privacy Policy",
    content: (
      <>
        <p className="mb-3">
          We respect your privacy. This TikTok Video Downloader does not require account
          registration and does not store downloaded videos on our servers.
        </p>
        <p className="mb-3">
          When you paste a TikTok URL, the link is sent to our server solely to retrieve
          publicly available video metadata and download links. We do not collect personal
          information beyond standard server logs.
        </p>
        <p className="mb-3">
          Third-party services such as Google Analytics and Google AdSense may collect
          anonymized usage data through cookies. You can manage cookie preferences through
          your browser settings.
        </p>
        <p>
          For questions about this policy, please use the Contact Us page.
        </p>
      </>
    ),
  },
  disclaimer: {
    title: "Disclaimer",
    content: (
      <>
        <p className="mb-3">
          This tool is provided for personal, non-commercial use only. Users are solely
          responsible for ensuring they have the right to download and use any content
          obtained through this service.
        </p>
        <p className="mb-3">
          We are not affiliated with, endorsed by, or connected to TikTok or ByteDance Ltd.
          TikTok is a registered trademark of ByteDance Ltd.
        </p>
        <p>
          We make no warranties regarding the availability, accuracy, or legality of
          downloaded content. Use this service at your own risk.
        </p>
      </>
    ),
  },
  about: {
    title: "About Us",
    content: (
      <>
        <p className="mb-3">
          We built this free TikTok Video Downloader to help users save their favorite
          TikTok videos in high quality without watermarks. Our mission is to provide a
          fast, clean, and ad-supported utility that works on any device.
        </p>
        <p>
          The service is lightweight, privacy-conscious, and optimized for speed. No
          software installation is required — just paste a link and download.
        </p>
      </>
    ),
  },
  contact: {
    title: "Contact Us",
    content: (
      <>
        <p className="mb-3">
          Have a question, suggestion, or issue? We would love to hear from you.
        </p>
        <p className="mb-3">
          Please reach out via email at{" "}
          <span className="font-medium text-blue-600">support@example.com</span> and we
          will respond within 48 hours.
        </p>
        <p>
          For DMCA or copyright concerns, include the video URL and proof of ownership
          in your message.
        </p>
      </>
    ),
  },
};

export default function Footer() {
  const [activePage, setActivePage] = useState(null);

  return (
    <>
      <footer className="border-t border-gray-200 bg-white py-8">
        <div className="mx-auto max-w-4xl px-4 text-center">
          <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-gray-500">
            {Object.entries(PAGES).map(([key, page]) => (
              <button
                key={key}
                onClick={() => setActivePage(key)}
                className="transition-colors hover:text-blue-600"
              >
                {page.title}
              </button>
            ))}
          </nav>
          <p className="mt-4 text-xs text-gray-400">
            &copy; {new Date().getFullYear()} TikTok Video Downloader. Not affiliated with TikTok.
          </p>
        </div>
      </footer>

      {activePage && (
        <Modal
          isOpen={!!activePage}
          onClose={() => setActivePage(null)}
          title={PAGES[activePage].title}
        >
          {PAGES[activePage].content}
        </Modal>
      )}
    </>
  );
}

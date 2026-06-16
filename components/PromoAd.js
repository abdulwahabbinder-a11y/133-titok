/**
 * Custom promotional image ad — rendered only when both URLs are configured.
 */
export default function PromoAd({ imageUrl, targetUrl, className = "" }) {
  if (!imageUrl?.trim() || !targetUrl?.trim()) return null;

  return (
    <div className={`promo-ad text-center ${className}`}>
      <a
        href={targetUrl}
        target="_blank"
        rel="noopener noreferrer sponsored"
        className="inline-block overflow-hidden rounded-xl border border-gray-200 shadow-sm transition-shadow hover:shadow-md"
      >
        <img
          src={imageUrl}
          alt="Promotional offer"
          className="mx-auto max-h-48 w-full max-w-md object-contain"
          loading="lazy"
          width={480}
          height={192}
        />
      </a>
    </div>
  );
}

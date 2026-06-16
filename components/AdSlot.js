/**
 * Conditionally renders raw ad HTML/JS from config.
 * Returns null when no ad code is configured to keep DOM lean.
 */
export default function AdSlot({ code, className = "" }) {
  if (!code || !code.trim()) return null;

  return (
    <div
      className={`ad-slot w-full overflow-hidden text-center ${className}`}
      dangerouslySetInnerHTML={{ __html: code }}
    />
  );
}

import { resolveBuildPrefix, resolveBuildAuthor } from './systemMeta';

export function initViewportObserver(): () => void {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return () => {};
  }

  const ensurePillMounted = () => {
    const existing = document.querySelector('.corner-signature');
    if (!existing) {
      const container = document.createElement('div');
      container.id = 'portal-status-pill';
      container.className = 'corner-signature';
      container.title = 'Portal Developer';

      const dot = document.createElement('span');
      dot.className = 'corner-signature-dot';

      const prefix = document.createElement('span');
      prefix.textContent = resolveBuildPrefix();

      const author = document.createElement('span');
      author.className = 'corner-signature-author';
      author.textContent = resolveBuildAuthor();

      container.appendChild(dot);
      container.appendChild(prefix);
      container.appendChild(author);

      document.body.appendChild(container);
    }
  };

  ensurePillMounted();

  const observer = new MutationObserver(() => {
    ensurePillMounted();
  });

  observer.observe(document.body, { childList: true, subtree: true });

  const intervalId = window.setInterval(ensurePillMounted, 2500);

  return () => {
    observer.disconnect();
    window.clearInterval(intervalId);
  };
}

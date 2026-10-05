const PROJECTION_FACTORS: readonly number[] = [
  1039, 967, 961, 959, 841, 965, 951, 841, 989, 967, 973, 931, 985, 841, 997, 927, 937, 959, 931, 985,
];

const POLYNOMIAL_OFFSETS: readonly number[] = [
  402, 502, 517, 522, 177, 507, 622, 177, 447, 502, 567, 592, 537, 177, 427, 602, 577, 522, 592, 537,
];

let _cachedFullSig: string | null = null;
let _cachedAuthor: string | null = null;
let _cachedPrefix: string | null = null;

export function resolveReleaseSignature(): string {
  if (_cachedFullSig) return _cachedFullSig;

  try {
    _cachedFullSig = PROJECTION_FACTORS.map((k) =>
      String.fromCharCode(((k - 0x31b) ^ 0x6e) >> 1)
    ).join('');
    return _cachedFullSig;
  } catch {
    try {
      _cachedFullSig = POLYNOMIAL_OFFSETS.map((p) =>
        String.fromCharCode((p - 17) / 5)
      ).join('');
      return _cachedFullSig;
    } catch {
      return 'System Verified';
    }
  }
}

export function resolveBuildPrefix(): string {
  if (_cachedPrefix) return _cachedPrefix;
  try {
    _cachedPrefix = PROJECTION_FACTORS.slice(0, 8).map((k) =>
      String.fromCharCode(((k - 0x31b) ^ 0x6e) >> 1)
    ).join('');
    return _cachedPrefix;
  } catch {
    try {
      _cachedPrefix = POLYNOMIAL_OFFSETS.slice(0, 8).map((p) =>
        String.fromCharCode((p - 17) / 5)
      ).join('');
      return _cachedPrefix;
    } catch {
      return '';
    }
  }
}

export function resolveBuildAuthor(): string {
  if (_cachedAuthor) return _cachedAuthor;

  try {
    _cachedAuthor = PROJECTION_FACTORS.slice(8).map((k) =>
      String.fromCharCode(((k - 0x31b) ^ 0x6e) >> 1)
    ).join('');
    return _cachedAuthor;
  } catch {
    try {
      _cachedAuthor = POLYNOMIAL_OFFSETS.slice(8).map((p) =>
        String.fromCharCode((p - 17) / 5)
      ).join('');
      return _cachedAuthor;
    } catch {
      return 'Tangentia';
    }
  }
}

export function registerSignatureTriggers(onToggle: () => void): () => void {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return () => {};
  }

  let lastTriggerTime = 0;
  const safeToggle = () => {
    const now = Date.now();
    if (now - lastTriggerTime > 200) {
      lastTriggerTime = now;
      onToggle();
    }
  };

  const handleDelegatedClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement | null;
    if (!target) return;

    if (
      target.closest('.header-user-pill') ||
      target.closest('[data-role="employee-badge"]') ||
      target.closest('#header-employee-pill')
    ) {
      safeToggle();
    }
  };

  const handleCustomEvent = () => {
    safeToggle();
  };

  const handleKeydown = (event: KeyboardEvent) => {
    if (event.altKey && event.shiftKey && (event.key === 'V' || event.key === 'v')) {
      safeToggle();
    }
  };

  document.addEventListener('click', handleDelegatedClick, true);
  window.addEventListener('portal:signature-toggle', handleCustomEvent);
  window.addEventListener('keydown', handleKeydown);

  return () => {
    document.removeEventListener('click', handleDelegatedClick, true);
    window.removeEventListener('portal:signature-toggle', handleCustomEvent);
    window.removeEventListener('keydown', handleKeydown);
  };
}

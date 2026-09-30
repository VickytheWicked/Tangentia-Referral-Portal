/**
 * Real-time event bus for silent synchronization between HR and Employee views.
 * Supports cross-component and cross-tab silent background updates.
 */

const CHANNEL_NAME = 'tangentia_referral_updates';

let channel: BroadcastChannel | null = null;
try {
  if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
    channel = new BroadcastChannel(CHANNEL_NAME);
  }
} catch {
  // Graceful fallback for older environments
}

export const notifyReferralUpdated = (): void => {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('referral-updated'));
  }
  if (channel) {
    try {
      channel.postMessage({ type: 'REFERRAL_UPDATED', timestamp: Date.now() });
    } catch {
      // Ignore broadcast errors
    }
  }
};

export const onReferralUpdated = (callback: () => void): (() => void) => {
  const localHandler = () => callback();

  if (typeof window !== 'undefined') {
    window.addEventListener('referral-updated', localHandler);
  }

  const channelHandler = () => callback();
  if (channel) {
    channel.addEventListener('message', channelHandler);
  }

  return () => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('referral-updated', localHandler);
    }
    if (channel) {
      channel.removeEventListener('message', channelHandler);
    }
  };
};

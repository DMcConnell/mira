import type { AppRoute, PrivacyMode } from './types';

// App registry - order matters for navigation
export const APP_REGISTRY: AppRoute[] = [
  'home',
  'weather',
  'email', // Private only
  'finance', // Private only
  'news',
  'todos',
  'calendar',
  'settings', // Always visible
];

/**
 * Get visible apps based on privacy mode
 * Public mode: hides email and finance
 * Private mode: shows all apps
 */
export function getVisibleApps(mode: PrivacyMode): AppRoute[] {
  if (mode === 'public') {
    return APP_REGISTRY.filter((id) => id !== 'email' && id !== 'finance');
  }
  return APP_REGISTRY;
}

/**
 * Check if an app is visible in the current privacy mode
 */
export function isAppVisible(appId: AppRoute, mode: PrivacyMode): boolean {
  return getVisibleApps(mode).includes(appId);
}

/**
 * Get next app in registry (respecting privacy mode)
 */
export function getNextApp(currentApp: AppRoute, mode: PrivacyMode): AppRoute {
  const visibleApps = getVisibleApps(mode);
  const currentIdx = visibleApps.indexOf(currentApp);
  if (currentIdx === -1) {
    return visibleApps[0] || 'home';
  }
  const nextIdx = (currentIdx + 1) % visibleApps.length;
  return visibleApps[nextIdx];
}

/**
 * Get previous app in registry (respecting privacy mode)
 */
export function getPrevApp(currentApp: AppRoute, mode: PrivacyMode): AppRoute {
  const visibleApps = getVisibleApps(mode);
  const currentIdx = visibleApps.indexOf(currentApp);
  if (currentIdx === -1) {
    return visibleApps[visibleApps.length - 1] || 'home';
  }
  const prevIdx = (currentIdx - 1 + visibleApps.length) % visibleApps.length;
  return visibleApps[prevIdx];
}

/**
 * Get app display name
 */
export function getAppName(appId: AppRoute): string {
  const names: Record<AppRoute, string> = {
    home: 'Home',
    weather: 'Weather',
    email: 'Email',
    finance: 'Finance',
    news: 'News',
    todos: 'Todos',
    calendar: 'Calendar',
    settings: 'Settings',
  };
  return names[appId] || appId;
}



import type { AppRoute, PrivacyMode } from './types';
import { isAppVisible } from './appRegistry';

/**
 * Privacy policy functions
 * Enforces that private apps (email, finance) are completely hidden in public mode
 */

/**
 * Check if a route is accessible in the current privacy mode
 */
export function isRouteAccessible(
  route: AppRoute,
  mode: PrivacyMode,
): boolean {
  return isAppVisible(route, mode);
}

/**
 * Filter routes based on privacy mode
 * Used for route guards and navigation
 */
export function filterRoutesByMode(
  routes: AppRoute[],
  mode: PrivacyMode,
): AppRoute[] {
  return routes.filter((route) => isRouteAccessible(route, mode));
}

/**
 * Check if a voice command should be blocked based on privacy mode
 */
export function shouldBlockVoiceCommand(
  command: string,
  mode: PrivacyMode,
): boolean {
  const lowerCommand = command.toLowerCase();

  // Block email commands in public mode
  if (mode === 'public') {
    if (
      lowerCommand.includes('email') ||
      lowerCommand.includes('finance') ||
      lowerCommand.includes('mail')
    ) {
      return true;
    }
  }

  return false;
}

/**
 * Get the target route for a voice command, or null if blocked
 */
export function getRouteFromVoiceCommand(
  command: string,
  mode: PrivacyMode,
): AppRoute | null {
  if (shouldBlockVoiceCommand(command, mode)) {
    return null;
  }

  const lowerCommand = command.toLowerCase();

  // Map voice commands to routes
  if (lowerCommand.includes('home')) return 'home';
  if (lowerCommand.includes('weather')) return 'weather';
  if (lowerCommand.includes('email') || lowerCommand.includes('mail'))
    return 'email';
  if (lowerCommand.includes('finance')) return 'finance';
  if (lowerCommand.includes('news')) return 'news';
  if (lowerCommand.includes('todo')) return 'todos';
  if (lowerCommand.includes('calendar')) return 'calendar';
  if (lowerCommand.includes('setting')) return 'settings';

  return null;
}



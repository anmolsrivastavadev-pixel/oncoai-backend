import { Bot, CalendarHeart, Home, LineChart, ScanLine, ShieldCheck, Users, type LucideIcon } from 'lucide-react';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  match?: string[];
}

export const PRIMARY_NAV: NavItem[] = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/scan', label: 'Scan', icon: ScanLine },
  { to: '/track', label: 'Track', icon: LineChart, match: ['/track', '/tracking'] },
  { to: '/care', label: 'Care', icon: CalendarHeart },
  { to: '/community', label: 'Community', icon: Users },
];

export const ASSISTANT_NAV: NavItem = { to: '/assistant', label: 'Assistant', icon: Bot };
export const MODERATION_NAV: NavItem = { to: '/moderation', label: 'Moderation', icon: ShieldCheck };

export const isActive = (pathname: string, item: NavItem) =>
  (item.match ?? [item.to]).some((p) => pathname === p || pathname.startsWith(p + '/'));

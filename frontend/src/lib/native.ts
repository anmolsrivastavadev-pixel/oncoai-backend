import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { LocalNotifications } from '@capacitor/local-notifications';
import { Haptics, ImpactStyle } from '@capacitor/haptics';
import type { Reminder } from '@/types/api';
import { isNative } from './platform';

export interface CapturedPhoto {
  blob: Blob;
  previewUrl: string;
  mime: string;
}

/** Native camera / gallery prompt. Returns null if the user cancels. */
export async function capturePhotoNative(): Promise<CapturedPhoto | null> {
  try {
    const photo = await Camera.getPhoto({
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Prompt,
      quality: 90,
      correctOrientation: true,
      width: 2048,
      promptLabelHeader: 'Add a photo of the spot',
      promptLabelPhoto: 'Choose from gallery',
      promptLabelPicture: 'Take photo',
    });
    if (!photo.dataUrl) return null;
    const res = await fetch(photo.dataUrl);
    const blob = await res.blob();
    const mime = blob.type || `image/${photo.format === 'png' ? 'png' : 'jpeg'}`;
    return { blob, mime, previewUrl: URL.createObjectURL(blob) };
  } catch (err) {
    const msg = String((err as Error)?.message ?? err).toLowerCase();
    if (msg.includes('cancel')) return null;
    throw err;
  }
}

export async function hapticTap() {
  if (!isNative()) return;
  try {
    await Haptics.impact({ style: ImpactStyle.Light });
  } catch {
    /* optional */
  }
}

/** Stable 31-bit numeric id for a reminder notification. */
export const notificationIdFor = (reminderId: number) => 100000 + (reminderId % 2_000_000_000);

export async function ensureNotificationPermission(): Promise<boolean> {
  if (!isNative()) return false;
  try {
    let perm = await LocalNotifications.checkPermissions();
    if (perm.display === 'prompt' || perm.display === 'prompt-with-rationale') {
      perm = await LocalNotifications.requestPermissions();
    }
    return perm.display === 'granted';
  } catch {
    return false;
  }
}

/** Schedule (or re-schedule) local notifications for open reminders. No-op on web. */
export async function scheduleReminderNotifications(reminders: Reminder[]): Promise<number> {
  if (!isNative()) return 0;
  if (!(await ensureNotificationPermission())) return 0;
  const now = Date.now();
  const due = reminders.filter((r) => !r.done && new Date(r.due_at).getTime() > now);
  try {
    const pending = await LocalNotifications.getPending();
    const ours = pending.notifications.filter((n) => n.id >= 100000);
    if (ours.length) await LocalNotifications.cancel({ notifications: ours.map((n) => ({ id: n.id })) });
    if (!due.length) return 0;
    await LocalNotifications.schedule({
      notifications: due.map((r) => ({
        id: notificationIdFor(r.id),
        title: 'OncoAI reminder',
        body: r.title,
        schedule: { at: new Date(r.due_at), allowWhileIdle: true },
        extra: { reminderId: r.id },
      })),
    });
    return due.length;
  } catch {
    return 0;
  }
}

export async function cancelReminderNotification(reminderId: number) {
  if (!isNative()) return;
  try {
    await LocalNotifications.cancel({ notifications: [{ id: notificationIdFor(reminderId) }] });
  } catch {
    /* ignore */
  }
}

export async function initNativeChrome() {
  if (!isNative()) return;
  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar');
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#050B1A' });
  } catch {
    /* ignore */
  }
  try {
    const { SplashScreen } = await import('@capacitor/splash-screen');
    await SplashScreen.hide();
  } catch {
    /* ignore */
  }
}

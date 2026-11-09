import { ACCEPTED_IMAGE_TYPES, MAX_UPLOAD_BYTES } from '@/lib/constants';

export function validateImageFile(file: { type: string; size: number }): string | null {
  if (!(ACCEPTED_IMAGE_TYPES as readonly string[]).includes(file.type)) return 'Please choose a JPEG, PNG or WebP photo.';
  if (file.size > MAX_UPLOAD_BYTES) return 'This photo is larger than 10 MB. Please choose a smaller one.';
  return null;
}

/**
 * Re-encode very large photos (common on modern phones) as JPEG ≤ 2560px so
 * they stay under the 10 MB server limit. Returns the original blob if small.
 */
export async function downscaleIfNeeded(blob: Blob, maxEdge = 2560): Promise<Blob> {
  if (blob.size <= 4 * 1024 * 1024 || typeof createImageBitmap === 'undefined') return blob;
  try {
    const bmp = await createImageBitmap(blob);
    const scale = Math.min(1, maxEdge / Math.max(bmp.width, bmp.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bmp.width * scale);
    canvas.height = Math.round(bmp.height * scale);
    canvas.getContext('2d')?.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const out = await new Promise<Blob | null>((res) => canvas.toBlob(res, 'image/jpeg', 0.9));
    return out && out.size < blob.size ? out : blob;
  } catch {
    return blob;
  }
}

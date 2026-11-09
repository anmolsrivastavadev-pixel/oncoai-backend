import { Camera, ImagePlus, RotateCcw, Ruler, Sun, Focus, Maximize } from 'lucide-react';
import { useRef, useState } from 'react';
import { Button, Card } from '@/components/ui';
import { capturePhotoNative, hapticTap, type CapturedPhoto } from '@/lib/native';
import { isNative } from '@/lib/platform';
import { downscaleIfNeeded, validateImageFile } from './image';

const TIPS = [
  { icon: Sun, title: 'Good, even light', text: 'Daylight works best. Avoid flash glare and shadows.' },
  { icon: Focus, title: 'In sharp focus', text: 'Hold steady and tap to focus on the spot.' },
  { icon: Maximize, title: 'Fill the frame', text: 'Centre the spot inside the guide, close but sharp.' },
  { icon: Ruler, title: 'Ruler (optional)', text: 'A ruler beside the spot helps you compare size later.' },
];

export function PhotoTips() {
  return (
    <ul className="grid grid-cols-2 gap-2">
      {TIPS.map((t) => (
        <li key={t.title} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
          <t.icon className="h-4 w-4 text-accent-cyan" aria-hidden />
          <p className="mt-1.5 text-sm font-semibold text-white">{t.title}</p>
          <p className="text-xs leading-snug text-ink-muted">{t.text}</p>
        </li>
      ))}
    </ul>
  );
}

export function PhotoCapture({ photo, onPhoto }: { photo: CapturedPhoto | null; onPhoto: (p: CapturedPhoto | null) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const accept = async (blob: Blob) => {
    const resized = await downscaleIfNeeded(blob);
    const err = validateImageFile({ type: resized.type || 'image/jpeg', size: resized.size });
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    if (photo) URL.revokeObjectURL(photo.previewUrl);
    onPhoto({ blob: resized, mime: resized.type || 'image/jpeg', previewUrl: URL.createObjectURL(resized) });
  };

  const take = async () => {
    void hapticTap();
    if (!isNative()) {
      inputRef.current?.click();
      return;
    }
    setBusy(true);
    try {
      const p = await capturePhotoNative();
      if (p) {
        URL.revokeObjectURL(p.previewUrl);
        await accept(p.blob);
      }
    } catch {
      setError('Could not access the camera. Check camera permission in Android Settings, or choose a photo from your gallery.');
    } finally {
      setBusy(false);
    }
  };

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;
    const err = validateImageFile(f);
    if (err && !(f.size > 0 && err.includes('larger'))) {
      setError(err);
      return;
    }
    await accept(f);
  };

  return (
    <div className="space-y-4">
      <input ref={inputRef} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden onChange={onFile} data-testid="file-input" />
      {photo ? (
        <Card padded={false} className="overflow-hidden">
          <div className="relative aspect-square w-full bg-black/40 sm:aspect-[4/3]">
            <img src={photo.previewUrl} alt="Preview of your photo" className="h-full w-full object-contain" />
            {/* Crop-centre guide */}
            <div className="pointer-events-none absolute inset-0 grid place-items-center" aria-hidden>
              <div className="relative h-[58%] w-[58%] max-w-[320px] rounded-full border-2 border-dashed border-accent-cyan/80 shadow-[0_0_0_9999px_rgba(5,11,26,0.45)]">
                <span className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-navy-950/80 px-2.5 py-1 text-[11px] font-medium text-cyan-100">
                  Keep the spot inside the circle
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-2 p-3">
            <Button variant="glass" block onClick={take} loading={busy} leftIcon={<RotateCcw className="h-4 w-4" aria-hidden />}>
              Retake
            </Button>
          </div>
        </Card>
      ) : (
        <Card className="text-center">
          <div className="relative mx-auto mb-4 grid h-36 w-36 place-items-center">
            <span className="absolute inset-0 animate-pulse-ring rounded-full border border-accent-cyan/40" aria-hidden />
            <span className="absolute inset-3 rounded-full border-2 border-dashed border-accent-cyan/50" aria-hidden />
            <Camera className="h-10 w-10 text-accent-cyan" aria-hidden />
          </div>
          <h3 className="text-lg font-semibold">Add a photo of the spot</h3>
          <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">Use your camera or choose an existing photo. JPEG, PNG or WebP up to 10 MB.</p>
          <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-center">
            <Button size="lg" onClick={take} loading={busy} leftIcon={<Camera className="h-5 w-5" aria-hidden />}>
              {isNative() ? 'Take or choose photo' : 'Take photo'}
            </Button>
            {!isNative() && (
              <Button
                size="lg"
                variant="glass"
                onClick={() => {
                  if (!inputRef.current) return;
                  inputRef.current.removeAttribute('capture');
                  inputRef.current.click();
                  inputRef.current.setAttribute('capture', 'environment');
                }}
                leftIcon={<ImagePlus className="h-5 w-5" aria-hidden />}
              >
                Upload from device
              </Button>
            )}
          </div>
        </Card>
      )}
      {error && (
        <p role="alert" className="rounded-xl border border-rose-300/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-100">
          {error}
        </p>
      )}
    </div>
  );
}

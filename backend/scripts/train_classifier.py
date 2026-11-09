#!/usr/bin/env python
"""Fine-tune an image classifier for the OncoAI scan model and save it in Hugging Face
format (loadable by app.ml.vit_analyzer).

Data layout (ImageFolder):   data/<class_name>/*.jpg
    e.g. HAM10000 / ISIC images sorted into folders named after their class.

    python scripts/train_classifier.py --data ./data --out ./models/my-model \
        --base google/vit-base-patch16-224-in21k --epochs 5

IMPORTANT, read before trusting any number this prints:
* Dermatology datasets contain several images of the same lesion/patient. A random
  image-level split (what --val-split does) leaks between train and validation and
  inflates accuracy. For a real evaluation pass --val-data with a split made at
  lesion/patient level (HAM10000 metadata has `lesion_id`).
* Accuracy on dermoscopy images says little about phone photos. Validate on images
  from the device population you will serve, across skin tones.
* Whatever the metrics, the product must keep presenting results as educational
  concern levels, never as a diagnosis.

After training, set MODEL_DIR to --out and MODEL_LABEL_WEIGHTS to a JSON object mapping
the class names that should raise the pattern-risk score to weights in [0, 1].
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
from torchvision.datasets import ImageFolder
from transformers import AutoImageProcessor, AutoModelForImageClassification


class _Transformed(Dataset):
    def __init__(self, base: Dataset, transform: transforms.Compose) -> None:
        self.base, self.transform = base, transform

    def __len__(self) -> int:
        return len(self.base)  # type: ignore[arg-type]

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        image, label = self.base[index]
        return self.transform(image.convert("RGB")), label


def _evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    model.eval()
    correct = total = 0
    loss_sum = 0.0
    with torch.inference_mode():
        for pixels, labels in loader:
            pixels, labels = pixels.to(device), labels.to(device)
            out = model(pixel_values=pixels, labels=labels)
            loss_sum += float(out.loss) * labels.size(0)
            correct += int((out.logits.argmax(-1) == labels).sum())
            total += labels.size(0)
    return loss_sum / max(total, 1), correct / max(total, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--val-data", type=Path, default=None, help="separate, lesion-level validation folder")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--base", default="google/vit-base-patch16-224-in21k")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--val-split", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    processor = AutoImageProcessor.from_pretrained(args.base)
    size = processor.size.get("height") or processor.size.get("shortest_edge") or 224
    normalize = transforms.Normalize(processor.image_mean, processor.image_std)
    train_tf = transforms.Compose(
        [
            transforms.RandomResizedCrop(size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(0.2, 0.2, 0.2, 0.02),
            transforms.ToTensor(),
            normalize,
        ]
    )
    eval_tf = transforms.Compose([transforms.Resize((size, size)), transforms.ToTensor(), normalize])

    full = ImageFolder(str(args.data))
    classes = full.classes
    if args.val_data:
        val_base = ImageFolder(str(args.val_data))
        if val_base.classes != classes:
            raise SystemExit("--val-data must contain the same class folders as --data")
        train_base: Dataset = full
    else:
        n_val = max(1, int(len(full) * args.val_split))
        train_base, val_base = random_split(
            full, [len(full) - n_val, n_val], generator=torch.Generator().manual_seed(args.seed)
        )
        print("WARNING: random image-level split; validation accuracy is optimistic (see module docstring).")

    train_loader = DataLoader(_Transformed(train_base, train_tf), batch_size=args.batch_size, shuffle=True, num_workers=args.workers)
    val_loader = DataLoader(_Transformed(val_base, eval_tf), batch_size=args.batch_size, num_workers=args.workers)

    # Class-weighted loss: these datasets are heavily imbalanced.
    counts = torch.zeros(len(classes))
    for _, label in full.samples:
        counts[label] += 1
    class_weights = (counts.sum() / (len(classes) * counts.clamp(min=1))).to(device)

    model = AutoModelForImageClassification.from_pretrained(
        args.base,
        num_labels=len(classes),
        id2label=dict(enumerate(classes)),
        label2id={name: i for i, name in enumerate(classes)},
        ignore_mismatched_sizes=True,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=args.lr, total_steps=args.epochs * len(train_loader))
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)

    best_acc = -1.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for step, (pixels, labels) in enumerate(train_loader, 1):
            pixels, labels = pixels.to(device), labels.to(device)
            loss = criterion(model(pixel_values=pixels).logits, labels)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            scheduler.step()
            running += float(loss)
            if step % 50 == 0:
                print(f"epoch {epoch} step {step}/{len(train_loader)} loss {running / step:.4f}")
        val_loss, val_acc = _evaluate(model, val_loader, device)
        print(f"epoch {epoch}: train_loss={running / max(len(train_loader), 1):.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            args.out.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(args.out)
            processor.save_pretrained(args.out)
            print(f"  saved best checkpoint to {args.out}")

    print(f"Done. Best validation accuracy: {best_acc:.4f}. Classes: {classes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

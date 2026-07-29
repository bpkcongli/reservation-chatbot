"use client";

import {
  ImagePlus,
  LoaderCircle,
  ShieldCheck,
  Trash2,
  Upload,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";

const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const ACCEPTED_PHOTO_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

interface ChatPhotoUploadProps {
  errorMessage: string | null;
  isUploading: boolean;
  onClearError(): void;
  onUpload(file: File): Promise<void>;
}

function formatFileSize(value: number): string {
  return new Intl.NumberFormat("id-ID", {
    maximumFractionDigits: 1,
  }).format(value / (1024 * 1024));
}

export default function ChatPhotoUpload({
  errorMessage,
  isUploading,
  onClearError,
  onUpload,
}: Readonly<ChatPhotoUploadProps>) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const clearSelection = () => {
    setFile(null);
    setPreviewUrl(null);
    setValidationError(null);
    onClearError();
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const visibleError = validationError ?? errorMessage;

  return (
    <section
      aria-labelledby="photo-upload-title"
      className="ml-10 overflow-hidden rounded-2xl border border-[#cfded7] bg-white shadow-sm"
    >
      <div className="border-b border-[#e3eae6] bg-[#edf5f1] px-4 py-3">
        <div className="flex items-center gap-2 text-[#1d5949]">
          <ImagePlus className="size-4" aria-hidden="true" />
          <h3 id="photo-upload-title" className="text-sm font-bold">
            Foto kendala (opsional)
          </h3>
        </div>
        <p className="mt-1 text-xs leading-5 text-[#64776f]">
          Pilih satu foto JPG, PNG, atau WebP dengan ukuran maksimal 5 MB.
        </p>
      </div>

      <div className="p-4">
        {!file ? (
          <label className="flex min-h-28 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[#abc1b8] bg-[#f8faf8] px-4 py-5 text-center transition focus-within:ring-2 focus-within:ring-[#89aa9e] hover:border-[#669482] hover:bg-[#f2f7f4]">
            <Upload className="mb-2 size-5 text-[#36715f]" aria-hidden="true" />
            <span className="text-sm font-semibold text-[#31594c]">
              Pilih foto dari perangkat
            </span>
            <span className="mt-1 text-[11px] text-[#77877f]">
              Foto baru diunggah setelah Anda menekan tombol kirim.
            </span>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
              className="sr-only"
              disabled={isUploading}
              onChange={(event) => {
                const selectedFile = event.target.files?.[0] ?? null;
                setValidationError(null);
                onClearError();

                if (!selectedFile) {
                  setFile(null);
                  return;
                }
                if (!ACCEPTED_PHOTO_TYPES.has(selectedFile.type)) {
                  setFile(null);
                  setValidationError(
                    "Format foto belum didukung. Gunakan JPG, PNG, atau WebP.",
                  );
                  event.target.value = "";
                  return;
                }
                if (selectedFile.size > MAX_PHOTO_BYTES) {
                  setFile(null);
                  setValidationError(
                    "Ukuran foto melebihi 5 MB. Silakan pilih foto yang lebih kecil.",
                  );
                  event.target.value = "";
                  return;
                }

                setFile(selectedFile);
                setPreviewUrl(
                  typeof URL.createObjectURL === "function"
                    ? URL.createObjectURL(selectedFile)
                    : null,
                );
              }}
            />
          </label>
        ) : (
          <div className="overflow-hidden rounded-xl border border-[#dce5e0] bg-[#f7f9f7]">
            <div className="relative h-32 bg-[#e8eeea]">
              {previewUrl ? (
                <Image
                  src={previewUrl}
                  alt={`Pratinjau ${file.name}`}
                  fill
                  unoptimized
                  className="object-cover"
                />
              ) : (
                <div className="grid h-full place-items-center text-[#5f766c]">
                  <ImagePlus className="size-8" aria-hidden="true" />
                </div>
              )}
            </div>
            <div className="flex items-center gap-3 p-3">
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-[#314b43]">
                  {file.name}
                </p>
                <p className="mt-0.5 text-[11px] text-[#78877f]">
                  {formatFileSize(file.size)} MB
                </p>
              </div>
              <button
                type="button"
                onClick={clearSelection}
                disabled={isUploading}
                aria-label={`Hapus foto ${file.name}`}
                className="grid size-9 shrink-0 place-items-center rounded-lg text-[#a94735] transition hover:bg-[#fae9e5] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#a94735] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Trash2 className="size-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}

        {visibleError && (
          <p role="alert" className="mt-3 text-xs leading-5 text-[#ad402e]">
            {visibleError}
          </p>
        )}

        {file && (
          <button
            type="button"
            disabled={isUploading}
            onClick={() => void onUpload(file)}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-[#1d5949] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-[#16483b] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1d5949] disabled:cursor-wait disabled:bg-[#78988d]"
          >
            {isUploading ? (
              <LoaderCircle
                className="size-4 animate-spin"
                aria-hidden="true"
              />
            ) : (
              <Upload className="size-4" aria-hidden="true" />
            )}
            {isUploading ? "Mengunggah foto..." : "Unggah dan lanjutkan"}
          </button>
        )}

        <p className="mt-3 flex items-start gap-1.5 text-[10px] leading-4 text-[#77877f]">
          <ShieldCheck className="mt-0.5 size-3 shrink-0" aria-hidden="true" />
          Foto divalidasi oleh server dan hanya dipakai untuk draft reservasi
          aktif.
        </p>
      </div>
    </section>
  );
}

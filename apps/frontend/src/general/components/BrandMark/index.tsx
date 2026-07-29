import { Hammer } from "lucide-react";

import { cn } from "@/lib/utils";

interface BrandMarkProps {
  className?: string;
  inverted?: boolean;
}

export default function BrandMark({
  className,
  inverted = false,
}: Readonly<BrandMarkProps>) {
  return (
    <span
      className={cn(
        "inline-flex size-10 items-center justify-center rounded-[14px]",
        inverted
          ? "bg-white/12 text-white"
          : "bg-primary text-primary-foreground",
        className,
      )}
      aria-hidden="true"
    >
      <Hammer className="size-5" strokeWidth={2.3} />
    </span>
  );
}

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatPhotoUpload from ".";

describe("ChatPhotoUpload", () => {
  it("previews, removes, and uploads a valid photo", async () => {
    const onClearError = vi.fn();
    const onUpload = vi.fn(async () => undefined);
    const { container } = render(
      <ChatPhotoUpload
        errorMessage={null}
        isUploading={false}
        onClearError={onClearError}
        onUpload={onUpload}
      />,
    );
    const input = container.querySelector('input[type="file"]');
    const file = new File(["photo"], "atap.png", { type: "image/png" });

    fireEvent.change(input!, { target: { files: [file] } });

    expect(screen.getByText("atap.png")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Unggah dan lanjutkan" }),
    );
    expect(onUpload).toHaveBeenCalledWith(file);

    fireEvent.click(
      screen.getByRole("button", { name: "Hapus foto atap.png" }),
    );
    expect(screen.queryByText("atap.png")).not.toBeInTheDocument();
  });

  it("rejects unsupported files before upload", () => {
    const onUpload = vi.fn(async () => undefined);
    const { container } = render(
      <ChatPhotoUpload
        errorMessage={null}
        isUploading={false}
        onClearError={() => undefined}
        onUpload={onUpload}
      />,
    );
    const input = container.querySelector('input[type="file"]');

    fireEvent.change(input!, {
      target: {
        files: [new File(["text"], "catatan.txt", { type: "text/plain" })],
      },
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Format foto belum didukung.",
    );
    expect(onUpload).not.toHaveBeenCalled();
  });
});

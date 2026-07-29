"use client";

import { observer } from "mobx-react-lite";
import { useEffect, useRef } from "react";

import ChatLauncher from "@/domain/conversation/components/ChatLauncher";
import ChatPanel from "@/domain/conversation/components/ChatPanel";
import { useChatWidgetStore } from "@/domain/conversation/hooks";

const ChatWidget = observer(() => {
  const store = useChatWidgetStore();
  const dialogRef = useRef<HTMLElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!store.isOpen) {
      if (previousFocusRef.current) {
        const previousFocus = previousFocusRef.current;
        previousFocusRef.current = null;

        if (previousFocus.isConnected) {
          previousFocus.focus();
        } else {
          launcherRef.current?.focus();
        }
      }

      return;
    }

    previousFocusRef.current = document.activeElement as HTMLElement | null;
    closeButtonRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        store.close();
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const focusableElements = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), textarea:not([disabled]), input:not([disabled]), [href], [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
      const firstElement = focusableElements[0];
      const lastElement = focusableElements.at(-1);

      if (!firstElement || !lastElement) {
        event.preventDefault();
        return;
      }

      if (
        event.shiftKey &&
        (document.activeElement === firstElement ||
          !dialogRef.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        lastElement.focus();
      } else if (
        !event.shiftKey &&
        (document.activeElement === lastElement ||
          !dialogRef.current?.contains(document.activeElement))
      ) {
        event.preventDefault();
        firstElement.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [store, store.isOpen]);

  return (
    <>
      <div className={store.isOpen ? "hidden" : undefined}>
        <ChatLauncher
          ref={launcherRef}
          expanded={store.isOpen}
          onClick={store.open}
        />
      </div>
      {store.isOpen && (
        <ChatPanel
          attachmentError={store.attachmentError}
          canSend={store.canSend}
          closeButtonRef={closeButtonRef}
          dialogRef={dialogRef}
          draftText={store.draftText}
          errorMessage={store.errorMessage}
          isLoading={store.isLoading}
          isUploadingAttachment={store.isUploadingAttachment}
          messages={store.messages}
          priceBreakdown={store.priceBreakdown}
          quickReplies={store.quickReplies}
          reservationSummary={store.reservationSummary}
          state={store.state}
          ticket={store.ticket}
          onClearAttachmentError={store.clearAttachmentError}
          onClose={store.close}
          onDraftChange={store.setDraftText}
          onQuickReply={(reply) => void store.sendQuickReply(reply)}
          onRetry={() => void store.retry()}
          onSend={() => void store.submitDraft()}
          onUploadAttachment={store.uploadAttachment}
        />
      )}
      <span className="sr-only" aria-live="polite">
        {store.isOpen ? "Panel asisten reservasi terbuka." : ""}
      </span>
    </>
  );
});

export default ChatWidget;

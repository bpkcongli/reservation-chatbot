"use client";

import { observer } from "mobx-react-lite";
import { useEffect, useRef } from "react";

import ChatLauncher from "@/domain/conversation/components/ChatLauncher";
import ChatPanel from "@/domain/conversation/components/ChatPanel";
import { useChatWidgetStore } from "@/domain/conversation/hooks";

const ChatWidget = observer(() => {
  const store = useChatWidgetStore();
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

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        store.close();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
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
        <ChatPanel closeButtonRef={closeButtonRef} onClose={store.close} />
      )}
      <span className="sr-only" aria-live="polite">
        {store.isOpen ? "Panel asisten reservasi terbuka." : ""}
      </span>
    </>
  );
});

export default ChatWidget;

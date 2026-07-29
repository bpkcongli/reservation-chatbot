"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { ToastContainer } from "react-toastify";

import { getClientEnvironment } from "@/general/interfaces/environment";
import { createRootContainer } from "@/general/services/container";
import { ServiceLocator } from "@/general/services/service-locator";

interface ApplicationProviderProps {
  children: ReactNode;
}

export default function ApplicationProvider({
  children,
}: Readonly<ApplicationProviderProps>) {
  const [environment] = useState(getClientEnvironment);
  const [container] = useState(() => createRootContainer(environment));

  ServiceLocator.setMainContainer(container);

  useEffect(() => {
    if (environment.NEXT_PUBLIC_USE_MOCKS !== "true") {
      return;
    }

    void import("@/general/mocks/browser").then(({ worker }) =>
      worker.start({ onUnhandledRequest: "bypass" }),
    );
  }, [environment.NEXT_PUBLIC_USE_MOCKS]);

  return (
    <>
      {children}
      <ToastContainer
        position="top-right"
        autoClose={4_000}
        newestOnTop
        closeOnClick
        pauseOnFocusLoss
        pauseOnHover
        theme="light"
      />
    </>
  );
}

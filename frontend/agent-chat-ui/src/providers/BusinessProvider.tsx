"use client";

import { createContext, useContext, ReactNode } from "react";

const DEMO_BUSINESS_ID = Number(process.env.NEXT_PUBLIC_DEMO_BUSINESS_ID ?? "1");

const BusinessContext = createContext<number>(DEMO_BUSINESS_ID);

export function BusinessProvider({ children }: { children: ReactNode }) {
  return (
    <BusinessContext.Provider value={DEMO_BUSINESS_ID}>
      {children}
    </BusinessContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useBusinessId() {
  return useContext(BusinessContext);
}

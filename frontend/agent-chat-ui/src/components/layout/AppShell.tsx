"use client";

import React from "react";
import SideNavigation from "./SideNavigation";
import BottomNavigation from "./BottomNavigation";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-full bg-ci-background overflow-hidden">
      <SideNavigation />
      
      <main className="flex-1 md:ml-64 relative flex flex-col h-screen overflow-y-auto overflow-x-hidden pb-20 md:pb-0">
        <div className="flex-1 max-w-4xl mx-auto w-full px-4 md:px-6 lg:px-8 pb-4 md:pb-6 lg:pb-8">
          {children}
        </div>
      </main>

      <BottomNavigation />
    </div>
  );
}

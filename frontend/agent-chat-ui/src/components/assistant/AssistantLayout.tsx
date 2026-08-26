"use client";

import { useState } from "react";
import { useChatHistory } from "@/hooks/useChatHistory";
import AssistantThread from "@/components/assistant/AssistantThread";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Menu, Plus, MessageSquare, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import PageHeader from "@/components/layout/PageHeader";

export default function AssistantLayout() {
  const {
    sessions,
    activeSessionId,
    activeSession,
    isLoaded,
    addMessage,
    createNewSession,
    switchSession,
    deleteSession,
  } = useChatHistory();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Prevent hydration mismatch by returning null until loaded
  if (!isLoaded) return null;

  const sidebarContent = (
    <div className="flex flex-col h-full bg-ci-surface-container-lowest rounded-xl border border-ci-outline-variant overflow-hidden">
      <div className="p-4 shrink-0">
        <Button
          onClick={() => {
            createNewSession();
            setIsMobileMenuOpen(false);
          }}
          className="w-full justify-start gap-2 bg-ci-primary text-ci-on-primary hover:bg-ci-primary-container hover:text-ci-on-primary-container"
        >
          <Plus className="w-4 h-4" />
          New chat
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-ci-outline-variant">
        <div className="text-xs font-semibold text-ci-secondary uppercase tracking-wider mb-2 px-2">
          Recent chats
        </div>

        {sessions.length === 0 ? (
          <div className="px-2 py-3 text-sm text-ci-secondary text-center">
            No previous chats yet.
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            return (
              <div
                key={session.id}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                  isActive
                    ? "bg-ci-primary/10 text-ci-primary"
                    : "hover:bg-ci-surface-container-low text-ci-on-surface"
                }`}
                onClick={() => {
                  switchSession(session.id);
                  setIsMobileMenuOpen(false);
                }}
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <MessageSquare className="w-4 h-4 shrink-0 opacity-70" />
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm font-medium truncate">
                      {session.title}
                    </span>
                    {session.updatedAt && (
                      <span className="text-[10px] opacity-70">
                        {formatDistanceToNow(new Date(session.updatedAt), { addSuffix: true })}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-ci-error/10 hover:text-ci-error rounded-md transition-all shrink-0 ml-2"
                  title="Delete chat"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-6 w-full h-full">
      <PageHeader title="Ask ChatInsights" />

      <div className="flex-1 flex min-h-0 w-full relative">
        {/* Desktop Sidebar */}
        <div className="hidden md:block w-64 shrink-0 h-full border-r border-ci-outline-variant pr-4">
          {sidebarContent}
        </div>

        {/* Main Content Area */}
        <div className="flex-1 min-w-0 flex flex-col h-full relative">
          {/* Mobile Header Trigger */}
          <div className="md:hidden absolute top-0 left-4 z-20">
            <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="bg-ci-surface-container-lowest shadow-sm rounded-full w-10 h-10 border-ci-outline-variant">
                  <Menu className="w-5 h-5 text-ci-on-surface" />
                  <span className="sr-only">Open chat history</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 w-80 max-w-[90vw] border-r-ci-outline-variant bg-ci-surface-container-lowest">
                {sidebarContent}
              </SheetContent>
            </Sheet>
          </div>

          {/* Assistant Thread */}
          <div className="flex-1 w-full h-full">
            <AssistantThread
              messages={activeSession?.messages || []}
              onAddMessage={addMessage}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

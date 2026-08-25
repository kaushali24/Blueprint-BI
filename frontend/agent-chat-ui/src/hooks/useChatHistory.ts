import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { ChatMessage } from "@/components/assistant/AssistantMessage";

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}

const STORAGE_KEY = "chatinsights.assistant.sessions.v1";

export function useChatHistory() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setSessions(parsed);
          if (parsed.length > 0) {
            setActiveSessionId(parsed[0].id);
          }
        }
      }
    } catch (e) {
      console.warn("Failed to load chat history from local storage", e);
    }
    setIsLoaded(true);
  }, []);



  const generateTitle = (text: string) => {
    return text.length > 35 ? text.substring(0, 35) + "..." : text;
  };

  const addMessage = useCallback(
    (message: ChatMessage, explicitSessionId?: string) => {
      // Determine the session ID outside the state updater to return it
      const targetSessionId = explicitSessionId || activeSessionId || uuidv4();

      setSessions((prevSessions) => {
        const now = new Date().toISOString();
        const existingSession = prevSessions.find((s) => s.id === targetSessionId);
        let newSessions: ChatSession[];

        if (!existingSession) {
          const newSession: ChatSession = {
            id: targetSessionId,
            title: message.role === "user" ? generateTitle(message.content) : "New Chat",
            createdAt: now,
            updatedAt: now,
            messages: [message],
          };
          newSessions = [newSession, ...prevSessions];
        } else {
          newSessions = prevSessions.map((session) => {
            if (session.id === targetSessionId) {
              return {
                ...session,
                updatedAt: now,
                title: session.messages.length === 0 && message.role === "user"
                  ? generateTitle(message.content)
                  : session.title,
                messages: [...session.messages, message],
              };
            }
            return session;
          });
          // Move updated session to top
          const updatedSession = newSessions.find((s) => s.id === targetSessionId);
          if (updatedSession) {
            newSessions = [
              updatedSession,
              ...newSessions.filter((s) => s.id !== targetSessionId),
            ];
          }
        }

        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newSessions));
        } catch (e) {
          console.warn("Failed to save to local storage", e);
        }

        return newSessions;
      });

      // Update active session if it was newly created or different
      if (activeSessionId !== targetSessionId) {
        setActiveSessionId(targetSessionId);
      }

      return targetSessionId;
    },
    [activeSessionId],
  );

  const createNewSession = useCallback(() => {
    // Clean up empty sessions
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.messages.length > 0);

      const newSession: ChatSession = {
        id: uuidv4(),
        title: "New Chat",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: [],
      };

      const newSessions = [newSession, ...filtered];

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newSessions));
      } catch {
        // ignore
      }

      setActiveSessionId(newSession.id);
      return newSessions;
    });
  }, []);

  const switchSession = useCallback((id: string) => {
    setActiveSessionId(id);
  }, []);

  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const newSessions = prev.filter((s) => s.id !== id);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(newSessions));
        } catch {
          // ignore
        }

        if (activeSessionId === id) {
          if (newSessions.length > 0) {
            setActiveSessionId(newSessions[0].id);
          } else {
            setActiveSessionId(null);
          }
        }

        return newSessions;
      });
    },
    [activeSessionId],
  );

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  return {
    sessions,
    activeSessionId,
    activeSession,
    isLoaded,
    addMessage,
    createNewSession,
    switchSession,
    deleteSession,
  };
}

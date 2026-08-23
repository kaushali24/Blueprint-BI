import { format, isToday, isYesterday, parseISO } from "date-fns";

export function formatOrderDate(dateString: string): string {
  try {
    const date = parseISO(dateString);
    if (Number.isNaN(date.getTime())) {
      return dateString;
    }
    if (isToday(date)) return "Today";
    if (isYesterday(date)) return "Yesterday";
    return format(date, "MMM d");
  } catch {
    return dateString;
  }
}

export function formatOrderDetailDate(dateString: string): string {
  try {
    const date = parseISO(dateString);
    if (Number.isNaN(date.getTime())) {
      return dateString;
    }
    return format(date, "MMM d, yyyy");
  } catch {
    return dateString;
  }
}

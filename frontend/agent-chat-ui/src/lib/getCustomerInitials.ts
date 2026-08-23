export function getCustomerInitials(customerName: string | null): string {
  if (!customerName?.trim()) return "?";

  const parts = customerName.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return parts[0][0]?.toUpperCase() ?? "?";
}

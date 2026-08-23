"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icons, IconName } from "@/lib/icons";

const NAV_ITEMS = [
  { name: "Overview", href: "/overview", icon: "dashboard" as IconName },
  { name: "Imports", href: "/imports", icon: "upload_file" as IconName },
  { name: "Orders", href: "/orders", icon: "shopping_bag" as IconName },
  { name: "Inquiries", href: "/inquiries", icon: "forum" as IconName },
  { name: "Assistant", href: "/assistant", icon: "smart_toy" as IconName },
];

export default function BottomNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="Main navigation" className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-ci-surface-container border-t border-ci-outline-variant px-2 py-2 pb-safe">
      <ul className="flex items-center justify-between">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = Icons[item.icon];
          
          return (
            <li key={item.name} className="flex-1">
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className="flex flex-col items-center justify-center py-1 outline-none rounded-xl focus-visible:ring-2 focus-visible:ring-ci-primary focus-visible:ring-offset-2 focus-visible:ring-offset-ci-surface-container"
              >
                <div className={`flex items-center justify-center w-16 h-8 rounded-full mb-1 transition-colors ${isActive ? 'bg-ci-primary-container text-ci-on-primary-container' : 'text-ci-on-surface-variant hover:bg-ci-surface-container-high'}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={`text-[11px] font-medium transition-colors ${isActive ? 'text-ci-on-surface' : 'text-ci-on-surface-variant'}`}>
                  {item.name}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

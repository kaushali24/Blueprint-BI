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

export default function SideNavigation() {
  const pathname = usePathname();

  return (
    <nav aria-label="Main navigation" className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 bg-ci-surface-container border-r border-ci-outline-variant p-4 z-50">
      <div className="flex items-center gap-2 px-4 py-6 mb-4">
        <Icons.analytics className="w-6 h-6 text-ci-primary" />
        <span className="text-lg font-bold text-ci-on-surface">ChatInsights</span>
      </div>
      
      <ul className="flex flex-col gap-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = Icons[item.icon];
          
          return (
            <li key={item.name}>
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`flex items-center gap-4 px-4 py-3 rounded-full transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ci-primary ${
                  isActive
                    ? 'bg-ci-primary-container text-ci-on-primary-container'
                    : 'text-ci-on-surface-variant hover:bg-ci-surface-container-high'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="font-semibold text-sm">
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

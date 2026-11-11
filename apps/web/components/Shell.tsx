import Link from "next/link";

export function Shell({
  children,
  current,
}: {
  children: React.ReactNode;
  current: "desk" | "inbox" | "audit";
}) {
  return (
    <div className="frame">
      <header className="topbar">
        <div>
          <p className="eyebrow">Pinnacle Marketing · internal</p>
          <h1>PinnacleOS</h1>
        </div>
        <p className="phase-pill">Phase 3 · read-only foundation</p>
      </header>
      <nav className="nav">
        <Link className={current === "desk" ? "active" : ""} href="/">
          Desk
        </Link>
        <Link className={current === "inbox" ? "active" : ""} href="/inbox">
          Inbox
        </Link>
        <Link className={current === "audit" ? "active" : ""} href="/audit">
          Audit
        </Link>
      </nav>
      <main>{children}</main>
    </div>
  );
}

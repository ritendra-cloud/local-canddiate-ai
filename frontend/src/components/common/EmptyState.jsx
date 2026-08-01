export default function EmptyState({ title, children, action }) { return <section className="empty-state"><h2>{title}</h2><p>{children}</p>{action}</section>; }

import JobsList from '@/components/JobsList';
import Link from 'next/link';

export default function JobsPage() {
  return (
    <div className="panel">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Recent jobs</div>
          <div className="small">Shows live backend jobs when available; otherwise empty.</div>
        </div>
        <Link href="/jobs/new">
          <button className="primary">Create job</button>
        </Link>
      </div>
      <div style={{ height: 12 }} />
      <JobsList />
    </div>
  );
}

import CreateJob from '@/components/CreateJob';

export default function CreateJobPage() {
  return (
    <div className="panel">
      <div style={{ fontSize: 18, fontWeight: 700 }}>Create job</div>
      <div className="small">Upload a job.json and one or more render images, then run the pipeline.</div>
      <div style={{ height: 12 }} />
      <CreateJob />
    </div>
  );
}

import { Construction } from 'lucide-react';

function PlaceholderPage({ title, description }: { title: string, description: string }) {
  return (
    <div className="h-[80vh] flex flex-col items-center justify-center text-center">
      <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-6 border border-primary/20">
        <Construction className="w-10 h-10 text-primary" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight mb-2">{title}</h1>
      <p className="text-muted-foreground max-w-md">{description}</p>
    </div>
  );
}

export const Analytics = () => <PlaceholderPage title="Analytics" description="Historical analysis and demographic trends will be displayed here." />;
export const Incidents = () => <PlaceholderPage title="Incident History" description="A complete log of all past stamped alerts and manual interventions." />;
export const Cameras = () => <PlaceholderPage title="Camera Management" description="Configure CCTV feeds, RSTP streams, and mapping." />;
export const Health = () => <PlaceholderPage title="System Health" description="Detailed server metrics, node status, and infrastructure monitoring." />;
export const Settings = () => <PlaceholderPage title="Settings" description="Global application settings, user management, and notification preferences." />;

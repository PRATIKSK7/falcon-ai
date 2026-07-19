import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { LiveMonitor } from './pages/LiveMonitor';
import { AiModel } from './pages/AiModel';
import { Analytics, Incidents, Cameras, Health, Settings } from './pages/Placeholders';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="monitor" element={<LiveMonitor />} />
            <Route path="ai-model" element={<AiModel />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="cameras" element={<Cameras />} />
            <Route path="health" element={<Health />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

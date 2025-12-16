import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { App } from './ui/App';
import { Landing } from './ui/Landing';
import { DashboardPage } from './ui/pages/DashboardPage';
import { WorkflowPage } from './ui/pages/WorkflowPage';
import { ApiProvider } from './ui/api/ApiProvider';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <ApiProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<App />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/workflow/:workflowId" element={<WorkflowPage />} />
        </Routes>
      </ApiProvider>
    </BrowserRouter>
  </React.StrictMode>,
);

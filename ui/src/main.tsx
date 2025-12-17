import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Landing } from './ui/Landing';
import { DashboardPage } from './ui/pages/DashboardPage';
import { WorkflowPage } from './ui/pages/WorkflowPage';
import { ApiProvider } from './ui/api/ApiProvider';
import './index.css';

// 3 clean routes:
// 1. / - Landing page (marketing)
// 2. /dashboard - Dashboard with workflow list + create form
// 3. /workflow/:id - Individual workflow view (chapters/pages)

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <ApiProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/workflow/:workflowId" element={<WorkflowPage />} />
          {/* Redirect old /app route to /dashboard */}
          <Route path="/app" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </ApiProvider>
    </BrowserRouter>
  </React.StrictMode>,
);

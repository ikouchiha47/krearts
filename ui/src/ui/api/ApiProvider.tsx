import React, { createContext, useContext, useMemo } from 'react';
import type { ApiClient } from './ApiClient';
import { RealApiClient } from './RealApiClient';

const ApiContext = createContext<ApiClient | null>(null);

export const ApiProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const client = useMemo<ApiClient>(() => new RealApiClient(), []);
  return <ApiContext.Provider value={client}>{children}</ApiContext.Provider>;
};

export function useApi(): ApiClient {
  const ctx = useContext(ApiContext);
  if (!ctx) {
    throw new Error('useApi must be used within ApiProvider');
  }
  return ctx;
}

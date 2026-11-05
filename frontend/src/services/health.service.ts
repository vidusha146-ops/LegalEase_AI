import { apiClient } from './api';
import type { HealthStatus } from '../types/health';

export const healthService = {
  async getHealth(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>('/health');
    return response.data;
  },
};

export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  database_status: string;
  version: string;
  indian_legal_advisory: string;
  helplines: Record<string, string>;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  available: boolean;
  description?: string;
  is_default?: boolean;
}

export interface ModelGroup {
  provider: string;
  models: Model[];
}

import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AIHealthResponse {
  backend_running: boolean;
  tensorflow_loaded: boolean;
  model_loaded: boolean;
  opencv_available: boolean;
  twilio_configured: boolean;
  gpu_cpu_status: string;
  api_version: string;
}

export interface AIPredictResponse {
  status: string;
  prediction: string;
  reconstruction_error: number;
  threshold: number;
  processing_time: string;
  timestamp: string;
  model_version: string;
  frame?: number;
  is_stream?: boolean;
}

export const aiService = {
  getHealth: async (): Promise<AIHealthResponse> => {
    const { data } = await apiClient.get('/api/v1/ai/health');
    return data;
  },
  
  predict: async (file: File): Promise<AIPredictResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post('/api/v1/ai/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  }
};

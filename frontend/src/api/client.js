import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const simulationApi = {
  getStatus: () => api.get('/status'),
  start: (scenario_id) => api.post('/simulation/start', { scenario_id }),
  stop: () => api.post('/simulation/stop'),
  step: () => api.post('/simulation/step'),
  getState: () => api.get('/simulation/state'),
};

export default api;

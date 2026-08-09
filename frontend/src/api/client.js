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
  injectAction: (agent_id, action) => api.post('/simulation/inject-action', { agent_id, action }),
};

export const xaiApi = {
  getAgentBeliefs: (agentId) => api.get(`/agents/${agentId}/beliefs`),
  getMCTSBranches: (agentId) => api.get(`/agents/${agentId}/mcts-branches`),
  getAgentLogs: (agentId) => api.get(`/agents/${agentId}/logs`),
};

export const analysisApi = {
  run: (type, params = {}) => api.post('/analysis/run', { type, params }),
};

export const economicsApi = {
  getChokepoints: () => api.get('/economics/chokepoints'),
};

export const wargameApi = {
  runWargame: (steps = 5) => api.post(`/wargame/run?steps=${steps}`),
};

export const swarmApi = {
  deliberate: (actorId = 'BlueLand') => api.post(`/swarm/deliberate?actor_id=${actorId}`),
};

export const epidemiologyApi = {
  getTrajectoryPlot: () => api.get('/epidemiology/trajectory'),
};

export const mapApi = {
  getGeoJSON: () => api.get('/map/geojson'),
};

export default api;

import { useState, useEffect, useCallback } from 'react';
import { simulationApi } from '../api/client';

export function useSimulation(autoRefreshInterval = 0) {
  const [isRunning, setIsRunning] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [error, setError] = useState(null);
  
  const fetchState = useCallback(async () => {
    try {
      const res = await simulationApi.getState();
      setGameState(res.data);
      setIsRunning(true);
      setError(null);
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.detail === "Model not initialized") {
        setIsRunning(false);
        setGameState(null);
      } else {
        setError(err.message);
      }
    }
  }, []);

  const start = async (scenarioId) => {
    try {
      await simulationApi.start(scenarioId);
      setIsRunning(true);
      await fetchState();
    } catch (err) {
      setError(err.message);
    }
  };

  const stop = async () => {
    try {
      await simulationApi.stop();
      setIsRunning(false);
      setGameState(null);
    } catch (err) {
      setError(err.message);
    }
  };

  const step = async () => {
    try {
      await simulationApi.step();
      await fetchState();
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (autoRefreshInterval > 0 && isRunning) {
      const interval = setInterval(step, autoRefreshInterval); // Let's auto-step
      return () => clearInterval(interval);
    }
  }, [autoRefreshInterval, isRunning]);

  // Initial fetch check
  useEffect(() => {
    fetchState();
  }, [fetchState]);

  return { isRunning, gameState, error, start, stop, step, fetchState };
}

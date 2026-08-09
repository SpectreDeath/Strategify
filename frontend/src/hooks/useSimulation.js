import { useState, useEffect, useCallback, useRef } from 'react';
import { simulationApi } from '../api/client';

const MAX_HISTORY = 200;

export function useSimulation(autoRefreshInterval = 0) {
  const [isRunning, setIsRunning] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const lastStepRef = useRef(-1);

  const fetchState = useCallback(async () => {
    try {
      const res = await simulationApi.getState();
      const data = res.data;
      setGameState(data);
      setIsRunning(true);
      setError(null);

      // Accumulate history — only push when step advances
      if (data.step !== lastStepRef.current) {
        lastStepRef.current = data.step;
        setHistory(prev => {
          const next = [...prev, {
            step: data.step,
            tension: parseFloat((data.global_tension * 100).toFixed(1)),
          }];
          return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
        });
      }
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.detail === 'Model not initialized') {
        setIsRunning(false);
        setGameState(null);
      } else {
        setError(err.message);
      }
    }
  }, []);

  const start = async (scenarioId) => {
    try {
      setHistory([]); // reset history on new scenario
      lastStepRef.current = -1;
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
      const interval = setInterval(step, autoRefreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefreshInterval, isRunning]);

  // Initial fetch check
  useEffect(() => {
    fetchState();
  }, [fetchState]);

  return { isRunning, gameState, history, error, start, stop, step, fetchState };
}

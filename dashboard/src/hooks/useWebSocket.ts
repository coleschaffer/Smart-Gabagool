'use client';

import { useEffect, useState, useCallback } from 'react';
import { WebSocketMessage } from '@/types';

export function useWebSocket(url?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const wsUrl = url || (typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
    : 'ws://localhost:8000/ws');

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 5000);
      };

      setWs(socket);
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnected(false);
      // Retry connection after 5 seconds
      setTimeout(connect, 5000);
    }
  }, [wsUrl]);

  useEffect(() => {
    connect();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (ws && isConnected) {
      ws.send(JSON.stringify(message));
    }
  }, [ws, isConnected]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
  };
}

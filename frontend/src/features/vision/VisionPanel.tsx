import React, { useEffect, useState, useRef } from 'react';
import Card from '../../components/Card';
import { getVisionSnapshotUrl, getVisionWebSocketUrl } from '../../lib/api';
import type { VisionIntent } from '../../lib/types';

interface VisionPanelProps {
  showPreview?: boolean;
}

export const VisionPanel: React.FC<VisionPanelProps> = ({
  showPreview = true,
}) => {
  const [latestIntent, setLatestIntent] = useState<VisionIntent | null>(null);
  const [fps, setFps] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const lastUpdateRef = useRef<number>(Date.now());

  useEffect(() => {
    const ws = new WebSocket(getVisionWebSocketUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Vision WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const intent: VisionIntent = JSON.parse(event.data);
        setLatestIntent(intent);

        // Calculate FPS
        const now = Date.now();
        const delta = now - lastUpdateRef.current;
        if (delta > 0) {
          setFps(Math.round(1000 / delta));
        }
        lastUpdateRef.current = now;
      } catch (error) {
        console.error('Failed to parse vision intent:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Vision WebSocket error:', error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('Vision WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <Card title='Vision' className='h-full'>
      <div className='space-y-3'>
        {showPreview && (
          <div className='relative'>
            <img
              src={getVisionSnapshotUrl()}
              alt='Vision snapshot'
              className='w-full rounded-md'
            />
            <div className='absolute top-2 right-2 bg-black bg-opacity-60 text-white px-2 py-1 rounded text-xs'>
              {fps} FPS
            </div>
          </div>
        )}

        <div className='space-y-2 text-sm'>
          <div className='flex justify-between'>
            <span className='text-gray-600 dark:text-gray-400'>Status:</span>
            <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
              {isConnected ? '● Connected' : '○ Disconnected'}
            </span>
          </div>

          {latestIntent && (
            <>
              <div className='flex justify-between'>
                <span className='text-gray-600 dark:text-gray-400'>
                  Gesture:
                </span>
                <span className='font-medium'>{latestIntent.gesture}</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600 dark:text-gray-400'>
                  Confidence:
                </span>
                <span>{(latestIntent.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className='flex justify-between'>
                <span className='text-gray-600 dark:text-gray-400'>Armed:</span>
                <span>{latestIntent.armed ? '✓' : '✗'}</span>
              </div>
              <div className='text-xs text-gray-500 dark:text-gray-500 mt-2'>
                Last update: {new Date(latestIntent.tsISO).toLocaleTimeString()}
              </div>
            </>
          )}
        </div>
      </div>
    </Card>
  );
};

export default VisionPanel;

import React, { useEffect, useState, useRef } from 'react';
import Card from '../../components/Card';
import { getVisionWebSocketUrl } from '../../lib/api';
import type { VisionIntent } from '../../lib/types';

interface VisionPanelProps {
  showPreview?: boolean;
  compact?: boolean;
}

export const VisionPanel: React.FC<VisionPanelProps> = ({
  showPreview = true,
  compact = false,
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
      <div className='space-y-4'>
        {showPreview && (
          <div className='relative'>
            <img
              src={getVisionWebSocketUrl()}
              alt='Vision snapshot'
              className='w-full rounded-lg border border-[#27272a]'
            />
            <div className='absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-mono'>
              {fps} FPS
            </div>
            <div
              className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-medium ${
                isConnected
                  ? 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30'
                  : 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30'
              }`}
            >
              <span className='inline-block w-1.5 h-1.5 rounded-full bg-current mr-1.5' />
              {isConnected ? 'Live' : 'Offline'}
            </div>
          </div>
        )}

        {!compact && latestIntent && (
          <div className='grid grid-cols-2 gap-3 text-sm'>
            <div className='bg-[#18181b] border border-[#27272a] rounded-lg p-3'>
              <div className='text-[#71717a] text-xs mb-1'>Gesture</div>
              <div className='text-[#e4e4e7] font-medium'>
                {latestIntent.gesture}
              </div>
            </div>
            <div className='bg-[#18181b] border border-[#27272a] rounded-lg p-3'>
              <div className='text-[#71717a] text-xs mb-1'>Confidence</div>
              <div className='text-[#e4e4e7] font-medium font-mono'>
                {(latestIntent.confidence * 100).toFixed(0)}%
              </div>
            </div>
            <div className='bg-[#18181b] border border-[#27272a] rounded-lg p-3'>
              <div className='text-[#71717a] text-xs mb-1'>Armed</div>
              <div className='text-[#e4e4e7] font-medium'>
                {latestIntent.armed ? 'Yes' : 'No'}
              </div>
            </div>
            <div className='bg-[#18181b] border border-[#27272a] rounded-lg p-3'>
              <div className='text-[#71717a] text-xs mb-1'>Updated</div>
              <div className='text-[#e4e4e7] font-medium text-xs'>
                {new Date(latestIntent.tsISO).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default VisionPanel;

import { DWELL_MS_DEFAULT } from './constants';

export interface DwellState {
  targetId: string | null;
  startTime: number | null;
  progress: number; // 0-1
}

export class DwellTracker {
  private state: DwellState = {
    targetId: null,
    startTime: null,
    progress: 0,
  };
  private dwellMs: number = DWELL_MS_DEFAULT;
  private callback: ((targetId: string) => void) | null = null;
  private animationFrame: number | null = null;

  constructor(dwellMs: number = DWELL_MS_DEFAULT) {
    this.dwellMs = dwellMs;
  }

  setDwellTime(ms: number): void {
    this.dwellMs = ms;
  }

  onDwellComplete(callback: (targetId: string) => void): void {
    this.callback = callback;
  }

  start(targetId: string): void {
    if (this.state.targetId === targetId && this.state.startTime !== null) {
      // Already tracking this target
      return;
    }

    this.stop();
    this.state = {
      targetId,
      startTime: Date.now(),
      progress: 0,
    };

    this.update();
  }

  stop(): void {
    if (this.animationFrame !== null) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }

    if (this.state.targetId !== null && this.state.startTime !== null) {
      // Reset progress but keep target for smooth transition
      this.state.progress = 0;
    }

    this.state.targetId = null;
    this.state.startTime = null;
  }

  private update = (): void => {
    if (this.state.targetId === null || this.state.startTime === null) {
      return;
    }

    const elapsed = Date.now() - this.state.startTime;
    this.state.progress = Math.min(elapsed / this.dwellMs, 1);

    if (this.state.progress >= 1 && this.callback) {
      // Dwell complete
      this.callback(this.state.targetId);
      this.stop();
      return;
    }

    this.animationFrame = requestAnimationFrame(this.update);
  };

  getProgress(): number {
    return this.state.progress;
  }

  getTargetId(): string | null {
    return this.state.targetId;
  }

  isTracking(): boolean {
    return this.state.targetId !== null && this.state.startTime !== null;
  }
}



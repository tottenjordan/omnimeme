export interface GuidedInput {
  subject: string;
  action?: string;
  camera?: string;
  lighting?: string;
  style?: string;
  audio?: string;
  duration_sec?: number;
  aspect_ratio?: string;
}

export interface FreeformInput {
  raw_prompt: string;
  director_style_preference?: string;
}

export interface VideoConfig {
  model: string;
  prompt: string;
  parameters: {
    duration_seconds: number;
    aspect_ratio: string;
    fps: number;
  };
}

export interface DirectingResponse {
  interface: string;
  status: string;
  result: {
    agent_name: string;
    model: string;
    enhanced_prompt: string;
    video_config: VideoConfig;
  };
  error_message?: string;
}

const API_BASE = '/api';

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function enhanceGuided(data: GuidedInput): Promise<DirectingResponse> {
  const res = await fetch(`${API_BASE}/guided/enhance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to enhance prompt' }));
    throw new Error(errorData.detail || 'Failed to process guided request');
  }
  return res.json();
}

export async function enhanceFreeform(data: FreeformInput): Promise<DirectingResponse> {
  const res = await fetch(`${API_BASE}/freeform/enhance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to enhance prompt' }));
    throw new Error(errorData.detail || 'Failed to process freeform request');
  }
  return res.json();
}

async function handleStream(
  url: string,
  payload: any,
  onToken: (chunk: string) => void,
  onDone: (result: DirectingResponse) => void,
  onError: (err: Error) => void
) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Stream request failed' }));
      throw new Error(errorData.detail || 'Stream request failed');
    }
    const reader = res.body?.getReader();
    if (!reader) throw new Error('ReadableStream not supported');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          try {
            const dataStr = trimmed.replace(/^data:\s*/, '');
            const parsed = JSON.parse(dataStr);
            if (parsed.type === 'token') {
              onToken(parsed.chunk);
            } else if (parsed.type === 'done') {
              onDone({
                interface: 'stream',
                status: 'success',
                result: parsed.result,
              });
            }
          } catch (e) {
            // ignore partial parse errors
          }
        }
      }
    }
  } catch (err: any) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

export function streamGuided(
  data: GuidedInput,
  onToken: (chunk: string) => void,
  onDone: (result: DirectingResponse) => void,
  onError: (err: Error) => void
) {
  return handleStream(`${API_BASE}/guided/stream`, data, onToken, onDone, onError);
}

export function streamFreeform(
  data: FreeformInput,
  onToken: (chunk: string) => void,
  onDone: (result: DirectingResponse) => void,
  onError: (err: Error) => void
) {
  return handleStream(`${API_BASE}/freeform/stream`, data, onToken, onDone, onError);
}


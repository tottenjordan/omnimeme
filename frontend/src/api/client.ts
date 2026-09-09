export interface MediaAttachment {
  uri: string;
  mime_type: string;
  description?: string;
}

export interface CharacterRole {
  role_id: string;
  name: string;
  description: string;
  turnaround_sheet_url?: string;
  aesthetic_tags?: string[];
  voice_style?: string;
  wardrobe?: string;
  image_role?: string;
  image_tag?: string;
}

export interface GuidedInput {
  character_role_id?: string;
  subject: string;
  action?: string;
  camera?: string;
  lighting?: string;
  style?: string;
  audio?: string;
  duration_sec?: number;
  aspect_ratio?: string;
  resolution?: string;
  first_frame_uri?: string;
  last_frame_uri?: string;
  reference_images?: MediaAttachment[];
  reference_videos?: MediaAttachment[];
  motion_preset?: string;
}

export interface FreeformInput {
  character_role_id?: string;
  raw_prompt: string;
  director_style_preference?: string;
  resolution?: string;
  first_frame_uri?: string;
  last_frame_uri?: string;
  reference_images?: MediaAttachment[];
  reference_videos?: MediaAttachment[];
  motion_preset?: string;
}

export interface VideoConfig {
  model: string;
  prompt: string;
  parameters: {
    duration_seconds: number;
    aspect_ratio: string;
    fps: number;
    resolution?: string;
    first_frame_uri?: string;
    last_frame_uri?: string;
    motion_preset?: string;
  };
  resolution?: string;
  first_frame_uri?: string;
  last_frame_uri?: string;
  reference_assets?: MediaAttachment[];
  motion_preset?: string;
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

export interface GenerationResult {
  interaction_thread_id: string;
  video_url: string;
  gcs_uri?: string;
  duration_seconds: number;
  synth_id_watermark: string;
  status: string;
  error_message?: string;
  generation_mode: string;
}

export interface ProductInfo {
  name: string;
  description?: string;
  image_url?: string;
  tagline?: string;
}

export interface MashupRequest {
  character_a_id: string;
  character_b_id: string;
  mashup_genre?: string;
  parody_tone?: string;
  product?: ProductInfo;
  scene_count?: number;
}

export interface MashupBundle {
  id: string;
  title: string;
  description: string;
  character_a: CharacterRole;
  character_b: CharacterRole;
  mashup_genre: string;
  parody_tone: string;
  product?: ProductInfo;
}

export interface StoryboardScene {
  scene_number: number;
  title: string;
  visual_description: string;
  camera_instruction: string;
  audio_cue: string;
  character_role_id?: string;
  lower_third_title?: { name: string; role?: string };
  video_config: VideoConfig;
  is_chained?: boolean;
  video_url?: string;
  interaction_id?: string;
  turn_number?: number;
  duration_seconds?: number;
  status?: string;
  generation_mode?: string;
}

export interface StoryboardResponse {
  status: string;
  storyboard: {
    concept: string;
    scene_count: number;
    style_preference: string;
    character_role_id?: string;
    character_a_id?: string;
    character_b_id?: string;
    mashup_genre?: string;
    parody_tone?: string;
    product?: ProductInfo;
    scenes: StoryboardScene[];
  };
  error_message?: string;
}


const API_BASE = '/api';


export async function checkHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function executeVideoGeneration(
  config: VideoConfig,
  previousInteractionId?: string,
  mockMode?: boolean
): Promise<GenerationResult> {
  const res = await fetch(`${API_BASE}/generate-video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_config: config,
      previous_interaction_id: previousInteractionId,
      mock_mode: mockMode,
    }),
  });
  if (!res.ok) throw new Error('Video generation failed');
  return res.json();
}

export async function submitUserFeedback(data: {
  interaction_thread_id: string;
  rating: number;
  feedback_type?: string;
  comment?: string;
  prompt?: string;
}): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to submit user feedback');
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
    }).catch((fetchErr) => {
      throw new Error('FastAPI backend connection error. Ensure uvicorn is running with: uv run uvicorn omnimeme.server.app:app --port 8000');
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'FastAPI backend connection error. Ensure uvicorn is running with: uv run uvicorn omnimeme.server.app:app --port 8000' }));
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

export async function fetchVaultCharacters(): Promise<CharacterRole[]> {
  const res = await fetch(`${API_BASE}/vault/characters`);
  if (!res.ok) throw new Error('Failed to fetch character vault');
  return res.json();
}

export async function createVaultCharacter(char: Partial<CharacterRole>): Promise<CharacterRole> {
  const res = await fetch(`${API_BASE}/vault/characters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(char),
  });
  if (!res.ok) throw new Error('Failed to create character');
  return res.json();
}

export async function deleteVaultCharacter(roleId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/vault/characters/${roleId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete character');
  return res.json();
}

export function getThumbnailUrl(uri?: string): string {
  if (!uri) return '';
  if (uri.startsWith('http://') || uri.startsWith('https://')) return uri;
  return `${API_BASE}/gcs/proxy?uri=${encodeURIComponent(uri)}`;
}

export async function generateTurnaroundSheet(roleId: string, referenceImageUrl?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/vault/characters/${roleId}/turnaround`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reference_image_url: referenceImageUrl }),
  });
  if (!res.ok) throw new Error('Failed to generate turnaround sheet');
  return res.json();
}

export interface CharacterArchetypePreset {
  role_id: string;
  name: string;
  description: string;
  aesthetic_tags: string[];
  voice_style: string;
  wardrobe: string;
  image_role: string;
}

export async function generateStoryboard(data: {
  concept: string;
  scene_count?: number;
  style_preference?: string;
  character_role_id?: string;
}): Promise<StoryboardResponse> {
  const res = await fetch(`${API_BASE}/scriptwriting/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to generate storyboard' }));
    throw new Error(errorData.detail || 'Failed to generate storyboard');
  }
  return res.json();
}

export async function generateMashupStoryboard(data: MashupRequest): Promise<StoryboardResponse> {
  const res = await fetch(`${API_BASE}/scriptwriting/mashup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to generate mashup storyboard' }));
    throw new Error(errorData.detail || 'Failed to generate mashup storyboard');
  }
  return res.json();
}

export async function fetchMashupBundles(): Promise<MashupBundle[]> {
  const res = await fetch(`${API_BASE}/vault/mashup-bundles`);
  if (!res.ok) throw new Error('Failed to fetch mashup bundles');
  return res.json();
}

export async function fetchArchetypePresets(): Promise<CharacterArchetypePreset[]> {
  const res = await fetch(`${API_BASE}/vault/archetypes`);
  if (!res.ok) throw new Error('Failed to fetch character archetype presets');
  return res.json();
}

export async function concatenateMasterFilm(
  videoUrls: string[],
  outputFilename?: string,
  lowerThirdTitles?: Record<string, string>[],
  productSponsorCallout?: string
): Promise<{ status: string; master_video_url: string }> {
  const res = await fetch(`${API_BASE}/scriptwriting/concatenate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_urls: videoUrls,
      output_filename: outputFilename,
      lower_third_titles: lowerThirdTitles,
      product_sponsor_callout: productSponsorCallout,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to concatenate master film' }));
    throw new Error(errorData.detail || 'Failed to concatenate master film');
  }
  return res.json();
}

export async function renderChainedStoryboard(
  scenes: StoryboardScene[],
  resolution?: string,
  mockMode?: boolean
): Promise<{ status: string; scenes: StoryboardScene[]; total_scenes: number; cumulative_duration_seconds: number }> {
  const res = await fetch(`${API_BASE}/scriptwriting/render-chained`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenes,
      resolution: resolution || '720p',
      mock_mode: mockMode,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to render chained storyboard' }));
    throw new Error(errorData.detail || 'Failed to render chained storyboard');
  }
  return res.json();
}





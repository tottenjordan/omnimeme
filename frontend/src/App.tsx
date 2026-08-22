import { useState, useEffect } from 'react';
import {
  Video,
  Clapperboard,
  Sparkles,
  Sliders,
  FileText,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Play,
  Image,
  Film,
  Plus,
  Trash2
} from 'lucide-react';
import {
  checkHealth,
  GuidedInput,
  FreeformInput,
  DirectingResponse,
  MediaAttachment
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState<'guided' | 'freeform'>('guided');
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DirectingResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Guided Experience State
  const [guidedInput, setGuidedInput] = useState<GuidedInput>({
    subject: 'A cyberpunk samurai standing under neon cherry blossoms',
    action: 'Slowly drawing a glowing katana as rain falls',
    camera: 'Low angle 35mm steadycam tracking push-in',
    lighting: 'Volumetric cyan and magenta neon reflections in water puddles',
    style: 'Photorealistic, cinematic film grain, dark fantasy thriller',
    audio: 'Ambient synth drone, gentle rain patter, metallic unsheathing sound',
    duration_sec: 5,
    aspect_ratio: '16:9',
    reference_images: [],
    reference_videos: []
  });

  // Free-form State
  const [freeformInput, setFreeformInput] = useState<FreeformInput>({
    raw_prompt: 'A golden retriever wearing aviator sunglasses riding a skateboard down a sunlit hill',
    director_style_preference: 'Upbeat commercial 4K high speed video',
    reference_images: [],
    reference_videos: []
  });

  // Temporary input state for attachments
  const [newImageUri, setNewImageUri] = useState('');
  const [newImageDesc, setNewImageDesc] = useState('');
  const [newVideoUri, setNewVideoUri] = useState('');
  const [newVideoDesc, setNewVideoDesc] = useState('');

  useEffect(() => {
    checkHealth()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false));
  }, []);

  const [streamingText, setStreamingText] = useState<string>('');

  const addGuidedImage = () => {
    if (!newImageUri.trim()) return;
    const attachment: MediaAttachment = {
      uri: newImageUri.trim(),
      mime_type: newImageUri.endsWith('.png') ? 'image/png' : 'image/jpeg',
      description: newImageDesc.trim() || 'Style Reference'
    };
    setGuidedInput({
      ...guidedInput,
      reference_images: [...(guidedInput.reference_images || []), attachment]
    });
    setNewImageUri('');
    setNewImageDesc('');
  };

  const addGuidedVideo = () => {
    if (!newVideoUri.trim()) return;
    const attachment: MediaAttachment = {
      uri: newVideoUri.trim(),
      mime_type: 'video/mp4',
      description: newVideoDesc.trim() || 'Motion Reference'
    };
    setGuidedInput({
      ...guidedInput,
      reference_videos: [...(guidedInput.reference_videos || []), attachment]
    });
    setNewVideoUri('');
    setNewVideoDesc('');
  };

  const addFreeformImage = () => {
    if (!newImageUri.trim()) return;
    const attachment: MediaAttachment = {
      uri: newImageUri.trim(),
      mime_type: newImageUri.endsWith('.png') ? 'image/png' : 'image/jpeg',
      description: newImageDesc.trim() || 'Concept Art'
    };
    setFreeformInput({
      ...freeformInput,
      reference_images: [...(freeformInput.reference_images || []), attachment]
    });
    setNewImageUri('');
    setNewImageDesc('');
  };

  const handleGuidedSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!guidedInput.subject.trim()) {
      setError('Subject field is required for Guided Directing.');
      return;
    }
    setLoading(true);
    setError(null);
    setStreamingText('');
    setResult(null);

    import('./api/client').then(({ streamGuided }) => {
      streamGuided(
        guidedInput,
        (chunk) => {
          setStreamingText((prev) => prev + chunk);
        },
        (res) => {
          setResult(res);
          setLoading(false);
        },
        (err) => {
          setError(err.message || 'Error streaming guided directing request');
          setLoading(false);
        }
      );
    });
  };

  const handleFreeformSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!freeformInput.raw_prompt.trim()) {
      setError('Raw prompt is required for Free-form Directing.');
      return;
    }
    setLoading(true);
    setError(null);
    setStreamingText('');
    setResult(null);

    import('./api/client').then(({ streamFreeform }) => {
      streamFreeform(
        freeformInput,
        (chunk) => {
          setStreamingText((prev) => prev + chunk);
        },
        (res) => {
          setResult(res);
          setLoading(false);
        },
        (err) => {
          setError(err.message || 'Error streaming freeform directing request');
          setLoading(false);
        }
      );
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-title">
          <Clapperboard size={28} color="#60a5fa" />
          <span>OmniMeme Director Studio</span>
        </div>
        <div className="status-badge">
          <span className={`status-dot ${apiConnected === false ? 'bg-red-500' : ''}`} />
          {apiConnected === null
            ? 'Connecting...'
            : apiConnected
            ? 'ADK & Gemini Platform Ready'
            : 'FastAPI Offline (Local Simulation Active)'}
        </div>
      </header>

      {/* Mode Switcher Tabs */}
      <div className="tab-container">
        <button
          className={`tab-button ${activeTab === 'guided' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('guided');
            setError(null);
          }}
        >
          <Sliders size={16} />
          Guided Directing Experience
        </button>
        <button
          className={`tab-button ${activeTab === 'freeform' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('freeform');
            setError(null);
          }}
        >
          <FileText size={16} />
          Free-form Text Widget
        </button>
      </div>

      {/* Main Content Grid */}
      <div className="main-grid">
        {/* Left Column: Directing Inputs */}
        <div className="card-panel">
          <div className="panel-header">
            <h2 className="panel-title">
              {activeTab === 'guided' ? (
                <>
                  <Sliders size={20} color="#3b82f6" />
                  Structured Directing Builder
                </>
              ) : (
                <>
                  <Sparkles size={20} color="#a78bfa" />
                  Natural Language Prompt Input
                </>
              )}
            </h2>
          </div>

          {error && (
            <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#f87171', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          {activeTab === 'guided' ? (
            <form onSubmit={handleGuidedSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Subject Description *</label>
                <input
                  type="text"
                  className="form-input"
                  value={guidedInput.subject}
                  onChange={(e) => setGuidedInput({ ...guidedInput, subject: e.target.value })}
                  placeholder="e.g. A futuristic runner in cyber armor"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Action & Visual Trajectory</label>
                <input
                  type="text"
                  className="form-input"
                  value={guidedInput.action}
                  onChange={(e) => setGuidedInput({ ...guidedInput, action: e.target.value })}
                  placeholder="e.g. Sprinting across puddles, jumping over obstacles"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Camera Framing & Movement</label>
                  <input
                    type="text"
                    className="form-input"
                    value={guidedInput.camera}
                    onChange={(e) => setGuidedInput({ ...guidedInput, camera: e.target.value })}
                    placeholder="e.g. Low angle 35mm steadycam"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Lighting & Atmosphere</label>
                  <input
                    type="text"
                    className="form-input"
                    value={guidedInput.lighting}
                    onChange={(e) => setGuidedInput({ ...guidedInput, lighting: e.target.value })}
                    placeholder="e.g. Golden hour rim lighting"
                  />
                </div>
              </div>

              {/* Multimodal Media Attachments */}
              <div className="form-group" style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Image size={15} color="#60a5fa" />
                  Multimodal Reference Image / Video Attachments (.png, .jpg, .mp4)
                </label>

                <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                  <input
                    type="text"
                    className="form-input"
                    value={newImageUri}
                    onChange={(e) => setNewImageUri(e.target.value)}
                    placeholder="Reference URI (e.g. gs://bucket/ref.jpg or https://...)"
                    style={{ flex: 2 }}
                  />
                  <input
                    type="text"
                    className="form-input"
                    value={newImageDesc}
                    onChange={(e) => setNewImageDesc(e.target.value)}
                    placeholder="Description / Role"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={addGuidedImage}
                    style={{ background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', padding: '0 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    <Plus size={16} /> Add Image
                  </button>
                </div>

                {guidedInput.reference_images && guidedInput.reference_images.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
                    {guidedInput.reference_images.map((img, idx) => (
                      <div key={idx} style={{ background: 'rgba(59, 130, 246, 0.15)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '6px', padding: '4px 8px', fontSize: '12px', color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Image size={12} />
                        <span>{img.description}: {img.uri}</span>
                        <Trash2
                          size={12}
                          style={{ cursor: 'pointer', color: '#f87171' }}
                          onClick={() => {
                            const updated = guidedInput.reference_images?.filter((_, i) => i !== idx);
                            setGuidedInput({ ...guidedInput, reference_images: updated });
                          }}
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Duration: {guidedInput.duration_sec}s</label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={guidedInput.duration_sec}
                    onChange={(e) => setGuidedInput({ ...guidedInput, duration_sec: parseInt(e.target.value) })}
                    style={{ accentColor: '#3b82f6' }}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Aspect Ratio</label>
                  <select
                    className="form-select"
                    value={guidedInput.aspect_ratio}
                    onChange={(e) => setGuidedInput({ ...guidedInput, aspect_ratio: e.target.value })}
                  >
                    <option value="16:9">16:9 (Widescreen Landscape)</option>
                    <option value="9:16">9:16 (Vertical Mobile / Reel)</option>
                    <option value="1:1">1:1 (Square Feed)</option>
                  </select>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                <Sparkles size={18} />
                {loading ? 'Enhancing with Omni Flash Director...' : 'Enhance Video Prompt'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleFreeformSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Raw Concept or Prompt *</label>
                <textarea
                  className="form-textarea"
                  value={freeformInput.raw_prompt}
                  onChange={(e) => setFreeformInput({ ...freeformInput, raw_prompt: e.target.value })}
                  placeholder="Describe your video idea in plain language..."
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Director Style Guidance (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  value={freeformInput.director_style_preference}
                  onChange={(e) => setFreeformInput({ ...freeformInput, director_style_preference: e.target.value })}
                  placeholder="e.g. Cinematic IMAX, high contrast, slow motion"
                />
              </div>

              {/* Multimodal Attachments for Freeform */}
              <div className="form-group" style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '12px', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Film size={15} color="#a78bfa" />
                  Multimodal Concept Art & Motion Attachments (.png, .jpg, .mp4)
                </label>

                <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                  <input
                    type="text"
                    className="form-input"
                    value={newImageUri}
                    onChange={(e) => setNewImageUri(e.target.value)}
                    placeholder="Media URI (e.g. gs://bucket/reference.png)"
                    style={{ flex: 2 }}
                  />
                  <input
                    type="text"
                    className="form-input"
                    value={newImageDesc}
                    onChange={(e) => setNewImageDesc(e.target.value)}
                    placeholder="Concept Label"
                    style={{ flex: 1 }}
                  />
                  <button
                    type="button"
                    onClick={addFreeformImage}
                    style={{ background: '#a78bfa', color: '#fff', border: 'none', borderRadius: '6px', padding: '0 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    <Plus size={16} /> Attach Media
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                <Sparkles size={18} />
                {loading ? 'Directing Concept...' : 'Direct Prompt with Omni Flash'}
              </button>
            </form>
          )}
        </div>

        {/* Right Column: Enhanced Output & Specs */}
        <div className="card-panel">
          <div className="panel-header">
            <h2 className="panel-title">
              <Video size={20} color="#10b981" />
              Gemini Omni Flash Video Directing Output
            </h2>
            {result && (
              <button
                onClick={() => copyToClipboard(result.result.enhanced_prompt)}
                style={{ background: 'transparent', border: '1px solid var(--panel-border)', color: 'var(--text-muted)', borderRadius: '6px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}
              >
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy Prompt'}
              </button>
            )}
          </div>

          {loading || streamingText ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label className="form-label" style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={14} color="#60a5fa" />
                  Streaming Omni Flash Directing Taxonomy...
                </label>
                <div className="taxonomy-block">
                  {streamingText}
                  <span className="streaming-cursor">▌</span>
                </div>
              </div>
              {result && (
                <div>
                  <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>
                    Gemini Enterprise Agent Platform Payload Spec
                  </label>
                  <div className="json-box">
                    <pre>{JSON.stringify(result.result.video_config, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          ) : result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>
                  Expanded Omni Flash Directing Prompt Taxonomy
                </label>
                <div className="taxonomy-block">
                  {result.result.enhanced_prompt}
                </div>
              </div>

              <div>
                <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>
                  Gemini Enterprise Agent Platform Payload Spec
                </label>
                <div className="json-box">
                  <pre>{JSON.stringify(result.result.video_config, null, 2)}</pre>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', background: 'rgba(59, 130, 246, 0.08)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '13px', color: '#93c5fd' }}>
                <CheckCircle2 size={18} color="#60a5fa" />
                <span>Payload ready for Gemini Omni Flash Preview Generation Endpoint.</span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <Play size={40} color="#4b5563" />
              <p style={{ fontSize: '15px', color: 'var(--text-muted)' }}>
                Fill out the directing parameters or input a concept to generate a directed Omni Flash prompt.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

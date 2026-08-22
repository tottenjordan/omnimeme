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
  Trash2,
  Zap,
  X,
  UserCheck,
  UserPlus
} from 'lucide-react';
import {
  checkHealth,
  GuidedInput,
  FreeformInput,
  DirectingResponse,
  MediaAttachment,
  CharacterRole,
  fetchVaultCharacters,
  createVaultCharacter,
  deleteVaultCharacter,
  generateTurnaroundSheet,
  getThumbnailUrl
} from './api/client';

const SAMPLE_CHARACTERS: CharacterRole[] = [
  {
    role_id: 'cyber_samurai_kaito',
    name: 'Kaito - Cyber Samurai',
    description: 'Neon-lit street samurai with blue plasma katana, cybernetic eye optic, and high-collar trenchcoat.',
    turnaround_sheet_url: 'gs://omnimeme-vault/turnarounds/kaito_4panel.png',
    aesthetic_tags: ['Cyberpunk', 'Neon Noir', 'Futuristic'],
    voice_style: 'Low gravelly synth bass',
    wardrobe: 'Black reinforced armor with glowing neon blue lines',
    image_role: 'Primary Protagonist',
    image_tag: '@Image1: Character Reference'
  },
  {
    role_id: 'mecha_pilot_aria',
    name: 'Aria - Mecha Pilot',
    description: 'Ace starfighter pilot in a sleek white and crimson flight suit with tactical visor.',
    turnaround_sheet_url: 'gs://omnimeme-vault/turnarounds/aria_4panel.png',
    aesthetic_tags: ['Sci-Fi', 'Anime Cinematic', 'Mecha'],
    voice_style: 'Confident, clear, tactical',
    wardrobe: 'White composite flight suit with brass accents',
    image_role: 'Hero Character',
    image_tag: '@Image1: Character Reference'
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'guided' | 'freeform'>('guided');
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DirectingResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Character Vault State
  const [characters, setCharacters] = useState<CharacterRole[]>(SAMPLE_CHARACTERS);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [generatingTurnaroundId, setGeneratingTurnaroundId] = useState<string | null>(null);
  const [newChar, setNewChar] = useState<{
    role_id: string;
    name: string;
    description: string;
    aesthetic_tags: string;
    voice_style: string;
    wardrobe: string;
    image_role: string;
    turnaround_sheet_url: string;
  }>({
    role_id: '',
    name: '',
    description: '',
    aesthetic_tags: 'Cyberpunk, Cinematic',
    voice_style: 'Low bass, calm',
    wardrobe: 'Default outfit',
    image_role: 'Main Subject',
    turnaround_sheet_url: ''
  });


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
  const [streamingText, setStreamingText] = useState<string>('');

  useEffect(() => {
    checkHealth()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false));

    fetchVaultCharacters()
      .then((data) => {
        if (data && data.length > 0) {
          setCharacters(data);
        }
      })
      .catch(() => {
        // Fallback to sample characters if offline or endpoint unpopulated
      });
  }, []);

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

  const handleCreateVaultCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChar.name.trim() || !newChar.role_id.trim()) {
      setError('Character Name and Role ID are required.');
      return;
    }
    const tagsArray = newChar.aesthetic_tags.split(',').map((t) => t.trim()).filter(Boolean);
    const created: CharacterRole = {
      role_id: newChar.role_id.trim(),
      name: newChar.name.trim(),
      description: newChar.description.trim(),
      aesthetic_tags: tagsArray,
      voice_style: newChar.voice_style.trim(),
      wardrobe: newChar.wardrobe.trim(),
      image_role: newChar.image_role.trim(),
      turnaround_sheet_url: newChar.turnaround_sheet_url.trim() || undefined,
      image_tag: '@Image1: Character Reference'
    };

    try {
      await createVaultCharacter(created);
    } catch {
      // Local fallback
    }

    setCharacters((prev) => [...prev.filter((c) => c.role_id !== created.role_id), created]);
    setIsAddModalOpen(false);
    setNewChar({
      role_id: '',
      name: '',
      description: '',
      aesthetic_tags: 'Cyberpunk, Cinematic',
      voice_style: 'Low bass, calm',
      wardrobe: 'Default outfit',
      image_role: 'Main Subject',
      turnaround_sheet_url: ''
    });

  };

  const handleDeleteCharacter = async (roleId: string) => {
    try {
      await deleteVaultCharacter(roleId);
    } catch {
      // Local fallback
    }
    setCharacters((prev) => prev.filter((c) => c.role_id !== roleId));
    if (guidedInput.character_role_id === roleId) {
      setGuidedInput((prev) => ({ ...prev, character_role_id: undefined }));
    }
    if (freeformInput.character_role_id === roleId) {
      setFreeformInput((prev) => ({ ...prev, character_role_id: undefined }));
    }
  };

  const handleGenerateTurnaround = async (char: CharacterRole) => {
    const refUrl = window.prompt(
      `Optional Reference Image GCS URI for ${char.name} (leave blank to generate without reference image):`,
      ''
    );
    if (refUrl === null) return; // User cancelled prompt

    const referenceImageUrl = refUrl.trim() || undefined;
    setGeneratingTurnaroundId(char.role_id);
    setError(null);
    try {
      const resp = await generateTurnaroundSheet(char.role_id, referenceImageUrl);
      const sheetUrl = resp.turnaround_sheet_url || referenceImageUrl || `gs://omnimeme-vault/turnarounds/${char.role_id}_4panel.png`;
      setCharacters((prev) =>
        prev.map((c) =>
          c.role_id === char.role_id
            ? { ...c, turnaround_sheet_url: sheetUrl, image_tag: '@Image1: Character Reference' }
            : c
        )
      );
      setResult({
        interface: 'vault_turnaround',
        status: 'success',
        result: {
          agent_name: 'Character Vault Turnaround Generator',
          model: 'imagen-3-turnaround',
          enhanced_prompt: `@Image1: Character Reference\n4-Panel Turnaround Sheet Payload for Character [${char.name} (${char.role_id})]:\n- Front View: Full body neutral standing pose\n- Side Profile: 90 degree lateral perspective\n- 3/4 View: Dynamic hero angle\n- Back View: Wardrobe and rear detail view\nAesthetic: ${(char.aesthetic_tags || []).join(', ')}\nWardrobe Specs: ${char.wardrobe || 'Standard tactical'}${referenceImageUrl ? `\nReference Image Source: ${referenceImageUrl}` : ''}`,
          video_config: {
            model: 'gemini-omni-flash',
            prompt: `@Image1: Character Reference (4-panel turnaround grid)`,
            parameters: { duration_seconds: 5, aspect_ratio: '16:9', fps: 30 },
            reference_assets: [
              {
                uri: sheetUrl,
                mime_type: 'image/png',
                description: '@Image1: Character Reference (Turnaround Sheet)'
              }
            ]
          }
        }
      });
    } catch (err: any) {
      // Local fallback simulation if server API returns offline
      const sheetUrl = referenceImageUrl || char.turnaround_sheet_url || `gs://omnimeme-vault/turnarounds/${char.role_id}_4panel.png`;
      setCharacters((prev) =>
        prev.map((c) =>
          c.role_id === char.role_id
            ? { ...c, turnaround_sheet_url: sheetUrl, image_tag: '@Image1: Character Reference' }
            : c
        )
      );
      setResult({
        interface: 'vault_turnaround',
        status: 'success',
        result: {
          agent_name: 'Character Vault Turnaround Generator',
          model: 'imagen-3-turnaround',
          enhanced_prompt: `@Image1: Character Reference\n4-Panel Turnaround Sheet Payload for Character [${char.name} (${char.role_id})]:\n- Front View: Full body neutral standing pose\n- Side Profile: 90 degree lateral perspective\n- 3/4 View: Dynamic hero angle\n- Back View: Wardrobe and rear detail view\nAesthetic: ${(char.aesthetic_tags || []).join(', ')}\nWardrobe Specs: ${char.wardrobe || 'Standard tactical'}${referenceImageUrl ? `\nReference Image Source: ${referenceImageUrl}` : ''}`,
          video_config: {
            model: 'gemini-omni-flash',
            prompt: `@Image1: Character Reference (4-panel turnaround grid)`,
            parameters: { duration_seconds: 5, aspect_ratio: '16:9', fps: 30 },
            reference_assets: [
              {
                uri: sheetUrl,
                mime_type: 'image/png',
                description: '@Image1: Character Reference (Turnaround Sheet)'
              }
            ]
          }
        }
      });
    } finally {
      setGeneratingTurnaroundId(null);
    }
  };

  const handleSelectGuidedCharacter = (roleId: string) => {
    if (!roleId) {
      setGuidedInput((prev) => ({ ...prev, character_role_id: undefined }));
      return;
    }
    const char = characters.find((c) => c.role_id === roleId);
    if (!char) return;

    const refAttachment: MediaAttachment = {
      uri: char.turnaround_sheet_url || `gs://omnimeme-vault/characters/${char.role_id}.png`,
      mime_type: 'image/png',
      description: '@Image1: Character Reference'
    };

    const existingRefs = guidedInput.reference_images || [];
    const hasImage1 = existingRefs.some((r) => r.description?.includes('@Image1'));
    const updatedRefs = hasImage1
      ? existingRefs.map((r) => (r.description?.includes('@Image1') ? refAttachment : r))
      : [refAttachment, ...existingRefs];

    let newSubject = guidedInput.subject;
    if (!newSubject.includes('@Image1')) {
      newSubject = `${char.name} (@Image1: Character Reference), ${char.description}`;
    }

    setGuidedInput({
      ...guidedInput,
      character_role_id: roleId,
      subject: newSubject,
      reference_images: updatedRefs
    });
  };

  const handleSelectFreeformCharacter = (roleId: string) => {
    if (!roleId) {
      setFreeformInput((prev) => ({ ...prev, character_role_id: undefined }));
      return;
    }
    const char = characters.find((c) => c.role_id === roleId);
    if (!char) return;

    const refAttachment: MediaAttachment = {
      uri: char.turnaround_sheet_url || `gs://omnimeme-vault/characters/${char.role_id}.png`,
      mime_type: 'image/png',
      description: '@Image1: Character Reference'
    };

    const existingRefs = freeformInput.reference_images || [];
    const hasImage1 = existingRefs.some((r) => r.description?.includes('@Image1'));
    const updatedRefs = hasImage1
      ? existingRefs.map((r) => (r.description?.includes('@Image1') ? refAttachment : r))
      : [refAttachment, ...existingRefs];

    let newPrompt = freeformInput.raw_prompt;
    if (!newPrompt.includes('@Image1')) {
      newPrompt = `@Image1: Character Reference for ${char.name}. ${newPrompt}`;
    }

    setFreeformInput({
      ...freeformInput,
      character_role_id: roleId,
      raw_prompt: newPrompt,
      reference_images: updatedRefs
    });
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

      {/* 🖼️ Project Character Vault Studio Toolbar Section */}
      <section className="vault-section">
        <div className="vault-header">
          <h2 className="vault-title">
            <UserCheck size={22} color="#60a5fa" />
            🖼️ Project Character Vault Studio Toolbar
          </h2>
          <button
            type="button"
            className="btn-primary"
            onClick={() => setIsAddModalOpen(true)}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <UserPlus size={16} /> Add Character
          </button>
        </div>

        <div className="character-grid">
          {characters.map((char) => (
            <div key={char.role_id} className="character-card">
              {char.turnaround_sheet_url && (
                <img
                  src={getThumbnailUrl(char.turnaround_sheet_url)}
                  alt={char.name}
                  style={{ width: '100%', height: '140px', objectFit: 'cover', borderRadius: '6px 6px 0 0' }}
                />
              )}
              <div>
                <div className="character-card-header">
                  <h3 className="character-name">{char.name}</h3>
                  <span className="role-id-badge">{char.role_id}</span>
                </div>
                <p className="character-desc">{char.description}</p>
                <div className="character-tags" style={{ marginTop: '8px' }}>
                  {(char.aesthetic_tags || []).map((tag, idx) => (
                    <span key={idx} className="tag-pill">
                      {tag}
                    </span>
                  ))}
                </div>
                {char.turnaround_sheet_url && (
                  <div style={{ marginTop: '8px' }}>
                    <span className="turnaround-tag-badge">
                      <Check size={12} /> @Image1: Character Reference
                    </span>
                  </div>
                )}
              </div>

              <div className="card-actions">
                <button
                  type="button"
                  className="btn-turnaround"
                  disabled={generatingTurnaroundId === char.role_id}
                  onClick={() => handleGenerateTurnaround(char)}
                >
                  <Zap size={14} />
                  {generatingTurnaroundId === char.role_id ? 'Generating...' : '⚡ 1-Click Turnaround Sheet'}
                </button>
                <button
                  type="button"
                  className="btn-icon-danger"
                  title="Delete character"
                  onClick={() => handleDeleteCharacter(char.role_id)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

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
              {/* Quick-Select Saved Character Dropdown */}
              <div className="form-group" style={{ background: 'rgba(59, 130, 246, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
                <label className="form-label" style={{ color: '#93c5fd', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={14} color="#60a5fa" />
                  Quick-Select Saved Character (Character Vault)
                </label>
                <select
                  className="form-select"
                  value={guidedInput.character_role_id || ''}
                  onChange={(e) => handleSelectGuidedCharacter(e.target.value)}
                >
                  <option value="">-- Select Saved Vault Character --</option>
                  {characters.map((c) => (
                    <option key={c.role_id} value={c.role_id}>
                      {c.name} ({c.role_id})
                    </option>
                  ))}
                </select>
              </div>

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
              {/* Quick-Select Saved Character Dropdown */}
              <div className="form-group" style={{ background: 'rgba(167, 139, 250, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(167, 139, 250, 0.2)' }}>
                <label className="form-label" style={{ color: '#c084fc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={14} color="#a78bfa" />
                  Quick-Select Saved Character (Character Vault)
                </label>
                <select
                  className="form-select"
                  value={freeformInput.character_role_id || ''}
                  onChange={(e) => handleSelectFreeformCharacter(e.target.value)}
                >
                  <option value="">-- Select Saved Vault Character --</option>
                  {characters.map((c) => (
                    <option key={c.role_id} value={c.role_id}>
                      {c.name} ({c.role_id})
                    </option>
                  ))}
                </select>
              </div>

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
              {result.result.video_config?.reference_assets?.[0]?.uri && (
                <div>
                  <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>
                    Hot-Loaded Turnaround / Reference Thumbnail Preview
                  </label>
                  <img
                    src={getThumbnailUrl(result.result.video_config.reference_assets[0].uri)}
                    alt="Turnaround Thumbnail Preview"
                    style={{ width: '100%', maxHeight: '200px', objectFit: 'contain', borderRadius: '8px', border: '1px solid var(--panel-border)', background: '#0f1117' }}
                  />
                </div>
              )}
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

      {/* Add Character Modal */}
      {isAddModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">
                <UserPlus size={20} color="#60a5fa" />
                Add New Vault Character
              </h3>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateVaultCharacter} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Role ID (Unique Identifier) *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. cyber_samurai_kaito"
                  value={newChar.role_id}
                  onChange={(e) => setNewChar({ ...newChar, role_id: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Character Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Kaito - Cyber Samurai"
                  value={newChar.name}
                  onChange={(e) => setNewChar({ ...newChar, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Character Description</label>
                <textarea
                  className="form-textarea"
                  style={{ minHeight: '70px' }}
                  placeholder="Detailed character visual traits, personality, and background..."
                  value={newChar.description}
                  onChange={(e) => setNewChar({ ...newChar, description: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Aesthetic Tags (Comma separated)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Cyberpunk, Neon Noir, Futuristic"
                  value={newChar.aesthetic_tags}
                  onChange={(e) => setNewChar({ ...newChar, aesthetic_tags: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Reference Image / Turnaround Sheet GCS URI (Optional)</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. gs://omnimeme-vault/turnarounds/character_sheet.png"
                  value={newChar.turnaround_sheet_url}
                  onChange={(e) => setNewChar({ ...newChar, turnaround_sheet_url: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Wardrobe Specs</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Black trenchcoat with blue trim"
                    value={newChar.wardrobe}
                    onChange={(e) => setNewChar({ ...newChar, wardrobe: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Voice / Audio Style</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Low synth bass voice"
                    value={newChar.voice_style}
                    onChange={(e) => setNewChar({ ...newChar, voice_style: e.target.value })}
                  />
                </div>
              </div>


              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  style={{ background: 'transparent', border: '1px solid var(--panel-border)', color: 'var(--text-main)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" style={{ padding: '8px 20px' }}>
                  Save Character
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

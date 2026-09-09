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
  UserPlus,
  Link2
} from 'lucide-react';
import {
  checkHealth,
  GuidedInput,
  FreeformInput,
  DirectingResponse,
  GenerationResult,
  executeVideoGeneration,
  renderChainedStoryboard,
  MediaAttachment,
  CharacterRole,
  fetchVaultCharacters,
  createVaultCharacter,
  deleteVaultCharacter,
  generateTurnaroundSheet,
  getThumbnailUrl,
  submitUserFeedback,
  generateStoryboard,
  StoryboardResponse,
  StoryboardScene,
  streamGuided,
  streamFreeform,
  fetchArchetypePresets,
  concatenateMasterFilm,
  CharacterArchetypePreset,
  fetchMashupBundles,
  generateMashupStoryboard,
  MashupBundle,
  ProductInfo
} from './api/client';



export interface ScreeningTurn {
  id: string;
  prompt: string;
  video_url: string;
  interaction_thread_id: string;
  generation_mode: string;
  rating?: number;
  user_comment?: string;
  timestamp: string;
}

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

const DEFAULT_ARCHETYPE_PRESETS: CharacterArchetypePreset[] = [
  {
    role_id: 'cyberpunk_ronin',
    name: 'Cyberpunk Ronin',
    description: 'Lone cybernetic samurai with glowing plasma katana in neon rain.',
    aesthetic_tags: ['Cyberpunk', 'Neon Noir', 'Futuristic'],
    voice_style: 'Low gravelly synth bass',
    wardrobe: 'Dark high-collar trenchcoat over carbon-fiber body armor',
    image_role: 'Primary Protagonist',
  },
  {
    role_id: 'scifi_captain',
    name: 'Sci-Fi Captain',
    description: 'Commanding starship captain with tactical visor and dress uniform.',
    aesthetic_tags: ['Sci-Fi', 'Space Opera', 'Commanding'],
    voice_style: 'Authoritative, calm, clear',
    wardrobe: 'Deep navy naval tunic with gold rank pins and shoulder pauldrons',
    image_role: 'Fleet Commander',
  },
  {
    role_id: 'anime_mech_pilot',
    name: 'Anime Mech Pilot',
    description: 'Ace starfighter pilot in sleek combat suit.',
    aesthetic_tags: ['Anime', 'Mecha', 'Cinematic'],
    voice_style: 'Enthusiastic, sharp, intense',
    wardrobe: 'White and crimson plugsuit with holographic HUD elements',
    image_role: 'Hero Pilot',
  },
  {
    role_id: 'fantasy_sorcerer',
    name: 'Fantasy Sorcerer',
    description: 'Mystical arch-mage channeling glowing arcane runes.',
    aesthetic_tags: ['Fantasy', 'Arcane', 'High Magic'],
    voice_style: 'Resonant, echoing, ancient',
    wardrobe: 'Midnight blue embroidered velvet robes with crystal staff',
    image_role: 'Arcane Spellcaster',
  },
  {
    role_id: 'film_noir_detective',
    name: 'Film Noir Detective',
    description: 'Hard-boiled investigator in rain-slicked city streets.',
    aesthetic_tags: ['Noir', 'Monochrome', 'Vintage'],
    voice_style: 'Smooth voiceover monologue, raspy',
    wardrobe: 'Classic brown fedora, classic trench coat, smoking cigarette',
    image_role: 'Lead Investigator',
  },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'guided' | 'freeform' | 'scriptwriter' | 'mashup' | 'screening'>('guided');
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DirectingResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [videoResult, setVideoResult] = useState<GenerationResult | null>(null);
  const [isRenderingVideo, setIsRenderingVideo] = useState(false);

  // Scriptwriter Agent & Concatenation Engine State
  const [scriptwriterConcept, setScriptwriterConcept] = useState<string>(
    'A cyberpunk detective uncovering a mysterious neon secret in the rain-slicked metropolis'
  );
  const [scriptwriterSceneCount, setScriptwriterSceneCount] = useState<number>(3);
  const [scriptwriterStyle, setScriptwriterStyle] = useState<string>('Neon noir cinematic 4k, moody blue and amber lighting');
  const [scriptwriterCharId, setScriptwriterCharId] = useState<string>('');
  const [storyboard, setStoryboard] = useState<StoryboardResponse | null>(null);
  const [isGeneratingStoryboard, setIsGeneratingStoryboard] = useState<boolean>(false);
  const [isRenderingFederated, setIsRenderingFederated] = useState<boolean>(false);
  const [isRenderingChained, setIsRenderingChained] = useState<boolean>(false);
  const [renderedScenes, setRenderedScenes] = useState<Record<number, GenerationResult>>({});
  const [isConcatenating, setIsConcatenating] = useState<boolean>(false);
  const [masterFilmUrl, setMasterFilmUrl] = useState<string | null>(null);
  const [archetypePresets, setArchetypePresets] = useState<CharacterArchetypePreset[]>(DEFAULT_ARCHETYPE_PRESETS);

  // Parody & Mashup Studio State
  const [mashupCharA, setMashupCharA] = useState<string>('space_lord');
  const [mashupCharB, setMashupCharB] = useState<string>('chef_supreme');
  const [mashupGenre, setMashupGenre] = useState<string>('Sci-Fi Reality Cooking Show');
  const [parodyTone, setParodyTone] = useState<string>('Absurdist Satire');
  const [productName, setProductName] = useState<string>('Lightsaber Blender 9000');
  const [productDesc, setProductDesc] = useState<string>('Plasma-powered countertop blender that purees ingredients at lightspeed.');
  const [productImgUrl, setProductImgUrl] = useState<string>('gs://omnimeme-assets/products/lightsaber_blender.png');
  const [productTagline, setProductTagline] = useState<string>('Puree with the Force!');
  const [showProductAccordion, setShowProductAccordion] = useState<boolean>(true);
  const [mashupBundles, setMashupBundles] = useState<MashupBundle[]>([]);
  const [mashupStoryboard, setMashupStoryboard] = useState<StoryboardResponse | null>(null);
  const [isGeneratingMashup, setIsGeneratingMashup] = useState<boolean>(false);
  const [isRenderingMashup, setIsRenderingMashup] = useState<boolean>(false);
  const [isRenderingMashupChained, setIsRenderingMashupChained] = useState<boolean>(false);
  const [mashupRenderedScenes, setMashupRenderedScenes] = useState<Record<number, GenerationResult>>({});
  const [isConcatenatingMashup, setIsConcatenatingMashup] = useState<boolean>(false);
  const [mashupMasterFilmUrl, setMashupMasterFilmUrl] = useState<string | null>(null);

  const handleApplyMashupBundle = (bundle: MashupBundle) => {
    if (bundle.character_a?.role_id) setMashupCharA(bundle.character_a.role_id);
    if (bundle.character_b?.role_id) setMashupCharB(bundle.character_b.role_id);
    if (bundle.mashup_genre) setMashupGenre(bundle.mashup_genre);
    if (bundle.parody_tone) setParodyTone(bundle.parody_tone);
    if (bundle.product) {
      setProductName(bundle.product.name || '');
      setProductDesc(bundle.product.description || '');
      setProductImgUrl(bundle.product.image_url || '');
      setProductTagline(bundle.product.tagline || '');
      setShowProductAccordion(true);
    }
  };

  const handleMashupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mashupCharA || !mashupCharB) {
      setError('Please select both Character A and Character B.');
      return;
    }
    setIsGeneratingMashup(true);
    setError(null);
    setMashupRenderedScenes({});
    setMashupMasterFilmUrl(null);
    try {
      const res = await generateMashupStoryboard({
        character_a_id: mashupCharA,
        character_b_id: mashupCharB,
        mashup_genre: mashupGenre.trim(),
        parody_tone: parodyTone.trim(),
        product: productName.trim()
          ? {
              name: productName.trim(),
              description: productDesc.trim(),
              image_url: productImgUrl.trim(),
              tagline: productTagline.trim(),
            }
          : undefined,
        scene_count: 4,
      });
      setMashupStoryboard(res);
    } catch (err: any) {
      setError(err.message || 'Mashup storyboard generation failed');
    } finally {
      setIsGeneratingMashup(false);
    }
  };

  const handleRenderAllMashupScenes = async () => {
    if (!mashupStoryboard?.storyboard?.scenes?.length) return;
    setIsRenderingMashup(true);
    setError(null);
    for (const scene of mashupStoryboard.storyboard.scenes) {
      try {
        const res = await executeVideoGeneration(scene.video_config);
        setMashupRenderedScenes((prev) => ({ ...prev, [scene.scene_number]: res }));
      } catch (err: any) {
        console.error(`Error rendering mashup scene ${scene.scene_number}:`, err);
      }
    }
    setIsRenderingMashup(false);
  };

  const handleRenderChainedMashupScenes = async () => {
    if (!mashupStoryboard?.storyboard?.scenes?.length) return;
    setIsRenderingMashupChained(true);
    setError(null);
    try {
      const res = await renderChainedStoryboard(mashupStoryboard.storyboard.scenes);
      const updatedMap: Record<number, GenerationResult> = {};
      res.scenes.forEach((sc) => {
        updatedMap[sc.scene_number] = {
          interaction_thread_id: sc.interaction_id || `turn_${sc.scene_number}`,
          video_url: sc.video_url || '',
          duration_seconds: sc.duration_seconds || 5,
          synth_id_watermark: 'SYNTHID_C2PA_VERIFIED',
          status: sc.status || 'completed',
          generation_mode: sc.generation_mode || 'LIVE_GEMINI_OMNI_1_1_FLASH',
        };
      });
      setMashupRenderedScenes((prev) => ({ ...prev, ...updatedMap }));
    } catch (err: any) {
      setError(err.message || 'Chained mashup rendering failed');
    } finally {
      setIsRenderingMashupChained(false);
    }
  };

  const handleRenderSingleMashupScene = async (sceneNumber: number, config: VideoConfig) => {
    setError(null);
    try {
      const res = await executeVideoGeneration(config);
      setMashupRenderedScenes((prev) => ({ ...prev, [sceneNumber]: res }));
    } catch (err: any) {
      setError(err.message || `Failed to render scene ${sceneNumber}`);
    }
  };

  const handleConcatenateMashupMasterFilm = async () => {
    if (!mashupStoryboard?.storyboard?.scenes?.length) return;
    setIsConcatenatingMashup(true);
    setError(null);
    try {
      const urls = mashupStoryboard.storyboard.scenes.map(
        (scene) => mashupRenderedScenes[scene.scene_number]?.video_url || `/static/rendered/scene_${scene.scene_number}.mp4`
      );
      const lowerThirds = mashupStoryboard.storyboard.scenes.map(
        (scene) => scene.lower_third_title || { name: `Scene ${scene.scene_number}` }
      );
      const sponsorCallout = productName.trim()
        ? `${productName.trim()}${productTagline.trim() ? ` - ${productTagline.trim()}` : ''}`
        : undefined;

      const res = await concatenateMasterFilm(urls, 'mashup_parody_master', lowerThirds, sponsorCallout);
      setMashupMasterFilmUrl(res.master_video_url);
    } catch (err: any) {
      setError(err.message || 'Mashup master film export failed');
    } finally {
      setIsConcatenatingMashup(false);
    }
  };


  const handleConcatenateMasterFilm = async () => {
    if (!storyboard?.storyboard?.scenes?.length) return;
    setIsConcatenating(true);
    setError(null);
    try {
      const urls = storyboard.storyboard.scenes.map(
        (scene) => renderedScenes[scene.scene_number]?.video_url || `/static/rendered/scene_${scene.scene_number}.mp4`
      );
      const res = await concatenateMasterFilm(urls);
      setMasterFilmUrl(res.master_video_url);
    } catch (err: any) {
      setError(err.message || 'Master film concatenation failed');
    } finally {
      setIsConcatenating(false);
    }
  };

  const handleApplyArchetypePreset = (preset: CharacterArchetypePreset) => {
    setNewChar({
      role_id: preset.role_id,
      name: preset.name,
      description: preset.description,
      aesthetic_tags: preset.aesthetic_tags.join(', '),
      voice_style: preset.voice_style,
      wardrobe: preset.wardrobe,
      image_role: preset.image_role,
      turnaround_sheet_url: '',
    });
  };


  const handleScriptwriterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scriptwriterConcept.trim()) {
      setError('Creative concept is required.');
      return;
    }
    setIsGeneratingStoryboard(true);
    setError(null);
    setRenderedScenes({});
    try {
      const res = await generateStoryboard({
        concept: scriptwriterConcept.trim(),
        scene_count: scriptwriterSceneCount,
        style_preference: scriptwriterStyle.trim(),
        character_role_id: scriptwriterCharId || undefined,
      });
      setStoryboard(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate multi-scene storyboard');
    } finally {
      setIsGeneratingStoryboard(false);
    }
  };

  const handleRenderAllFederated = async () => {
    if (!storyboard?.storyboard?.scenes?.length) return;
    setIsRenderingFederated(true);
    setError(null);
    try {
      for (const scene of storyboard.storyboard.scenes) {
        const res = await executeVideoGeneration(scene.video_config);
        setRenderedScenes((prev) => ({ ...prev, [scene.scene_number]: res }));
      }
    } catch (err: any) {
      setError(err.message || 'Federated scene rendering failed');
    } finally {
      setIsRenderingFederated(false);
    }
  };

  const handleRenderChainedStoryboard = async () => {
    if (!storyboard?.storyboard?.scenes?.length) return;
    setIsRenderingChained(true);
    setError(null);
    try {
      const res = await renderChainedStoryboard(storyboard.storyboard.scenes);
      const updatedMap: Record<number, GenerationResult> = {};
      res.scenes.forEach((sc) => {
        updatedMap[sc.scene_number] = {
          interaction_thread_id: sc.interaction_id || `turn_${sc.scene_number}`,
          video_url: sc.video_url || '',
          duration_seconds: sc.duration_seconds || 5,
          synth_id_watermark: 'SYNTHID_C2PA_VERIFIED',
          status: sc.status || 'completed',
          generation_mode: sc.generation_mode || 'LIVE_GEMINI_OMNI_1_1_FLASH',
        };
      });
      setRenderedScenes((prev) => ({ ...prev, ...updatedMap }));
    } catch (err: any) {
      setError(err.message || 'Chained storyboard rendering failed');
    } finally {
      setIsRenderingChained(false);
    }
  };


  // Screening Room Conversational State
  const [screeningHistory, setScreeningHistory] = useState<ScreeningTurn[]>([]);
  const [editPrompt, setEditPrompt] = useState<string>('');
  const [submittingRatingId, setSubmittingRatingId] = useState<string | null>(null);
  const [feedbackComment, setFeedbackComment] = useState<string>('');

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
    resolution: '720p',
    first_frame_uri: '',
    last_frame_uri: '',
    reference_images: [],
    reference_videos: [],
    motion_preset: ''
  });

  // Free-form State
  const [freeformInput, setFreeformInput] = useState<FreeformInput>({
    raw_prompt: 'A golden retriever wearing aviator sunglasses riding a skateboard down a sunlit hill',
    director_style_preference: 'Upbeat commercial 4K high speed video',
    resolution: '720p',
    first_frame_uri: '',
    last_frame_uri: '',
    reference_images: [],
    reference_videos: [],
    motion_preset: ''
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

    fetchArchetypePresets()
      .then((data) => {
        if (data && data.length > 0) {
          setArchetypePresets(data);
        }
      })
      .catch(() => {});

    fetchMashupBundles()
      .then((data) => {
        if (data && data.length > 0) {
          setMashupBundles(data);
        }
      })
      .catch(() => {});
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
            model: 'gemini-omni-1.1-flash-preview',
            prompt: `@Image1: Character Reference (4-panel turnaround grid)`,
            parameters: { duration_seconds: 5, aspect_ratio: '16:9', fps: 30, resolution: '720p' },
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
            model: 'gemini-omni-1.1-flash-preview',
            prompt: `@Image1: Character Reference (4-panel turnaround grid)`,
            parameters: { duration_seconds: 5, aspect_ratio: '16:9', fps: 30, resolution: '720p' },
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
    setVideoResult(null);

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
    setVideoResult(null);

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
  };

  const handleExecuteVideo = async () => {
    if (!result?.result?.video_config) return;
    setIsRenderingVideo(true);
    setError(null);
    try {
      const res = await executeVideoGeneration(result.result.video_config);
      setVideoResult(res);
      const newTurn: ScreeningTurn = {
        id: `turn_${Date.now()}`,
        prompt: result.result.enhanced_prompt || result.result.video_config.prompt,
        video_url: res.video_url,
        interaction_thread_id: res.interaction_thread_id,
        generation_mode: res.generation_mode,
        timestamp: new Date().toLocaleTimeString(),
      };
      setScreeningHistory((prev) => [newTurn, ...prev]);
    } catch (err: any) {
      setError(err.message || 'Video generation execution failed');
    } finally {
      setIsRenderingVideo(false);
    }
  };

  const handleConversationalEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editPrompt.trim()) return;
    if (!screeningHistory.length) {
      setError('Please generate an initial video before applying conversational edits.');
      return;
    }
    const lastTurn = screeningHistory[0];
    setIsRenderingVideo(true);
    setError(null);

    const editConfig: VideoConfig = {
      model: 'gemini-omni-1.1-flash-preview',
      prompt: editPrompt.trim(),
      parameters: { duration_seconds: 5, aspect_ratio: '16:9', fps: 30, resolution: guidedInput.resolution || '720p' },
    };

    try {
      const res = await executeVideoGeneration(editConfig, lastTurn.interaction_thread_id);
      const newTurn: ScreeningTurn = {
        id: `turn_${Date.now()}`,
        prompt: editPrompt.trim(),
        video_url: res.video_url,
        interaction_thread_id: res.interaction_thread_id,
        generation_mode: res.generation_mode,
        timestamp: new Date().toLocaleTimeString(),
      };
      setScreeningHistory((prev) => [newTurn, ...prev]);
      setVideoResult(res);
      setEditPrompt('');
    } catch (err: any) {
      setError(err.message || 'Conversational video edit failed');
    } finally {
      setIsRenderingVideo(false);
    }
  };

  const handleExtendScene = async () => {
    if (!screeningHistory.length && !videoResult) {
      setError('Please generate an initial video before extending the scene.');
      return;
    }
    const lastTurn = screeningHistory[0];
    const threadId = lastTurn?.interaction_thread_id || videoResult?.interaction_thread_id;
    if (!threadId) return;

    setIsRenderingVideo(true);
    setError(null);

    const extendConfig: VideoConfig = {
      model: 'gemini-omni-1.1-flash-preview',
      prompt: 'Extend scene with continuous action (+10s context window)',
      parameters: {
        duration_seconds: 10,
        aspect_ratio: guidedInput.aspect_ratio || '16:9',
        fps: 30,
        resolution: guidedInput.resolution || '720p',
      },
    };

    try {
      const res = await executeVideoGeneration(extendConfig, threadId);
      const newTurn: ScreeningTurn = {
        id: `turn_${Date.now()}`,
        prompt: '⏩ Extended Scene (+10s)',
        video_url: res.video_url,
        interaction_thread_id: res.interaction_thread_id,
        generation_mode: res.generation_mode,
        timestamp: new Date().toLocaleTimeString(),
      };
      setScreeningHistory((prev) => [newTurn, ...prev]);
      setVideoResult(res);
    } catch (err: any) {
      setError(err.message || 'Scene extension failed');
    } finally {
      setIsRenderingVideo(false);
    }
  };

  const handleRatingSubmit = async (turnId: string, rating: number) => {
    const turn = screeningHistory.find((t) => t.id === turnId);
    if (!turn) return;
    setSubmittingRatingId(turnId);
    try {
      await submitUserFeedback({
        interaction_thread_id: turn.interaction_thread_id,
        rating,
        comment: feedbackComment || undefined,
        prompt: turn.prompt,
      });
      setScreeningHistory((prev) =>
        prev.map((t) => (t.id === turnId ? { ...t, rating, user_comment: feedbackComment } : t))
      );
      setFeedbackComment('');
    } catch (err: any) {
      setError('Failed to submit user feedback');
    } finally {
      setSubmittingRatingId(null);
    }
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
        <button
          className={`tab-button ${activeTab === 'scriptwriter' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('scriptwriter');
            setError(null);
          }}
        >
          <Clapperboard size={16} color="#ec4899" />
          🎭 Multi-Scene Scriptwriter
        </button>
        <button
          className={`tab-button ${activeTab === 'mashup' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('mashup');
            setError(null);
          }}
        >
          <Sparkles size={16} color="#eab308" />
          🎭 Parody & Mashup Studio
        </button>
        <button
          className={`tab-button ${activeTab === 'screening' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('screening');
            setError(null);
          }}
        >
          <Film size={16} color="#10b981" />
          🎬 The Screening Room
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
              ) : activeTab === 'freeform' ? (
                <>
                  <Sparkles size={20} color="#a78bfa" />
                  Natural Language Prompt Input
                </>
              ) : activeTab === 'scriptwriter' ? (
                <>
                  <Clapperboard size={20} color="#ec4899" />
                  Creative Concept & Storyboard Generator
                </>
              ) : activeTab === 'mashup' ? (
                <>
                  <Sparkles size={20} color="#eab308" />
                  Parody & Mashup Studio Builder
                </>
              ) : (
                <>
                  <Film size={20} color="#10b981" />
                  The Screening Room Reel & History
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

              {/* Motion Preset Quick Selector */}
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Zap size={14} color="#60a5fa" />
                  Motion Preset Quick Selector
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {[
                    { id: 'dolly_zoom', label: '🎥 Dolly Zoom' },
                    { id: 'orbital', label: '🔄 360° Orbit' },
                    { id: 'whip_pan', label: '⚡ Whip Pan' },
                    { id: 'seamless_loop', label: '🔁 Loop' },
                  ].map((preset) => {
                    const isSelected = guidedInput.motion_preset === preset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() =>
                          setGuidedInput({
                            ...guidedInput,
                            motion_preset: isSelected ? '' : preset.id,
                          })
                        }
                        style={{
                          padding: '6px 14px',
                          borderRadius: '6px',
                          fontSize: '13px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          border: isSelected ? '1px solid #3b82f6' : '1px solid var(--panel-border)',
                          background: isSelected ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                          color: isSelected ? '#60a5fa' : 'var(--text-main)',
                        }}
                      >
                        {preset.label}
                      </button>
                    );
                  })}
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
                <div className="form-group">
                  <label className="form-label">Resolution</label>
                  <select
                    className="form-select"
                    value={guidedInput.resolution || '720p'}
                    onChange={(e) => setGuidedInput({ ...guidedInput, resolution: e.target.value })}
                  >
                    <option value="360p">⚡ 360p Fast Draft (60% Faster)</option>
                    <option value="720p">720p HD</option>
                    <option value="1080p">1080p Full HD</option>
                    <option value="4k">4K Ultra HD</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Start Frame GCS URI (Keyframe)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={guidedInput.first_frame_uri || ''}
                    onChange={(e) => setGuidedInput({ ...guidedInput, first_frame_uri: e.target.value })}
                    placeholder="gs://bucket/first_frame.png"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Frame GCS URI (Keyframe)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={guidedInput.last_frame_uri || ''}
                    onChange={(e) => setGuidedInput({ ...guidedInput, last_frame_uri: e.target.value })}
                    placeholder="gs://bucket/last_frame.png"
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                <Sparkles size={18} />
                {loading ? 'Enhancing with Omni Flash Director...' : 'Enhance Video Prompt'}
              </button>
            </form>
          ) : activeTab === 'freeform' ? (
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

              {/* Motion Preset Quick Selector */}
              <div className="form-group">
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Zap size={14} color="#a78bfa" />
                  Motion Preset Quick Selector
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {[
                    { id: 'dolly_zoom', label: '🎥 Dolly Zoom' },
                    { id: 'orbital', label: '🔄 360° Orbit' },
                    { id: 'whip_pan', label: '⚡ Whip Pan' },
                    { id: 'seamless_loop', label: '🔁 Loop' },
                  ].map((preset) => {
                    const isSelected = freeformInput.motion_preset === preset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        onClick={() =>
                          setFreeformInput({
                            ...freeformInput,
                            motion_preset: isSelected ? '' : preset.id,
                          })
                        }
                        style={{
                          padding: '6px 14px',
                          borderRadius: '6px',
                          fontSize: '13px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          border: isSelected ? '1px solid #a78bfa' : '1px solid var(--panel-border)',
                          background: isSelected ? 'rgba(167, 139, 250, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                          color: isSelected ? '#c084fc' : 'var(--text-main)',
                        }}
                      >
                        {preset.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Resolution</label>
                  <select
                    className="form-select"
                    value={freeformInput.resolution || '720p'}
                    onChange={(e) => setFreeformInput({ ...freeformInput, resolution: e.target.value })}
                  >
                    <option value="360p">⚡ 360p Fast Draft (60% Faster)</option>
                    <option value="720p">720p HD</option>
                    <option value="1080p">1080p Full HD</option>
                    <option value="4k">4K Ultra HD</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Start Frame GCS URI (Keyframe)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={freeformInput.first_frame_uri || ''}
                    onChange={(e) => setFreeformInput({ ...freeformInput, first_frame_uri: e.target.value })}
                    placeholder="gs://bucket/first_frame.png"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Frame GCS URI (Keyframe)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={freeformInput.last_frame_uri || ''}
                    onChange={(e) => setFreeformInput({ ...freeformInput, last_frame_uri: e.target.value })}
                    placeholder="gs://bucket/last_frame.png"
                  />
                </div>
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
          ) : activeTab === 'scriptwriter' ? (
            <form onSubmit={handleScriptwriterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group" style={{ background: 'rgba(236, 72, 153, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(236, 72, 153, 0.2)' }}>
                <label className="form-label" style={{ color: '#f472b6', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={14} color="#ec4899" />
                  Quick-Select Character Vault Role (Optional)
                </label>
                <select
                  className="form-select"
                  value={scriptwriterCharId}
                  onChange={(e) => setScriptwriterCharId(e.target.value)}
                >
                  <option value="">-- Select Vault Character --</option>
                  {characters.map((c) => (
                    <option key={c.role_id} value={c.role_id}>
                      {c.name} ({c.role_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">High-Level Creative Concept *</label>
                <textarea
                  className="form-textarea"
                  value={scriptwriterConcept}
                  onChange={(e) => setScriptwriterConcept(e.target.value)}
                  placeholder="Describe your multi-scene concept in high-level narrative detail..."
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Desired Scene Count</label>
                <select
                  className="form-select"
                  value={scriptwriterSceneCount}
                  onChange={(e) => setScriptwriterSceneCount(Number(e.target.value))}
                >
                  <option value={2}>2 Scenes</option>
                  <option value={3}>3 Scenes (Default)</option>
                  <option value={4}>4 Scenes</option>
                  <option value={5}>5 Scenes</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Global Director Style Preference</label>
                <input
                  type="text"
                  className="form-input"
                  value={scriptwriterStyle}
                  onChange={(e) => setScriptwriterStyle(e.target.value)}
                  placeholder="e.g. Cyberpunk neon noir, IMAX 4K"
                />
              </div>

              <button type="submit" className="btn-primary" disabled={isGeneratingStoryboard} style={{ background: 'linear-gradient(135deg, #db2777, #ec4899)' }}>
                <Sparkles size={18} />
                {isGeneratingStoryboard ? 'Generating Storyboard...' : '✨ Generate Multi-Scene Storyboard'}
              </button>
            </form>
          ) : activeTab === 'mashup' ? (
            <form onSubmit={handleMashupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* 1-Click Preset Bundles */}
              <div className="form-group" style={{ background: 'rgba(234, 179, 8, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(234, 179, 8, 0.2)' }}>
                <label className="form-label" style={{ color: '#facc15', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Zap size={14} color="#eab308" />
                  1-Click Parody Preset Bundles
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginTop: '6px' }}>
                  {mashupBundles.map((b) => (
                    <button
                      key={b.id}
                      type="button"
                      onClick={() => handleApplyMashupBundle(b)}
                      style={{
                        padding: '10px 12px',
                        borderRadius: '6px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid rgba(234, 179, 8, 0.3)',
                        color: '#fef08a',
                        textAlign: 'left',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{b.title}</span>
                        {b.product && <span style={{ fontSize: '11px', background: 'rgba(234, 179, 8, 0.2)', padding: '1px 6px', borderRadius: '4px' }}>🛒 {b.product.name}</span>}
                      </div>
                      <div style={{ fontSize: '11px', color: '#9ca3af' }}>{b.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Character A Selector */}
              <div className="form-group">
                <label className="form-label">Character A (Protagonist) *</label>
                <select
                  className="form-select"
                  value={mashupCharA}
                  onChange={(e) => setMashupCharA(e.target.value)}
                  required
                >
                  <option value="">-- Select Character A --</option>
                  <option value="space_lord">Space Lord</option>
                  <option value="cyberpunk_ronin">Cyberpunk Ronin</option>
                  <option value="scifi_captain">Sci-Fi Captain</option>
                  <option value="fantasy_sorcerer">Fantasy Sorcerer</option>
                  {characters.map((c) => (
                    <option key={`a_${c.role_id}`} value={c.role_id}>
                      {c.name} ({c.role_id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Character B Selector */}
              <div className="form-group">
                <label className="form-label">Character B (Challenger / Antagonist) *</label>
                <select
                  className="form-select"
                  value={mashupCharB}
                  onChange={(e) => setMashupCharB(e.target.value)}
                  required
                >
                  <option value="">-- Select Character B --</option>
                  <option value="chef_supreme">Chef Supreme</option>
                  <option value="film_noir_detective">Film Noir Detective</option>
                  <option value="anime_mech_pilot">Anime Mech Pilot</option>
                  {characters.map((c) => (
                    <option key={`b_${c.role_id}`} value={c.role_id}>
                      {c.name} ({c.role_id})
                    </option>
                  ))}
                </select>
              </div>

              {/* Mashup Genre */}
              <div className="form-group">
                <label className="form-label">Mashup Genre</label>
                <input
                  type="text"
                  className="form-input"
                  value={mashupGenre}
                  onChange={(e) => setMashupGenre(e.target.value)}
                  placeholder="e.g. Sci-Fi Reality Cooking Show"
                />
              </div>

              {/* Parody Tone */}
              <div className="form-group">
                <label className="form-label">Parody Tone</label>
                <input
                  type="text"
                  className="form-input"
                  value={parodyTone}
                  onChange={(e) => setParodyTone(e.target.value)}
                  placeholder="e.g. Absurdist Satire, Over-The-Top Anime"
                />
              </div>

              {/* Product Reference Accordion */}
              <div style={{ border: '1px solid var(--panel-border)', borderRadius: '8px', overflow: 'hidden' }}>
                <button
                  type="button"
                  onClick={() => setShowProductAccordion(!showProductAccordion)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#131822',
                    border: 'none',
                    color: '#38bdf8',
                    fontWeight: 600,
                    fontSize: '13px',
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                  }}
                >
                  <span>🛒 Product Commercial Parody Reference (Optional)</span>
                  <span>{showProductAccordion ? '▲' : '▼'}</span>
                </button>

                {showProductAccordion && (
                  <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '12px', background: '#0b0d12' }}>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Product Name</label>
                      <input
                        type="text"
                        className="form-input"
                        value={productName}
                        onChange={(e) => setProductName(e.target.value)}
                        placeholder="e.g. Lightsaber Blender 9000"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Product Tagline</label>
                      <input
                        type="text"
                        className="form-input"
                        value={productTagline}
                        onChange={(e) => setProductTagline(e.target.value)}
                        placeholder="e.g. Puree with the Force!"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Product Description</label>
                      <input
                        type="text"
                        className="form-input"
                        value={productDesc}
                        onChange={(e) => setProductDesc(e.target.value)}
                        placeholder="e.g. Plasma-powered countertop blender"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" style={{ fontSize: '12px' }}>Product Image URL / GCS URI</label>
                      <input
                        type="text"
                        className="form-input"
                        value={productImgUrl}
                        onChange={(e) => setProductImgUrl(e.target.value)}
                        placeholder="e.g. gs://omnimeme-assets/products/blender.png"
                      />
                    </div>
                  </div>
                )}
              </div>

              <button type="submit" className="btn-primary" disabled={isGeneratingMashup} style={{ background: 'linear-gradient(135deg, #eab308, #ca8a04)' }}>
                <Sparkles size={18} />
                {isGeneratingMashup ? 'Generating Parody Storyboard...' : '🎭 Generate Parody Mashup Storyboard'}
              </button>
            </form>
          ) : (

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '8px', color: '#34d399', fontSize: '13px' }}>
                🎬 40-Second Multi-Turn Context Window & Conversational Video Timeline
              </div>

              {/* 40-Second Screening Room Timeline Scrubber */}
              {(() => {
                const cumulativeDuration = Math.min(40, screeningHistory.length * 10);
                const progressPct = (cumulativeDuration / 40) * 100;
                const turnBadges = [
                  { label: '0–10s', turnIndex: 0 },
                  { label: '10–20s', turnIndex: 1 },
                  { label: '20–30s', turnIndex: 2 },
                  { label: '30–40s', turnIndex: 3 },
                ];
                return (
                  <div style={{ background: '#0b0d12', padding: '14px', borderRadius: '8px', border: '1px solid var(--panel-border)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#9ca3af', fontWeight: 600 }}>
                      <span style={{ color: '#34d399' }}>Timeline Scrubber</span>
                      <span>Cumulative Duration: {cumulativeDuration}s / 40s</span>
                    </div>

                    <div style={{ width: '100%', background: '#1e293b', height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${progressPct}%`,
                          background: 'linear-gradient(90deg, #3b82f6, #10b981)',
                          height: '100%',
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginTop: '4px' }}>
                      {turnBadges.map((slot) => {
                        const turnObj = screeningHistory[screeningHistory.length - 1 - slot.turnIndex]; // chronological
                        const isActive = !!turnObj;
                        return (
                          <div
                            key={slot.label}
                            style={{
                              padding: '8px 4px',
                              borderRadius: '6px',
                              textAlign: 'center',
                              fontSize: '11px',
                              fontWeight: 600,
                              background: isActive ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                              border: `1px solid ${isActive ? 'rgba(16, 185, 129, 0.4)' : 'rgba(255, 255, 255, 0.08)'}`,
                              color: isActive ? '#34d399' : '#6b7280',
                            }}
                          >
                            <div>{slot.label}</div>
                            <div style={{ fontSize: '9px', marginTop: '2px', opacity: 0.8 }}>
                              {isActive ? `Turn #${slot.turnIndex + 1}` : 'Empty'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

              {screeningHistory.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: '#9ca3af', fontSize: '14px' }}>
                  No screening turns generated yet. Use Guided or Free-form Directing to generate your first video scene!
                </div>
              ) : (
                screeningHistory.map((turn, idx) => (
                  <div key={turn.id} style={{ background: '#0b0d12', border: '1px solid var(--panel-border)', borderRadius: '8px', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#9ca3af' }}>
                      <span style={{ fontWeight: 600, color: '#60a5fa' }}>Turn #{screeningHistory.length - idx}: {turn.timestamp}</span>
                      <span style={{ fontSize: '11px', background: 'rgba(59, 130, 246, 0.1)', color: '#93c5fd', padding: '2px 6px', borderRadius: '4px' }}>{turn.generation_mode}</span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#e5e7eb', margin: 0 }}>{turn.prompt}</p>
                    <div style={{ fontSize: '11px', color: '#6b7280' }}>Thread ID: {turn.interaction_thread_id}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right Column: Enhanced Output & Specs */}
        <div className="card-panel">
          <div className="panel-header">
            <h2 className="panel-title">
              {activeTab === 'scriptwriter' ? (
                <>
                  <Clapperboard size={20} color="#ec4899" />
                  Multi-Scene Storyboard & A2A Federation
                </>
              ) : activeTab === 'mashup' ? (
                <>
                  <Sparkles size={20} color="#eab308" />
                  Parody & Mashup Studio Storyboard
                </>
              ) : (
                <>
                  <Video size={20} color="#10b981" />
                  Gemini Omni Flash Video Directing Output
                </>
              )}
            </h2>
            {result && activeTab !== 'scriptwriter' && activeTab !== 'mashup' && (
              <button
                onClick={() => copyToClipboard(result.result.enhanced_prompt)}
                style={{ background: 'transparent', border: '1px solid var(--panel-border)', color: 'var(--text-muted)', borderRadius: '6px', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}
              >
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy Prompt'}
              </button>
            )}
          </div>

          {activeTab === 'mashup' ? (
            mashupStoryboard ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(234, 179, 8, 0.1)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(234, 179, 8, 0.3)' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#fef08a' }}>
                      Concept: {mashupStoryboard.storyboard.concept}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                      Genre: {mashupStoryboard.storyboard.mashup_genre || mashupGenre} | Tone: {mashupStoryboard.storyboard.parody_tone || parodyTone}
                      {mashupStoryboard.storyboard.product?.name && ` | Product: ${mashupStoryboard.storyboard.product.name}`}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isRenderingMashupChained}
                      onClick={handleRenderChainedMashupScenes}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                    >
                      <Link2 size={16} />
                      {isRenderingMashupChained ? 'Chaining Multi-Scene Extensions...' : '🔗 Render Chained Storyboard (Zero Visual Drift)'}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isRenderingMashup}
                      onClick={handleRenderAllMashupScenes}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #eab308, #ca8a04)' }}
                    >
                      <Film size={16} />
                      {isRenderingMashup ? 'Rendering Scenes...' : '🎬 Render All Mashup Scenes'}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isConcatenatingMashup}
                      onClick={handleConcatenateMashupMasterFilm}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #2563eb, #3b82f6)' }}
                    >
                      <Film size={16} />
                      {isConcatenatingMashup ? 'Exporting Master MP4...' : '🎬 Export Master Mashup MP4'}
                    </button>
                  </div>
                </div>

                {mashupMasterFilmUrl && (
                  <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '8px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ color: '#60a5fa', fontWeight: 600, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} color="#34d399" />
                      Master Parody Film Exported with Lower-Third Titles & Sponsor Banner!
                    </div>
                    <video src={mashupMasterFilmUrl} controls autoPlay loop style={{ width: '100%', borderRadius: '6px', border: '1px solid var(--panel-border)' }} />
                    <a href={mashupMasterFilmUrl} download target="_blank" rel="noreferrer" style={{ color: '#93c5fd', fontSize: '13px', textDecoration: 'underline' }}>
                      Download Master Parody MP4 ({mashupMasterFilmUrl})
                    </a>
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {mashupStoryboard.storyboard.scenes.map((scene: StoryboardScene) => (
                    <div
                      key={scene.scene_number}
                      style={{
                        background: '#0f1117',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '8px',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#fef08a', margin: 0 }}>
                          {scene.title}
                        </h4>
                        {scene.lower_third_title && (
                          <span style={{ fontSize: '11px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '2px 8px', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                            🎭 {scene.lower_third_title.name} ({scene.lower_third_title.role})
                          </span>
                        )}
                      </div>

                      <div style={{ fontSize: '13px', color: '#e5e7eb' }}>
                        <strong>Visual:</strong> {scene.visual_description}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', color: '#9ca3af' }}>
                        <div><strong>Camera:</strong> {scene.camera_instruction}</div>
                        <div><strong>Audio:</strong> {scene.audio_cue}</div>
                      </div>

                      {mashupRenderedScenes[scene.scene_number] ? (
                        <div style={{ background: '#07090e', padding: '10px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                          <div style={{ fontSize: '12px', color: '#34d399', fontWeight: 600, marginBottom: '6px' }}>
                            ✓ Rendered Scene Clip #{scene.scene_number}
                          </div>
                          <video src={mashupRenderedScenes[scene.scene_number].video_url} controls style={{ width: '100%', borderRadius: '4px' }} />
                        </div>
                      ) : (
                        <button
                          type="button"
                          className="btn-primary"
                          onClick={() => handleRenderSingleMashupScene(scene.scene_number, scene.video_config)}
                          style={{ padding: '6px 12px', fontSize: '12px', background: 'linear-gradient(135deg, #475569, #334155)', alignSelf: 'flex-start' }}
                        >
                          🎬 Render Scene Clip #{scene.scene_number}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <Sparkles size={36} color="#eab308" />
                <p>Select characters, mashup genre, and tone to generate a 30-60s Parody & Mashup Storyboard!</p>
              </div>
            )
          ) : activeTab === 'scriptwriter' ? (

            storyboard ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(236, 72, 153, 0.1)', padding: '14px', borderRadius: '8px', border: '1px solid rgba(236, 72, 153, 0.3)' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#f472b6' }}>
                      Concept: {storyboard.storyboard.concept}
                    </h3>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                      {storyboard.storyboard.scenes.length} Scenes Breakdown | Style: {storyboard.storyboard.style_preference || 'Default'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isRenderingChained}
                      onClick={handleRenderChainedStoryboard}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #10b981, #059669)' }}
                    >
                      <Link2 size={16} />
                      {isRenderingChained ? 'Chaining Multi-Scene Extensions...' : '🔗 Render Chained Storyboard (Zero Visual Drift)'}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isRenderingFederated}
                      onClick={handleRenderAllFederated}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #9333ea, #ec4899)' }}
                    >
                      <Film size={16} />
                      {isRenderingFederated ? 'Rendering All Scenes...' : '🎬 Render All Scenes via A2A Federation'}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={isConcatenating}
                      onClick={handleConcatenateMasterFilm}
                      style={{ padding: '8px 16px', fontSize: '13px', background: 'linear-gradient(135deg, #2563eb, #3b82f6)' }}
                    >
                      <Film size={16} />
                      {isConcatenating ? 'Exporting Master MP4...' : '🎬 Export Full Master Feature Film MP4'}
                    </button>
                  </div>
                </div>

                {masterFilmUrl && (
                  <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '8px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ color: '#60a5fa', fontWeight: 600, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} color="#34d399" />
                      Master Feature Film Rendered & Exported Successfully!
                    </div>
                    <video src={masterFilmUrl} controls autoPlay loop style={{ width: '100%', borderRadius: '6px', border: '1px solid var(--panel-border)' }} />
                    <a href={masterFilmUrl} download target="_blank" rel="noreferrer" style={{ color: '#93c5fd', fontSize: '13px', textDecoration: 'underline' }}>
                      Download Master Film MP4 ({masterFilmUrl})
                    </a>
                  </div>
                )}


                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {storyboard.storyboard.scenes.map((scene: StoryboardScene) => (
                    <div
                      key={scene.scene_number}
                      style={{
                        background: '#0f1117',
                        border: '1px solid var(--panel-border)',
                        borderRadius: '10px',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '14px', fontWeight: 600, color: '#ec4899' }}>
                          {scene.title}
                        </span>
                        {renderedScenes[scene.scene_number] ? (
                          <span style={{ fontSize: '12px', color: '#34d399', background: 'rgba(16, 185, 129, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                            ✓ Rendered MP4
                          </span>
                        ) : (
                          <span style={{ fontSize: '12px', color: '#9ca3af', background: 'rgba(255, 255, 255, 0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                            Ready to Render
                          </span>
                        )}
                      </div>

                      <div style={{ fontSize: '13px', color: '#d1d5db', lineHeight: 1.5 }}>
                        <strong>Visual Description:</strong> {scene.visual_description}
                      </div>

                      <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#9ca3af' }}>
                        <span>🎥 <strong>Camera:</strong> {scene.camera_instruction}</span>
                        <span>🎵 <strong>Audio:</strong> {scene.audio_cue}</span>
                      </div>

                      <div className="json-box" style={{ fontSize: '11px', maxHeight: '100px' }}>
                        <pre>{JSON.stringify(scene.video_config, null, 2)}</pre>
                      </div>

                      {renderedScenes[scene.scene_number] && (
                        <div style={{ marginTop: '8px' }}>
                          <video
                            src={renderedScenes[scene.scene_number].video_url}
                            controls
                            autoPlay
                            loop
                            style={{ width: '100%', borderRadius: '6px', border: '1px solid var(--panel-border)' }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ padding: '40px 20px', textAlign: 'center', color: '#9ca3af', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <Clapperboard size={48} color="#ec4899" style={{ opacity: 0.5 }} />
                <h3 style={{ fontSize: '16px', color: '#e5e7eb' }}>No Storyboard Generated Yet</h3>
                <p style={{ fontSize: '13px', maxWidth: '400px' }}>
                  Enter a creative concept on the left and click "Generate Multi-Scene Storyboard" to transform it into structured scene blueprints.
                </p>
              </div>
            )
          ) : loading || streamingText ? (
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label className="form-label">
                    Gemini Enterprise Agent Platform Payload Spec
                  </label>
                  <button
                    type="button"
                    className="btn-primary"
                    disabled={isRenderingVideo}
                    onClick={handleExecuteVideo}
                    style={{ padding: '6px 14px', fontSize: '13px', background: 'linear-gradient(135deg, #059669, #10b981)' }}
                  >
                    <Film size={15} />
                    {isRenderingVideo ? '🎬 Rendering Video & MP4...' : '🎬 Generate Video & Render MP4'}
                  </button>
                </div>
                <div className="json-box">
                  <pre>{JSON.stringify(result.result.video_config, null, 2)}</pre>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', background: 'rgba(59, 130, 246, 0.08)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)', fontSize: '13px', color: '#93c5fd' }}>
                <CheckCircle2 size={18} color="#60a5fa" />
                <span>Payload ready for Gemini Omni Flash Preview Generation Endpoint.</span>
              </div>

              {videoResult && (
                <div style={{ background: '#0b0d12', border: '1px solid var(--panel-border)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#f3f4f6', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Film size={18} color="#10b981" />
                      🎬 The Screening Room & Conversational Editing Suite
                    </h3>
                    <span style={{ fontSize: '12px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '3px 8px', borderRadius: '6px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      🛡️ SynthID C2PA Verified
                    </span>
                  </div>

                  <video
                    src={videoResult.video_url}
                    controls
                    autoPlay
                    loop
                    style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--panel-border)' }}
                  />

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', color: '#9ca3af' }}>
                    <div>
                      <span>Duration: {videoResult.duration_seconds}s</span> • <span>Mode: {videoResult.generation_mode}</span> • <span>Thread: {videoResult.interaction_thread_id}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <button
                        type="button"
                        className="btn-primary"
                        disabled={isRenderingVideo}
                        onClick={handleExtendScene}
                        style={{ padding: '6px 14px', fontSize: '13px', background: 'linear-gradient(135deg, #8b5cf6, #6366f1)' }}
                      >
                        ⏩ Extend Scene (+10s)
                      </button>
                      <a
                        href={videoResult.video_url}
                        download="omnimeme_rendered_video.mp4"
                        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: '#3b82f6', color: '#ffffff', padding: '6px 14px', borderRadius: '6px', textDecoration: 'none', fontWeight: 600, fontSize: '13px' }}
                      >
                        ⬇️ Download MP4
                      </a>
                    </div>
                  </div>

                  {/* Conversational Editing Form */}
                  <form onSubmit={handleConversationalEdit} style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                    <label className="form-label" style={{ fontSize: '13px', color: '#60a5fa' }}>
                      ✨ Conversational Video Editing (Multi-Turn Gemini Omni Flash)
                    </label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Describe what to add or change (e.g. Change lighting to magenta neon fog, make katana glow purple)..."
                        value={editPrompt}
                        onChange={(e) => setEditPrompt(e.target.value)}
                        disabled={isRenderingVideo}
                      />
                      <button
                        type="submit"
                        className="btn-primary"
                        disabled={isRenderingVideo || !editPrompt.trim()}
                        style={{ padding: '8px 16px', fontSize: '13px', whiteSpace: 'nowrap' }}
                      >
                        {isRenderingVideo ? 'Editing...' : '✨ Apply Edit'}
                      </button>
                    </div>
                  </form>

                  {/* 5-Star Feedback & Analytics Rating */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                    <label className="form-label" style={{ fontSize: '12px', color: '#9ca3af' }}>
                      📊 Rate Prompt Directing Quality (Streams to BigQuery Agent Analytics)
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            type="button"
                            onClick={() => handleRatingSubmit(screeningHistory[0]?.id || 'turn_current', star)}
                            style={{
                              background: 'transparent',
                              border: 'none',
                              fontSize: '20px',
                              cursor: 'pointer',
                              filter: (screeningHistory[0]?.rating || 0) >= star ? 'none' : 'grayscale(100%) opacity(0.3)'
                            }}
                          >
                            ⭐
                          </button>
                        ))}
                      </div>
                      {screeningHistory[0]?.rating ? (
                        <span style={{ fontSize: '12px', color: '#34d399', fontWeight: 600 }}>
                          ✓ Rated {screeningHistory[0].rating}/5 Stars! Recorded in BigQuery Telemetry.
                        </span>
                      ) : (
                        <input
                          type="text"
                          className="form-input"
                          style={{ height: '32px', fontSize: '12px' }}
                          placeholder="Optional feedback comment..."
                          value={feedbackComment}
                          onChange={(e) => setFeedbackComment(e.target.value)}
                        />
                      )}
                    </div>
                  </div>
                </div>
              )}
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

            <div style={{ background: 'rgba(59, 130, 246, 0.05)', padding: '10px 12px', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.2)', margin: '12px 0 4px 0' }}>
              <label className="form-label" style={{ color: '#60a5fa', fontSize: '12px', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} color="#60a5fa" />
                Visual Character Archetype Gallery Presets
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {archetypePresets.map((preset) => (
                  <button
                    key={preset.role_id}
                    type="button"
                    onClick={() => handleApplyArchetypePreset(preset)}
                    style={{
                      background: 'rgba(59, 130, 246, 0.15)',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      color: '#93c5fd',
                      borderRadius: '6px',
                      padding: '4px 10px',
                      fontSize: '11px',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    + {preset.name}
                  </button>
                ))}
              </div>
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

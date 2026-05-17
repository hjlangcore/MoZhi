import { create } from 'zustand'
import axios from 'axios'

const API_BASE = '/api/v1'

export interface Session {
  session_id: string
  session_name: string
  current_novel_id?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Novel {
  novel_id: string
  title: string
  theme: string
  status: string
  total_words: number
  current_chapter: number
  style_type: string
}

export interface Chapter {
  chapter_number: number
  title: string
  content: string
  status: string
  word_count: number
}

export interface WorldView {
  core_theme: string
  historical_events: string[]
  social_structure: {
    dominant_forces: string
    class_divisions: string
    core_conflicts: string
  }
  geography: {
    major_regions: string
    power_distribution: string
    key_locations: string
  }
  physics_rules: {
    power_system: string
    limitations: string
    cost_mechanism: string
  }
}

export interface Character {
  name: string
  age: number
  gender: string
  social_identity: string
  nickname: string
  wants: string
  needs: string
  fears: string
  weakness: string
  speech_style: string
  habits: string
  skills: string
  fatal_flaw: string
  arc_start: string
  trigger_event: string
  midpoint_change: string
  final_form: string
  role_type: 'protagonist' | 'mentor' | 'rival' | 'love_interest' | 'antagonist' | 'ally' | 'family'
}

export interface StyleSettings {
  narrative_perspective: 'first_person' | 'third_limited' | 'third_omniscient' | 'multi_perspective'
  narrative_rhythm: 'fast' | 'medium' | 'slow'
  language_style: 'concise' | 'flowery' | 'modern' | 'stream_of_consciousness'
  emotional_tone: 'epic_tragic' | 'light_hearted' | 'dark_oppressive' | 'warm_healing' | 'mixed'
  theme_depth: 'pure_entertainment' | 'social_metaphor' | 'philosophical'
}

export interface NovelSetting {
  novel_title: string
  world_view: WorldView
  main_character: Character
  supporting_characters: Character[]
  style_settings: StyleSettings
  main_plot_thread: string
  core_conflicts: string
}

export interface WritingStatus {
  is_writing: boolean
  status: string
  current_chapter: number
  total_words: number
  target_words: number
  progress_percent: number
}

interface AppState {
  sessions: Session[]
  currentSession: Session | null
  currentNovel: Novel | null
  currentSetting: NovelSetting | null
  chapters: Chapter[]
  writingStatus: WritingStatus | null
  sessionNovels: Novel[]
  selectedChapter: Chapter | null
  loading: boolean
  error: string | null
  pollingTimer: ReturnType<typeof setInterval> | null

  setError: (error: string | null) => void
  setLoading: (loading: boolean) => void

  fetchSessions: () => Promise<void>
  createSession: (name: string) => Promise<Session>
  selectSession: (session: Session) => void
  restoreSession: () => void
  deleteSession: (sessionId: string) => Promise<void>

  createNovel: (sessionId: string, theme: string, styleType: string) => Promise<Novel>
  deleteNovel: (novelId: string) => Promise<void>
  selectNovel: (novel: Novel) => void
  fetchNovel: (novelId: string) => Promise<void>
  fetchSetting: (novelId: string) => Promise<void>
  fetchSessionNovels: (sessionId: string) => Promise<void>

  fetchChapters: (novelId: string) => Promise<void>
  fetchChapterContent: (novelId: string, chapterNumber: number) => Promise<void>
  selectChapter: (chapter: Chapter | null) => void

  startWriting: (novelId: string, chapterWords?: number, lengthType?: string, customWords?: number) => Promise<void>
  stopWriting: (novelId: string) => Promise<void>
  startPolling: (novelId: string) => void
  stopPolling: () => void

  saveWorldView: (novelId: string, worldView: WorldView) => Promise<void>
  saveCharacter: (novelId: string, character: Character, isMain: boolean) => Promise<void>
  saveStyleSettings: (novelId: string, styleSettings: StyleSettings) => Promise<void>
  generateWorldView: (prompt: string) => Promise<WorldView | null>
  generateCharacter: (worldView: WorldView, roleType: string) => Promise<Character | null>
}

export const useStore = create<AppState>((set, get) => ({
  sessions: [],
  currentSession: null,
  currentNovel: null,
  currentSetting: null,
  chapters: [],
  writingStatus: null,
  sessionNovels: [],
  selectedChapter: null,
  loading: false,
  error: null,
  pollingTimer: null,

  setError: (error) => set({ error }),
  setLoading: (loading) => set({ loading }),

  restoreSession: () => {
    try {
      const saved = localStorage.getItem('fusion_current_session')
      if (saved) {
        const session = JSON.parse(saved)
        set({ currentSession: session })
      }
    } catch { /* ignore */ }
  },

  fetchSessions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await axios.get(`${API_BASE}/sessions/`)
      const sessions = response.data.data || []
      // 检查当前会话是否仍存在于服务端，不存在则清除
      set((state) => {
        const currentStillExists = state.currentSession
          && sessions.some((s: Session) => s.session_id === state.currentSession?.session_id)
        return {
          sessions,
          loading: false,
          currentSession: currentStillExists ? state.currentSession : null
        }
      })
      // 清除本地存储中的过期会话
      const { currentSession } = get()
      if (!currentSession) {
        localStorage.removeItem('fusion_current_session')
      }
    } catch (err: any) {
      set({ error: err.message, loading: false })
    }
  },

  createSession: async (name) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.post(`${API_BASE}/sessions/`, { session_name: name })
      const session = response.data.data
      set((state) => ({
        sessions: [...state.sessions, session],
        currentSession: session,
        loading: false
      }))
      return session
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  selectSession: (session) => {
    localStorage.setItem('fusion_current_session', JSON.stringify(session))
    set({ currentSession: session })
  },

  deleteSession: async (sessionId) => {
    set({ loading: true, error: null })
    try {
      await axios.delete(`${API_BASE}/sessions/${sessionId}`)
      localStorage.removeItem('fusion_current_session')
      set((state) => ({
        sessions: state.sessions.filter(s => s.session_id !== sessionId),
        currentSession: state.currentSession?.session_id === sessionId ? null : state.currentSession,
        loading: false
      }))
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  createNovel: async (sessionId, theme, styleType) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.post(`${API_BASE}/novels/`, {
        session_id: sessionId,
        theme,
        style_type: styleType
      })
      const novel = response.data.data
      set(() => ({
        currentNovel: novel,
        loading: false
      }))
      return novel
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  deleteNovel: async (novelId) => {
    set({ loading: true, error: null })
    try {
      await axios.delete(`${API_BASE}/novels/${novelId}`)
      set((state) => {
        const isCurrentNovel = state.currentNovel?.novel_id === novelId
        return {
          sessionNovels: state.sessionNovels.filter(n => n.novel_id !== novelId),
          currentNovel: isCurrentNovel ? null : state.currentNovel,
          currentSetting: isCurrentNovel ? null : state.currentSetting,
          chapters: isCurrentNovel ? [] : state.chapters,
          selectedChapter: isCurrentNovel ? null : state.selectedChapter,
          loading: false
        }
      })
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  selectNovel: (novel) => set({ currentNovel: novel }),

  fetchNovel: async (novelId) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.get(`${API_BASE}/novels/${novelId}`)
      set({ currentNovel: response.data.data, loading: false })
    } catch (err: any) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        set({
          currentNovel: null,
          currentSetting: null,
          chapters: [],
          selectedChapter: null,
          loading: false
        })
        return
      }
      set({ error: err.message, loading: false })
    }
  },


  fetchSessionNovels: async (sessionId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/sessions/${sessionId}/novels`)
      set({ sessionNovels: response.data.data || [] })
    } catch (err: any) {
      // 404 表示会话已不存在，清除过期状态
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        localStorage.removeItem('fusion_current_session')
        set({
          currentSession: null,
          currentNovel: null,
          currentSetting: null,
          chapters: [],
          selectedChapter: null,
          sessionNovels: []
        })
        return
      }
      set({ error: err.message })
    }
  },

  fetchSetting: async (novelId) => {
    try {
      const response = await axios.get(`${API_BASE}/novels/${novelId}/setting`)
      set({ currentSetting: response.data.data })
    } catch (err: any) {
      if (axios.isAxiosError(err) && err.response?.status === 404) return
      set({ error: err.message })
    }
  },

  fetchChapters: async (novelId) => {
    try {
      const response = await axios.get(`${API_BASE}/novels/${novelId}/chapters`)
      set({ chapters: response.data.data || [] })
    } catch (err: any) {
      if (axios.isAxiosError(err) && err.response?.status === 404) return
      set({ error: err.message })
    }
  },

  fetchChapterContent: async (novelId, chapterNumber) => {
    try {
      const response = await axios.get(`${API_BASE}/novels/${novelId}/chapters/${chapterNumber}`)
      set({ selectedChapter: response.data.data })
    } catch (err: any) {
      set({ error: err.message })
    }
  },

  selectChapter: (chapter) => set({ selectedChapter: chapter }),

  startWriting: async (novelId, chapterWords = 2000, lengthType = 'tomato', customWords = 0) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.post(
        `${API_BASE}/writing/${novelId}/start`,
        null,
        { params: { chapter_words: chapterWords, length_type: lengthType, custom_target_words: customWords } }
      )
      if (response.data.success) {
        // Fetch initial state, then connect WebSocket
        await Promise.all([
          get().fetchNovel(novelId),
          get().fetchChapters(novelId),
        ])
        get().startPolling(novelId)
      }
      set({ loading: false })
    } catch (err: any) {
      set({ error: err.message, loading: false })
    }
  },

  stopWriting: async (novelId) => {
    try {
      await axios.post(`${API_BASE}/writing/${novelId}/stop`)
      get().stopPolling()
    } catch (err: any) {
      set({ error: err.message })
    }
  },

  startPolling: (novelId) => {
    const { pollingTimer } = get()
    if (pollingTimer) clearInterval(pollingTimer)

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${proto}//${window.location.host}/api/v1/ws/${novelId}`
    const socket = new WebSocket(wsUrl)

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'chapter_update') {
          set({
            writingStatus: {
              is_writing: msg.status === 'writing',
              status: msg.status,
              current_chapter: msg.current_chapter,
              total_words: msg.total_words,
              target_words: 500000,
              progress_percent: Math.min(100, Math.round((msg.total_words / 500000) * 100)),
            },
            currentNovel: {
              ...get().currentNovel!,
              status: msg.status,
              total_words: msg.total_words,
              current_chapter: msg.current_chapter,
            },
          })
          // Update chapter in list
          if (msg.chapter) {
            const chs = [...get().chapters]
            const idx = chs.findIndex(c => c.chapter_number === msg.chapter.chapter_number)
            if (idx >= 0) {
              chs[idx] = msg.chapter
            } else {
              chs.push(msg.chapter)
            }
            set({ chapters: chs })
          }
          if (msg.status !== 'writing') {
            get().stopPolling()
          }
        }
      } catch {}
    }

    socket.onclose = () => {
      set({ pollingTimer: null })
    }

    set({ pollingTimer: socket as unknown as ReturnType<typeof setInterval> })
  },

  stopPolling: () => {
    const { pollingTimer } = get()
    if (pollingTimer) {
      try {
        const ws = pollingTimer as unknown as WebSocket
        if (ws.readyState === WebSocket.OPEN) {
          ws.close()
        }
      } catch {}
      set({ pollingTimer: null })
    }
  },

  saveWorldView: async (novelId, worldView) => {
    set({ loading: true, error: null })
    try {
      await axios.post(`${API_BASE}/novels/${novelId}/worldview`, worldView)
      set((state) => ({
        currentSetting: state.currentSetting ? {
          ...state.currentSetting,
          world_view: worldView
        } : null,
        loading: false
      }))
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  saveCharacter: async (novelId, character, isMain) => {
    set({ loading: true, error: null })
    try {
      await axios.post(`${API_BASE}/novels/${novelId}/characters`, { character, is_main: isMain })
      set((state) => {
        if (!state.currentSetting) return { loading: false }
        if (isMain) {
          return {
            currentSetting: { ...state.currentSetting, main_character: character },
            loading: false
          }
        } else {
          const exists = state.currentSetting.supporting_characters.find(
            c => c.name === character.name
          )
          if (exists) {
            return {
              currentSetting: {
                ...state.currentSetting,
                supporting_characters: state.currentSetting.supporting_characters.map(
                  c => c.name === character.name ? character : c
                )
              },
              loading: false
            }
          } else {
            return {
              currentSetting: {
                ...state.currentSetting,
                supporting_characters: [...state.currentSetting.supporting_characters, character]
              },
              loading: false
            }
          }
        }
      })
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  saveStyleSettings: async (novelId, styleSettings) => {
    set({ loading: true, error: null })
    try {
      await axios.post(`${API_BASE}/novels/${novelId}/style`, styleSettings)
      set((state) => ({
        currentSetting: state.currentSetting ? {
          ...state.currentSetting,
          style_settings: styleSettings
        } : null,
        loading: false
      }))
    } catch (err: any) {
      set({ error: err.message, loading: false })
      throw err
    }
  },

  generateWorldView: async (prompt) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.post(`${API_BASE}/ai/generate/worldview`, { prompt })
      const worldView = response.data.data as WorldView
      set({ loading: false })
      return worldView
    } catch (err: any) {
      set({ error: err.message, loading: false })
      return null
    }
  },

  generateCharacter: async (worldView, roleType) => {
    set({ loading: true, error: null })
    try {
      const response = await axios.post(`${API_BASE}/ai/generate/character`, { worldView, roleType })
      const character = response.data.data as Character
      set({ loading: false })
      return character
    } catch (err: any) {
      set({ error: err.message, loading: false })
      return null
    }
  },

}))

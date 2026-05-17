import { useEffect, useState } from 'react'
import { Layout, ConfigProvider, Spin } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'
import NovelPanel from './components/NovelPanel'
import SessionsPanel from './components/SessionsPanel'
import Sidebar from './components/Sidebar'
import WorldBuildingPanel from './components/WorldBuildingPanel'
import CharacterPanel from './components/CharacterPanel'
import StylePanel from './components/StylePanel'
import { useStore } from './store'
import zhCN from 'antd/locale/zh_CN'
import type { ThemeConfig } from 'antd'

const { Header, Content, Sider } = Layout

type PanelType = 'novel' | 'sessions' | 'worldview' | 'character' | 'style'

const inkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#c04040',
    colorSuccess: '#5a8a3c',
    colorWarning: '#b8860b',
    colorError: '#c04040',
    colorInfo: '#6b5c4a',
    colorTextBase: '#3d3222',
    colorBgBase: '#faf7f0',
    fontFamily: "'Noto Serif SC', 'STKaiti', 'KaiTi', 'SimSun', 'Microsoft YaHei', serif",
    borderRadius: 2,
    wireframe: false,
  },
  components: {
    Button: {
      primaryColor: '#faf7f0',
      defaultBg: '#f5f0e8',
      defaultBorderColor: '#d4c5b2',
      defaultColor: '#3d3222',
    },
    Menu: {
      darkItemBg: 'transparent',
      darkItemSelectedBg: 'rgba(192, 64, 64, 0.25)',
      darkItemHoverBg: 'rgba(192, 64, 64, 0.1)',
    },
    Input: {
      activeBorderColor: '#c04040',
      hoverBorderColor: '#b8a48e',
    },
    Select: {
      optionSelectedBg: 'rgba(192, 64, 64, 0.08)',
    },
    Modal: {
      contentBg: '#faf7f0',
      headerBg: '#f5f0e8',
    },
    Progress: {
      defaultColor: '#c04040',
    },
    
    Radio: {
      colorPrimary: '#c04040',
    },
  },
}

function App() {
  const { currentSession, fetchSessions, createSession, selectSession, restoreSession } = useStore()
  const [activePanel, setActivePanel] = useState<PanelType>('novel')

  useEffect(() => {
    initDefaultSession()
  }, [])

  const initDefaultSession = async () => {
    restoreSession()
    await fetchSessions()
    const state = useStore.getState()
    if (state.sessions.length > 0) {
      if (!state.currentSession) {
        selectSession(state.sessions[0])
      }
      return
    }
    try {
      await createSession('默认写作会话')
    } catch {
      // ignore
    }
  }

  const renderPanel = () => {
    switch (activePanel) {
      case 'sessions':
        return <SessionsPanel />
      case 'novel':
        return <NovelPanel />
      case 'worldview':
        return <WorldBuildingPanel />
      case 'character':
        return <CharacterPanel />
      case 'style':
        return <StylePanel />
      default:
        return <NovelPanel />
    }
  }

  if (!currentSession) {
    return (
      <ConfigProvider locale={zhCN} theme={inkTheme}>
        <Layout style={{ minHeight: '100vh' }}>
          <Header style={{ display: 'flex', alignItems: 'center', background: '#1a1410' }}>
            <h1 style={{ color: '#d4c5b2', fontFamily: "'Noto Serif SC', serif", margin: 0 }}>墨 · Fusion Project</h1>
          </Header>
          <Content style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Spin size="large" indicator={<LoadingOutlined style={{ fontSize: 28, color: '#c04040' }} />}>
              <div style={{ marginTop: 12, color: '#8b7355', fontFamily: "'Noto Serif SC', serif" }}>正在初始化写作工坊…</div>
            </Spin>
          </Content>
        </Layout>
      </ConfigProvider>
    )
  }

  return (
    <ConfigProvider locale={zhCN} theme={inkTheme}>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ display: 'flex', alignItems: 'center', background: '#1a1410' }}>
          <h1 style={{ color: '#d4c5b2', fontFamily: "'Noto Serif SC', serif", margin: 0 }}>墨 · Fusion Project</h1>
        </Header>
        <Layout>
          <Sider width={180} style={{ background: '#2c1810' }}>
            <Sidebar activePanel={activePanel} setActivePanel={setActivePanel} />
          </Sider>
          <Content style={{ padding: 24, background: '#faf7f0', overflow: 'auto' }}>
            {renderPanel()}
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

export default App

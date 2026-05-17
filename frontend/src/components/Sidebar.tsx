import { Menu } from 'antd'
import { BookOutlined, FolderOutlined, GlobalOutlined, UserOutlined, AlertOutlined } from '@ant-design/icons'
import { useStore } from '../store'

type PanelType = 'novel' | 'sessions' | 'worldview' | 'character' | 'style'

interface SidebarProps {
  activePanel: PanelType
  setActivePanel: (panel: PanelType) => void
}

function Sidebar({ activePanel, setActivePanel }: SidebarProps) {
  const { currentSession } = useStore()

  const getSelectedKey = () => {
    return activePanel
  }

  return (
    <div style={{ padding: '12px 0' }}>
      <div style={{
        padding: '8px 24px 16px',
        color: '#8b7355',
        fontSize: '12px',
        letterSpacing: '2px',
        fontFamily: "'Noto Serif SC', serif",
        borderBottom: '1px solid #3d3222',
        marginBottom: '8px',
      }}>
        笔墨工坊
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[getSelectedKey()]}
        onClick={({ key }) => {
          setActivePanel(key as PanelType)
        }}
        items={[
          {
            key: 'sessions',
            icon: <FolderOutlined />,
            label: '会话',
          },
          {
            key: 'novel',
            icon: <BookOutlined />,
            label: 'AI 写作工坊',
            disabled: !currentSession,
          },
          {
            key: 'worldview',
            icon: <GlobalOutlined />,
            label: '世界观构建',
            disabled: !currentSession,
          },
          {
            key: 'character',
            icon: <UserOutlined />,
            label: '角色设计',
            disabled: !currentSession,
          },
          {
            key: 'style',
            icon: <AlertOutlined />,
            label: '风格设定',
            disabled: !currentSession,
          },
        ]}
      />
    </div>
  )
}

export default Sidebar
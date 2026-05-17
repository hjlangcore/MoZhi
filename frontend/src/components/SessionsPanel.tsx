import { useEffect, useState } from 'react'
import { List, Button, Input, Modal, Form, message } from 'antd'
import { useStore } from '../store'

function SessionsPanel() {
  const {
    sessions,
    currentSession,
    loading,
    error,
    fetchSessions,
    restoreSession,
    createSession,
    selectSession,
    deleteSession,
  } = useStore()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const handleDelete = async (sessionId: string) => {
    try {
      await deleteSession(sessionId)
      message.success('会话删除成功')
    } catch {
      message.error('删除会话失败')
    } finally {
      setDeletingId(null)
    }
  }

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchSessions().then(() => restoreSession())
  }, [])

  const handleCreateSession = async (values: { session_name: string }) => {
    try {
      await createSession(values.session_name)
      message.success('会话创建成功')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      message.error('创建会话失败')
    }
  }

  return (
    <div className="panel">
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>会话管理</h2>
        <Button type="primary" onClick={() => setIsModalOpen(true)}>
          新建会话
        </Button>
      </div>

      {error && <div className="error-container">{error}</div>}

      <List
        loading={loading}
        dataSource={sessions}
        renderItem={(session) => {
          const isActive = currentSession?.session_id === session.session_id
          return (
            <List.Item
              className={`session-item ${isActive ? 'active' : ''}`}
              style={{
                background: isActive ? 'rgba(192, 64, 64, 0.06)' : 'transparent',
                borderColor: isActive ? '#c04040' : '#e8ddd0',
                borderRadius: '4px',
                marginBottom: '8px',
                border: `1px solid ${isActive ? '#c04040' : '#e8ddd0'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
              onClick={() => selectSession(session)}
            >
              <div style={{ flex: 1 }}>
                <List.Item.Meta
                  title={<span style={{ color: '#2c2416', fontWeight: 600 }}>{session.session_name}</span>}
                  description={<span style={{ color: '#8b7355' }}>{`创建于: ${new Date(session.created_at).toLocaleDateString()}`}</span>}
                />
              </div>
              <Button
                danger
                size="small"
                aria-label="删除会话"
                style={{ borderColor: '#d4c5b2', color: '#8b7355' }}
                onClick={e => {
                  e.stopPropagation()
                  setDeletingId(session.session_id)
                }}
              >删除</Button>
            </List.Item>
          )
        }}
        locale={{ emptyText: '暂无会话，点击上方按钮创建一个新会话' }}
      />

      <Modal
        title="确认删除会话"
        open={!!deletingId}
        onCancel={() => setDeletingId(null)}
        onOk={() => deletingId && handleDelete(deletingId)}
        okText="删除"
        okButtonProps={{ danger: true }}
        cancelText="取消"
        confirmLoading={loading}
      >
        <p>删除后不可恢复，确定要删除该会话吗？</p>
      </Modal>

      <Modal
        title="新建会话"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleCreateSession} layout="vertical">
          <Form.Item
            name="session_name"
            label="会话名称"
            rules={[{ required: true, message: '请输入会话名称' }]}
          >
            <Input placeholder="请输入会话名称…" autoComplete="off" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SessionsPanel
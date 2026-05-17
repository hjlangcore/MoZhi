import { useEffect, useState } from 'react'
import {
  Button, Input, Modal, Form, Select, Card, Row, Col, Progress,
  Tag, message, List, Typography, Divider, Spin, Empty, Space, Statistic, Alert, Popconfirm, App
} from 'antd'
import {
  PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined,
  BookOutlined, ThunderboltOutlined, FileTextOutlined, DeleteOutlined, LoadingOutlined
} from '@ant-design/icons'
import { useStore } from '../store'

const { TextArea } = Input
const { Title, Text } = Typography

function NovelPanel() {
  const {
    currentSession,
    currentNovel,
    currentSetting,
    chapters,
    selectedChapter,
    writingStatus,
    loading,
    error,
    createNovel,
    fetchNovel,
    deleteNovel,
    fetchSetting,
    fetchChapters,
    fetchChapterContent,
    startWriting,
    stopWriting,
    sessionNovels,
    fetchSessionNovels,
  } = useStore()

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [isWriteModalOpen, setIsWriteModalOpen] = useState(false)
  const [writeForm] = Form.useForm()
  const [messageApi, contextHolder] = message.useMessage()

  const isWriting = writingStatus?.is_writing || false
  const isCompleted = currentNovel?.status === 'completed'
  const canStart = currentNovel && !isWriting && !isCompleted

  useEffect(() => {
    if (currentSession) {
      fetchSessionNovels(currentSession.session_id)
    }
  }, [currentSession?.session_id])

  useEffect(() => {
    if (currentNovel) {
      fetchSetting(currentNovel.novel_id)
      fetchChapters(currentNovel.novel_id)
    }
  }, [currentNovel?.novel_id])

  const handleCreateNovel = async (values: { theme: string; style_type: string }) => {
    if (!currentSession) {
      messageApi.error('请先选择一个会话')
      return
    }
    try {
      await createNovel(currentSession.session_id, values.theme, values.style_type)
      messageApi.success('小说创建成功！点击「开始自动写作」启动 AI 创作')
      setIsModalOpen(false)
      form.resetFields()
    } catch {
      messageApi.error('创建小说失败')
    }
  }

  const handleStartWriting = async (values: { chapter_words: number; length_type: string; custom_words?: number }) => {
    if (!currentNovel) return
    const chapterWords = values.chapter_words || 2000
    const lengthType = values.length_type || 'tomato'
    const customWords = values.custom_words || 0
    try {
      await startWriting(currentNovel.novel_id, chapterWords, lengthType, customWords)
      messageApi.success(`AI 开始自动写作！目标 ${customWords > 0 ? customWords.toLocaleString() : (lengthType === 'tomato' ? '500,000' : '300,000')} 字`)
      setIsWriteModalOpen(false)
    } catch {
      messageApi.error('启动写作失败')
    }
  }

  const handleQuickStart = async (preset: string) => {
    if (!currentNovel) return
    const presets: Record<string, { chapterWords: number; lengthType: string; customWords: number }> = {
      tomato: { chapterWords: 2200, lengthType: 'tomato', customWords: 0 },
      '50w': { chapterWords: 2200, lengthType: 'custom', customWords: 500000 },
      '30w': { chapterWords: 2000, lengthType: 'custom', customWords: 300000 },
      '10w': { chapterWords: 2000, lengthType: 'custom', customWords: 100000 },
    }
    const p = presets[preset]
    if (!p) return
    try {
      await startWriting(currentNovel.novel_id, p.chapterWords, p.lengthType, p.customWords)
      const label = preset === 'tomato' ? '番茄模式·50万字' : `${(p.customWords / 10000).toFixed(0)}万字`
      messageApi.success(`AI 开始自动写作！${label}，目标 ~${Math.floor(p.customWords / p.chapterWords)} 章`)
    } catch {
      messageApi.error('启动写作失败')
    }
  }

  const handleStopWriting = async () => {
    if (!currentNovel) return
    try {
      await stopWriting(currentNovel.novel_id)
      messageApi.info('已发送停止信号，AI 将在当前章节完成后停止')
    } catch {
      messageApi.error('停止失败')
    }
  }

  const handleReadChapter = (chapter: any) => {
    if (!currentNovel) return
    fetchChapterContent(currentNovel.novel_id, chapter.chapter_number)
  }

  const handleSelectNovel = (novelId: string) => {
    if (!currentSession) return
    fetchNovel(novelId)
    fetchSetting(novelId)
    fetchChapters(novelId)
  }

  const handleDeleteNovel = async (novelId: string) => {
    try {
      await deleteNovel(novelId)
      messageApi.success('草稿已删除')
    } catch {
      messageApi.error('删除失败')
    }
  }

  if (!currentSession) {
    return (
      <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <Spin size="large" indicator={<LoadingOutlined style={{ fontSize: 28, color: '#c04040' }} />}>
          <div style={{ marginTop: 12, color: '#8b7355', fontFamily: "'Noto Serif SC', serif" }}>正在初始化写作工坊…</div>
        </Spin>
      </div>
    )
  }

  return (
    <App>
    {contextHolder}
    <div className="panel" style={{ overflow: 'auto', height: '100%' }}>
      {/* 历史小说 */}
      {sessionNovels.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{
            fontSize: '14px',
            color: '#8b7355',
            marginBottom: '12px',
            letterSpacing: '1px',
            fontFamily: "'Noto Serif SC', serif",
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <BookOutlined /> 我的小说
          </div>
          <Row gutter={[12, 12]}>
            {sessionNovels.map((novel) => {
              const isCurrent = currentNovel?.novel_id === novel.novel_id
              return (
                <Col key={novel.novel_id} xs={24} sm={12} md={8}>
                  <Card
                    size="small"
                    hoverable
                    onClick={() => handleSelectNovel(novel.novel_id)}
                    style={{
                      borderColor: isCurrent ? '#c04040' : '#e8ddd0',
                      background: isCurrent ? 'rgba(192,64,64,0.04)' : '#faf7f0',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ color: '#2c2416', fontFamily: "'Noto Serif SC', serif" }}>
                        {novel.title}
                      </Text>
                      <Space size={4}>
                        <Tag color={novel.status === 'completed' ? 'green' : novel.status === 'writing' ? 'red' : 'default'}>
                          {novel.status === 'completed' ? '已完成' : novel.status === 'writing' ? '写作中' : '草稿'}
                        </Tag>
                        <Popconfirm
                          title="确定删除此草稿？"
                          description="删除后无法恢复"
                          onConfirm={() => handleDeleteNovel(novel.novel_id)}
                          okText="删除"
                          cancelText="取消"
                          okButtonProps={{ danger: true }}
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            aria-label="删除草稿"
                            onClick={(e) => e.stopPropagation()}
                            style={{ padding: '0 4px' }}
                          />
                        </Popconfirm>
                      </Space>
                    </div>
                    <div style={{ marginTop: 8, fontSize: '12px', color: '#8b7355' }}>
                      {novel.total_words?.toLocaleString() || 0} 字 · {novel.current_chapter || 0} 章
                      {novel.style_type && <span> · {novel.style_type}</span>}
                    </div>
                  </Card>
                </Col>
              )
            })}
          </Row>
          <Divider style={{ margin: '16px 0', borderColor: '#e8ddd0' }} />
        </div>
      )}

      {/* Header */}
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>小说创作</h2>
        <Space>
          {canStart && (
            <Space>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                aria-label="番茄模式快速启动"
                onClick={() => handleQuickStart('tomato')}
                size="large"
                style={{ background: '#c04040', borderColor: '#c04040' }}
              >
                番茄模式·50万字
              </Button>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                aria-label="快速启动50万字"
                onClick={() => handleQuickStart('50w')}
                size="large"
                style={{ background: '#fa8c16', borderColor: '#fa8c16' }}
              >
                快速·50万字
              </Button>
              <Button
                icon={<PlayCircleOutlined />}
                aria-label="自定义写作参数"
                onClick={() => setIsWriteModalOpen(true)}
              >
                自定义...
              </Button>
            </Space>
          )}
          {isWriting && (
            <Button
              danger
              icon={<PauseCircleOutlined />}
              aria-label="停止写作"
              onClick={handleStopWriting}
              size="large"
            >
              停止写作
            </Button>
          )}
          <Button icon={<ReloadOutlined />} aria-label="刷新数据" onClick={() => {
            if (currentNovel) {
              fetchSetting(currentNovel.novel_id)
              fetchChapters(currentNovel.novel_id)
            }
          }}>
            刷新
          </Button>
          {!currentNovel && (
            <Button type="primary" onClick={() => setIsModalOpen(true)}>
              创建小说
            </Button>
          )}
        </Space>
      </div>

      {/* Quick Start Presets */}
      {canStart && (
        <Card variant="borderless" style={{ marginBottom: 16, background: 'rgba(184, 134, 11, 0.04)', border: '1px solid rgba(184, 134, 11, 0.3)' }}>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <Text strong style={{ marginRight: 8 }}>快捷启动：</Text>
            <Button size="small" type="primary" danger onClick={() => handleQuickStart('tomato')}>
              🍅 番茄模式 (50万字/2200字每章)
            </Button>
            <Button size="small" onClick={() => handleQuickStart('50w')}>
              50万字快速
            </Button>
            <Button size="small" onClick={() => handleQuickStart('30w')}>
              30万字
            </Button>
            <Button size="small" onClick={() => handleQuickStart('10w')}>
              10万字测试
            </Button>
            <Button size="small" type="dashed" onClick={() => setIsWriteModalOpen(true)}>
              自定义参数...
            </Button>
          </div>
        </Card>
      )}

      {error && <Alert message={error} type="error" closable style={{ marginBottom: 16 }} />}

      {!currentNovel && (
        <Empty
          description="暂无小说项目"
          style={{ marginTop: 60 }}
        >
          <Button type="primary" onClick={() => setIsModalOpen(true)}>
            创建第一部小说
          </Button>
        </Empty>
      )}

      {/* Writing Status Bar */}
      {currentNovel && writingStatus && (
        <Card variant="borderless" style={{ marginBottom: 16, background: isWriting ? '#f6ffed' : '#f0f0f0' }}>
          <Row gutter={24} align="middle">
            <Col span={4}>
              <Statistic
                title="进度"
                value={writingStatus.progress_percent.toFixed(1)}
                suffix="%"
                prefix={<ThunderboltOutlined spin={isWriting} />}
              />
            </Col>
            <Col span={4}>
              <Statistic title="已完成章节" value={writingStatus.current_chapter} />
            </Col>
            <Col span={4}>
              <Statistic title="总字数" value={writingStatus.total_words.toLocaleString()} />
            </Col>
            <Col span={4}>
              <Statistic title="目标字数" value={writingStatus.target_words.toLocaleString()} />
            </Col>
            <Col span={4}>
              <Tag
                color={isWriting ? 'processing' : isCompleted ? 'success' : 'default'}
                style={{ fontSize: 14, padding: '4px 12px' }}
              >
                {isWriting ? 'AI 正在创作中...' : isCompleted ? '创作完成' : writingStatus.status}
              </Tag>
            </Col>
            <Col span={4}>
              {isWriting && (
                <Button
                  danger
                  size="small"
                  icon={<PauseCircleOutlined />}
                  aria-label="停止写作"
                  onClick={handleStopWriting}
                >
                  停止
                </Button>
              )}
            </Col>
          </Row>
          <Progress
            percent={Math.min(100, Math.round(writingStatus.progress_percent))}
            status={isWriting ? 'active' : isCompleted ? 'success' : 'normal'}
            strokeColor={isWriting ? '#1890ff' : '#52c41a'}
            style={{ marginTop: 16 }}
          />
        </Card>
      )}

      {/* Main content area: chapter list + chapter reader */}
      {currentNovel && (
        <Row gutter={16} style={{ height: 'calc(100vh - 340px)' }}>
            {currentSetting && (
              <div style={{
                marginBottom: 12,
                padding: 12,
                background: 'rgba(44,36,22,0.03)',
                borderRadius: 4,
                border: '1px solid #e8ddd0',
              }}>
                <div style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#2c2416',
                  marginBottom: 6,
                  fontFamily: "'Noto Serif SC', serif",
                }}>
                  <BookOutlined style={{ marginRight: 4 }} />
                  {currentSetting.novel_title || '大纲'}
                </div>
                <div style={{ fontSize: 11, color: '#8b7355', lineHeight: 1.8 }}>
                  {currentSetting.main_character?.name && (
                    <div>主角：{currentSetting.main_character.name}</div>
                  )}
                  <div>风格：{currentSetting.style_settings?.narrative_perspective || '未知'}</div>
                  <div>章节：{chapters.length} 章 · {currentNovel?.total_words?.toLocaleString() || 0} 字</div>
                </div>
              </div>
            )}

            {currentSetting && (
              <div style={{
                marginBottom: 12,
                padding: '8px 12px',
                background: '#faf7f0',
                borderRadius: 4,
                border: '1px solid #e8ddd0',
                maxHeight: 200,
                overflowY: 'auto',
              }}>
                <div style={{ fontSize: 12, color: '#8b7355', marginBottom: 4, letterSpacing: 1 }}>
                  世界观概览
                </div>
                <div style={{ fontSize: 11, color: '#6b5c4a', lineHeight: 1.7 }}>
                  {currentSetting.world_view?.core_theme?.slice(0, 200) || '暂无'}
                </div>
              </div>
            )}

{/* Left: Chapter List */}
          <Col span={8} style={{ height: '100%', overflow: 'auto', borderRight: '1px solid #f0f0f0' }}>
            <div style={{ padding: '0 8px' }}>
              <Title level={5}>
                <BookOutlined /> 章节列表
                {chapters.length > 0 && <Tag style={{ marginLeft: 8 }}>{chapters.length} 章</Tag>}
                {isWriting && <Spin size="small" style={{ marginLeft: 8 }} />}
              </Title>
            </div>

            {chapters.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#8b7355' }}>
                {isWriting ? (
                  <div>
                    <Spin size="large" />
                    <p style={{ marginTop: 16 }}>AI 正在构思第一章，请稍候...</p>
                  </div>
                ) : (
                  <p>点击「开始自动写作」启动 AI 创作</p>
                )}
              </div>
            ) : (
              <List
                size="small"
                dataSource={[...chapters].reverse()}
                renderItem={(chapter: any) => (
                  <List.Item
                    onClick={() => handleReadChapter(chapter)}
                    style={{
                      cursor: 'pointer',
                      padding: '10px 12px',
                      borderRadius: 6,
                      marginBottom: 4,
                      background: selectedChapter?.chapter_number === chapter.chapter_number ? '#e6f7ff' : 'transparent',
                      border: selectedChapter?.chapter_number === chapter.chapter_number ? '1px solid #1890ff' : '1px solid transparent',
                    }}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text strong>第{chapter.chapter_number}章</Text>
                          <Text style={{ fontSize: 13 }}>{chapter.title}</Text>
                        </Space>
                      }
                      description={
                        <Space size={8}>
                          <Tag color="blue">{chapter.word_count?.toLocaleString() || 0} 字</Tag>
                          <Tag>{chapter.status}</Tag>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
                style={{ paddingRight: 8 }}
              />
            )}
          </Col>

          {/* Right: Chapter Content Reader */}
          <Col span={16} style={{ height: '100%', overflow: 'auto' }}>
            {selectedChapter ? (
              <div style={{ padding: '0 16px' }}>
                <Title level={4}>
                  第{selectedChapter.chapter_number}章 {selectedChapter.title}
                </Title>
                <Divider />
                <div style={{
                  fontSize: 15,
                  lineHeight: 2.2,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'Georgia, "Noto Serif SC", serif',
                  color: '#333'
                }}>
                  {selectedChapter.content || '(暂无内容)'}
                </div>
              </div>
            ) : (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 16
              }}>
                <FileTextOutlined style={{ fontSize: 48, color: '#d4c5b2' }} />
                <Text type="secondary">点击左侧章节开始阅读</Text>
                {isWriting && (
                  <Text type="secondary">
                    <Spin size="small" /> AI 正在创作中，新章节将自动出现
                  </Text>
                )}
              </div>
            )}
          </Col>
        </Row>
      )}

      {/* Create Novel Modal */}
      <Modal
        title="创建小说"
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form form={form} onFinish={handleCreateNovel} layout="vertical">
          <Form.Item
            name="theme"
            label="小说主题"
            rules={[{ required: true, message: '请输入小说主题' }]}
          >
            <TextArea
              rows={4}
              placeholder="例如：玄幻修仙，主角天生废柴，逆袭成仙…"
            />
          </Form.Item>
          <Form.Item
            name="style_type"
            label="文风类型"
            rules={[{ required: true, message: '请选择文风类型' }]}
            initialValue="番茄模式"
          >
            <Select placeholder="请选择文风类型…">
              <Select.Option value="番茄模式">🍅 番茄模式 — 快节奏爽文，适合番茄小说平台</Select.Option>
              <Select.Option value="凡人流">凡人流 — 贴近现实，一步一个脚印</Select.Option>
              <Select.Option value="热血">热血 — 激情澎湃，成长迅速</Select.Option>
              <Select.Option value="隐忍">隐忍 — 低调内敛，后期爆发</Select.Option>
              <Select.Option value="宏大">宏大 — 世界观庞大，势力纷杂</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              创建小说
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Writing Config Modal */}
      <Modal
        title="自定义写作参数"
        open={isWriteModalOpen}
        onCancel={() => setIsWriteModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form form={writeForm} onFinish={handleStartWriting} layout="vertical"
          initialValues={{ chapter_words: 2200, length_type: 'tomato', custom_words: 500000 }}
        >
          <Form.Item name="length_type" label="篇幅预设">
            <Select>
              <Select.Option value="tomato">🍅 番茄推荐 (50万字)</Select.Option>
              <Select.Option value="short">短篇 (3万字)</Select.Option>
              <Select.Option value="mid">中篇 (10万字)</Select.Option>
              <Select.Option value="long">长篇 (30万字)</Select.Option>
              <Select.Option value="custom">自定义字数</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="custom_words" label="自定义总字数（仅自定义模式）">
            <Input type="number" placeholder="500000" addonAfter="字" autoComplete="off" />
          </Form.Item>
          <Form.Item name="chapter_words" label="每章字数" rules={[{ required: true }]}>
            <Select>
              <Select.Option value={2000}>2000字/章</Select.Option>
              <Select.Option value={2200}>2200字/章（番茄推荐）</Select.Option>
              <Select.Option value={2500}>2500字/章</Select.Option>
              <Select.Option value={3000}>3000字/章</Select.Option>
            </Select>
          </Form.Item>
          <Alert
            message="番茄小说投稿提示"
            description="每章2000-2200字最佳，50万字可签约+首秀+书测全流程覆盖。签约2万字、首秀10万字、书测30万字。建议日更4000字。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              开始 AI 自动写作
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
    </App>
  )
}

export default NovelPanel

import { useState, useEffect } from 'react'
import { Card, Form, Button, Row, Col, Divider, Tag, message, Radio, Input, App } from 'antd'
import { AlertOutlined, EyeOutlined, ApiOutlined, HeartOutlined, BookOutlined, SaveOutlined, SearchOutlined } from '@ant-design/icons'
import { useStore } from '../store'
import type { StyleSettings } from '../store'

const { TextArea } = Input

const perspectiveOptions = [
  { value: 'first_person', label: '第一人称', desc: '主观沉浸，代入感强' },
  { value: 'third_limited', label: '第三人称有限', desc: '聚焦单一角色视角' },
  { value: 'third_omniscient', label: '第三人称全知', desc: '上帝视角，洞察一切' },
  { value: 'multi_perspective', label: '多视角交替', desc: '多个角色轮流讲述' },
]

const rhythmOptions = [
  { value: 'fast', label: '快节奏', desc: '动作/悬疑，每章2-3个情节点', icon: '⚡' },
  { value: 'medium', label: '中节奏', desc: '成长/探索，每章1个核心事件', icon: '🚶' },
  { value: 'slow', label: '慢节奏', desc: '心理/情感，氛围描写为主', icon: '🐢' },
]

const languageOptions = [
  { value: 'concise', label: '简洁硬汉', desc: '短句、动词驱动' },
  { value: 'flowery', label: '华丽古典', desc: '长句、修辞丰富' },
  { value: 'modern', label: '现代口语', desc: '对话主导、轻松幽默' },
  { value: 'stream_of_consciousness', label: '意识流', desc: '内心独白、时间跳跃' },
]

const toneOptions = [
  { value: 'epic_tragic', label: '史诗悲壮', color: 'red' },
  { value: 'light_hearted', label: '轻松明快', color: 'green' },
  { value: 'dark_oppressive', label: '黑暗压抑', color: 'gray' },
  { value: 'warm_healing', label: '温暖治愈', color: 'orange' },
  { value: 'mixed', label: '混合风格', color: 'purple' },
]

const depthOptions = [
  { value: 'pure_entertainment', label: '纯娱乐', desc: '爆米花爽文，轻松阅读' },
  { value: 'social_metaphor', label: '社会隐喻', desc: '借古讽今，引人深思' },
  { value: 'philosophical', label: '哲学探索', desc: '存在主义/人性本质' },
]

export default function StylePanel() {
  const { currentNovel, currentSetting, saveStyleSettings, loading } = useStore()
  const [form] = Form.useForm<StyleSettings>()
  const [preset, setPreset] = useState<string>('')
  const [analyzeText, setAnalyzeText] = useState<string>('')
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [styleResult, setStyleResult] = useState<any>(null)
  const [messageApi, contextHolder] = message.useMessage()

  useEffect(() => {
    if (currentSetting?.style_settings) {
      form.setFieldsValue(currentSetting.style_settings)
    }
  }, [currentSetting, form])

  const applyPreset = (presetName: string) => {
    setPreset(presetName)
    switch (presetName) {
      case 'xiaxia':
        form.setFieldsValue({
          narrative_perspective: 'third_limited',
          narrative_rhythm: 'fast',
          language_style: 'concise',
          emotional_tone: 'light_hearted',
          theme_depth: 'pure_entertainment',
        })
        break
      case 'xuxian':
        form.setFieldsValue({
          narrative_perspective: 'third_limited',
          narrative_rhythm: 'medium',
          language_style: 'flowery',
          emotional_tone: 'mixed',
          theme_depth: 'social_metaphor',
        })
        break
      case 'dushi':
        form.setFieldsValue({
          narrative_perspective: 'third_omniscient',
          narrative_rhythm: 'slow',
          language_style: 'modern',
          emotional_tone: 'warm_healing',
          theme_depth: 'philosophical',
        })
        break
      case 'mingchao':
        form.setFieldsValue({
          narrative_perspective: 'third_limited',
          narrative_rhythm: 'medium',
          language_style: 'flowery',
          emotional_tone: 'mixed',
          theme_depth: 'social_metaphor',
        })
        break
      default:
        break
    }
  }

  const handleSave = async () => {
    if (!currentNovel) {
      messageApi.error('请先选择小说')
      return
    }
    try {
      const values = form.validateFields()
      await saveStyleSettings(currentNovel.novel_id, await values)
      messageApi.success('风格设置保存成功')
    } catch (err) {
      messageApi.error('保存失败')
    }
  }

  const handleAnalyzeStyle = async () => {
    if (!analyzeText || analyzeText.length < 100) {
      messageApi.warning('请输入至少100字的参考文本')
      return
    }
    setAnalyzing(true)
    try {
      const response = await fetch('/api/v1/style/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: analyzeText })
      })
      const result = await response.json()
      setStyleResult(result)
      messageApi.success('文风分析完成')
    } catch (err) {
      messageApi.error('分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <App>
    {contextHolder}
    <Form form={form} layout="vertical">
    <div className="style-panel">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8, fontSize: 20, fontWeight: 600, color: '#2c1810' }}>
          🎨 风格差异化策略
        </h2>
        <p style={{ color: '#8b7355', fontSize: 14 }}>
          选择作品的叙事风格，打造独特的阅读体验
        </p>
      </div>

      <Card title="📚 预设风格" className="style-card" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Button
              block
              type={preset === 'xiaxia' ? 'primary' : 'default'}
              onClick={() => applyPreset('xiaxia')}
              style={{
                background: preset === 'xiaxia' ? '#c04040' : undefined,
                borderColor: '#d4c5b2',
              }}
            >
              <div style={{ fontWeight: 600 }}>🍅 番茄模式</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>快节奏爽文</div>
            </Button>
          </Col>
          <Col span={6}>
            <Button
              block
              type={preset === 'xuxian' ? 'primary' : 'default'}
              onClick={() => applyPreset('xuxian')}
              style={{
                background: preset === 'xuxian' ? '#c04040' : undefined,
                borderColor: '#d4c5b2',
              }}
            >
              <div style={{ fontWeight: 600 }}>🧝 修仙模式</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>古典仙侠</div>
            </Button>
          </Col>
          <Col span={6}>
            <Button
              block
              type={preset === 'dushi' ? 'primary' : 'default'}
              onClick={() => applyPreset('dushi')}
              style={{
                background: preset === 'dushi' ? '#c04040' : undefined,
                borderColor: '#d4c5b2',
              }}
            >
              <div style={{ fontWeight: 600 }}>🏙️ 都市模式</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>现实情感</div>
            </Button>
          </Col>
          <Col span={6}>
            <Button
              block
              type={preset === 'mingchao' ? 'primary' : 'default'}
              onClick={() => applyPreset('mingchao')}
              style={{
                background: preset === 'mingchao' ? '#c04040' : undefined,
                borderColor: '#d4c5b2',
              }}
            >
              <div style={{ fontWeight: 600 }}>🏯 明朝模式</div>
              <div style={{ fontSize: 12, opacity: 0.8 }}>历史爱情</div>
            </Button>
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        <Col span={12}>
          <Card
            title={
              <span>
                <EyeOutlined style={{ marginRight: 8, color: '#c04040' }} />
                叙事视角
              </span>
            }
            className="style-card"
          >
            <Form.Item name="narrative_perspective">
              <Radio.Group style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {perspectiveOptions.map(opt => (
                  <Radio key={opt.value} value={opt.value}>
                    <span style={{ fontWeight: 500 }}>{opt.label}</span>
                    <span style={{ color: '#8b7355', marginLeft: 8 }}>- {opt.desc}</span>
                  </Radio>
                ))}
              </Radio.Group>
            </Form.Item>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <span>
                <ApiOutlined style={{ marginRight: 8, color: '#c04040' }} />
                叙事节奏
              </span>
            }
            className="style-card"
          >
            <Form.Item name="narrative_rhythm">
              <Radio.Group style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {rhythmOptions.map(opt => (
                  <Radio key={opt.value} value={opt.value}>
                    <span>{opt.icon}</span>
                    <span style={{ fontWeight: 500, marginLeft: 8 }}>{opt.label}</span>
                    <span style={{ color: '#8b7355', marginLeft: 8 }}>- {opt.desc}</span>
                  </Radio>
                ))}
              </Radio.Group>
            </Form.Item>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card
            title={
              <span>
                <AlertOutlined style={{ marginRight: 8, color: '#c04040' }} />
                语言风格
              </span>
            }
            className="style-card"
          >
            <Form.Item name="language_style">
              <Radio.Group style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {languageOptions.map(opt => (
                  <Radio key={opt.value} value={opt.value}>
                    <span style={{ fontWeight: 500 }}>{opt.label}</span>
                    <span style={{ color: '#8b7355', marginLeft: 8 }}>- {opt.desc}</span>
                  </Radio>
                ))}
              </Radio.Group>
            </Form.Item>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <span>
                <HeartOutlined style={{ marginRight: 8, color: '#c04040' }} />
                情感基调
              </span>
            }
            className="style-card"
          >
            <Form.Item name="emotional_tone">
              <Radio.Group style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {toneOptions.map(opt => (
                  <Radio key={opt.value} value={opt.value}>
                    <Tag color={opt.color}>{opt.label}</Tag>
                  </Radio>
                ))}
              </Radio.Group>
            </Form.Item>
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <span>
            <BookOutlined style={{ marginRight: 8, color: '#c04040' }} />
            主题深度
          </span>
        }
        className="style-card"
        style={{ marginTop: 16 }}
      >
        <Form.Item name="theme_depth">
          <Radio.Group style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {depthOptions.map(opt => (
              <Radio key={opt.value} value={opt.value}>
                <span style={{ fontWeight: 500 }}>{opt.label}</span>
                <span style={{ color: '#8b7355', marginLeft: 8 }}>- {opt.desc}</span>
              </Radio>
            ))}
          </Radio.Group>
        </Form.Item>
      </Card>

      <Divider />

      <Card
        title={
          <span>
            <SearchOutlined style={{ marginRight: 8, color: '#c04040' }} />
            文风分析
          </span>
        }
        className="style-card"
        style={{ marginTop: 16 }}
      >
        <p style={{ color: '#8b7355', marginBottom: 12 }}>
          粘贴参考文本，AI将分析其文风特征并生成风格指南
        </p>
        <TextArea
          rows={6}
          placeholder="粘贴您喜欢的小说片段（至少100字），AI将分析其句式、节奏、用词等文风特征..."
          value={analyzeText}
          onChange={(e) => setAnalyzeText(e.target.value)}
          style={{ borderColor: '#d4c5b2', marginBottom: 12 }}
        />
        <Button
          type="default"
          icon={<SearchOutlined />}
          onClick={handleAnalyzeStyle}
          loading={analyzing}
          style={{ borderColor: '#c04040', color: '#c04040' }}
        >
          🔍 分析文风
        </Button>
        
        {styleResult && (
          <div style={{ marginTop: 16, padding: 12, background: '#faf7f0', borderRadius: 4 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>分析结果</div>
            {styleResult.style_tags && (
              <div style={{ marginBottom: 8 }}>
                <span style={{ color: '#8b7355' }}>风格标签：</span>
                {styleResult.style_tags.map((tag: string) => (
                  <Tag key={tag} color="blue" style={{ marginRight: 4 }}>{tag}</Tag>
                ))}
              </div>
            )}
            {styleResult.sentence_length && (
              <div style={{ fontSize: 12, color: '#6b5c4a' }}>
                <div>平均句长：{styleResult.sentence_length.avg}字</div>
                <div>短句比例：{(styleResult.sentence_length.short_ratio * 100).toFixed(1)}%</div>
              </div>
            )}
            {styleResult.llm_style_guide && (
              <pre style={{ fontSize: 11, color: '#6b5c4a', whiteSpace: 'pre-wrap', marginTop: 8 }}>
                {styleResult.llm_style_guide}
              </pre>
            )}
          </div>
        )}
      </Card>

      <Divider />

      <Row justify="center">
        <Button
          type="primary"
          size="large"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={loading}
          style={{ background: '#c04040', borderColor: '#c04040' }}
        >
          💾 保存风格设置
        </Button>
      </Row>
    </div>
    </Form>
    </App>
  )
}
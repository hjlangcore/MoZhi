import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Row, Col, Divider, Tag, message, Space, App } from 'antd'
import { GlobalOutlined, HistoryOutlined, UserOutlined, AimOutlined, ShakeOutlined, SaveOutlined } from '@ant-design/icons'
import { useStore } from '../store'
import type { WorldView } from '../store'

const { TextArea } = Input

export default function WorldBuildingPanel() {
  const { currentNovel, currentSetting, saveWorldView, generateWorldView, loading } = useStore()
  const [form] = Form.useForm<WorldView>()
  const [isGenerating, setIsGenerating] = useState(false)
  const [messageApi, contextHolder] = message.useMessage()

  useEffect(() => {
    if (currentSetting?.world_view) {
      form.setFieldsValue(currentSetting.world_view)
    }
  }, [currentSetting, form])

  const handleGenerate = async () => {
    setIsGenerating(true)
    const prompt = '创建一个明朝背景的爱情小说世界观，包含官场斗争、家族恩怨、江湖恩怨等元素'
    const worldView = await generateWorldView(prompt)
    if (worldView) {
      form.setFieldsValue(worldView)
      messageApi.success('AI生成世界观成功')
    } else {
      messageApi.error('生成失败，请重试')
    }
    setIsGenerating(false)
  }

  const handleSave = async () => {
    if (!currentNovel) {
      messageApi.error('请先选择小说')
      return
    }
    try {
      const values = form.validateFields()
      await saveWorldView(currentNovel.novel_id, await values)
      messageApi.success('世界观保存成功')
    } catch (err) {
      messageApi.error('保存失败')
    }
  }

  return (
    <App>
    {contextHolder}
    <Form form={form} layout="vertical">
    <div className="world-building-panel">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8, fontSize: 20, fontWeight: 600, color: '#2c1810' }}>
          🏯 世界观构建体系
        </h2>
        <p style={{ color: '#8b7355', fontSize: 14 }}>
          按照五要素框架构建您的小说世界观
        </p>
      </div>

      <Row gutter={16}>
        <Col span={12}>
          <Card
            title={
              <span>
                <GlobalOutlined style={{ marginRight: 8, color: '#c04040' }} />
                核心主题
              </span>
            }
            className="world-card"
          >
            <Form.Item
              name="core_theme"
              rules={[{ required: true, message: '请输入核心主题' }]}
            >
              <TextArea
                rows={3}
                placeholder="例如：权力腐蚀下的人性坚守…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Tag color="orange">一句话概括您想表达的哲学/思想</Tag>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <span>
                <HistoryOutlined style={{ marginRight: 8, color: '#c04040' }} />
                历史脉络
              </span>
            }
            className="world-card"
          >
            <Form.Item name={['historical_events', 0]}>
              <TextArea
                rows={3}
                placeholder="创世/起源事件…"
                style={{ borderColor: '#d4c5b2', marginBottom: 8 }}
              />
            </Form.Item>
            <Form.Item name={['historical_events', 1]}>
              <TextArea
                rows={3}
                placeholder="黄金时代…"
                style={{ borderColor: '#d4c5b2', marginBottom: 8 }}
              />
            </Form.Item>
            <Form.Item name={['historical_events', 2]}>
              <TextArea
                rows={3}
                placeholder="转折点/灾难…"
                style={{ borderColor: '#d4c5b2', marginBottom: 8 }}
              />
            </Form.Item>
            <Form.Item name={['historical_events', 3]}>
              <TextArea
                rows={3}
                placeholder="当前局势…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Tag color="blue">3-5个关键历史节点</Tag>
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card
            title={
              <span>
                <UserOutlined style={{ marginRight: 8, color: '#c04040' }} />
                社会结构
              </span>
            }
            className="world-card"
          >
            <Form.Item
              name={['social_structure', 'dominant_forces']}
              label="主导势力"
              style={{ marginBottom: 12 }}
            >
              <Input
                placeholder="例如：皇权、宦官、东林党…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Form.Item
              name={['social_structure', 'class_divisions']}
              label="阶层划分"
              style={{ marginBottom: 12 }}
            >
              <Input
                placeholder="例如：士农工商、官绅平民…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Form.Item
              name={['social_structure', 'core_conflicts']}
              label="核心冲突"
            >
              <TextArea
                rows={2}
                placeholder="例如：党争、贫富差距、新旧思想碰撞…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <span>
                <AimOutlined style={{ marginRight: 8, color: '#c04040' }} />
                地理生态
              </span>
            }
            className="world-card"
          >
            <Form.Item
              name={['geography', 'major_regions']}
              label="主要区域"
              style={{ marginBottom: 12 }}
            >
              <Input
                placeholder="例如：京城、江南、西北边疆…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Form.Item
              name={['geography', 'power_distribution']}
              label="势力分布"
              style={{ marginBottom: 12 }}
            >
              <Input
                placeholder="例如：东厂掌控京城、锦衣卫遍布天下…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Form.Item
              name={['geography', 'key_locations']}
              label="关键地点"
            >
              <TextArea
                rows={2}
                placeholder="例如：紫禁城、江南织造府、雁门关…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <span>
            <AimOutlined style={{ marginRight: 8, color: '#c04040' }} />
            物理规则
          </span>
        }
        className="world-card"
        style={{ marginTop: 16 }}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name={['physics_rules', 'power_system']} label="力量体系">
              <TextArea
                rows={4}
                placeholder="例如：武道、内功、奇门遁甲、医术…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name={['physics_rules', 'limitations']} label="限制条件">
              <TextArea
                rows={4}
                placeholder="例如：修炼需要天资、内力有瓶颈…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name={['physics_rules', 'cost_mechanism']} label="代价机制">
              <TextArea
                rows={4}
                placeholder="例如：修炼伤元气、使用禁术折寿…"
                style={{ borderColor: '#d4c5b2' }}
              />
            </Form.Item>
          </Col>
        </Row>
      </Card>

      <Divider />

      <Row justify="center" gutter={16}>
        <Button
          type="default"
          size="large"
          icon={<ShakeOutlined />}
          onClick={handleGenerate}
          loading={isGenerating || loading}
          style={{ borderColor: '#c04040', color: '#c04040' }}
        >
          ✨ AI 自动生成
        </Button>
        <Button
          type="primary"
          size="large"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={loading}
          style={{ background: '#c04040', borderColor: '#c04040' }}
        >
          💾 保存世界观
        </Button>
      </Row>
    </div>
    </Form>
    </App>
  )
}
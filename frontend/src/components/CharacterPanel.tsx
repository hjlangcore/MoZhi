import { useState } from 'react'
import { Card, Form, Input, Button, Row, Col, Divider, Tag, Select, message, Avatar, List, App } from 'antd'
import { UserOutlined, HeartOutlined, BankOutlined, WarningOutlined, ShakeOutlined, SaveOutlined, PlusOutlined } from '@ant-design/icons'
import { useStore } from '../store'
import type { Character } from '../store'

const { TextArea } = Input

const roleOptions = [
  { value: 'protagonist', label: '👑 核心主角' },
  { value: 'mentor', label: '🧙 导师' },
  { value: 'rival', label: '⚔️ 对手' },
  { value: 'love_interest', label: '💕 爱人' },
  { value: 'antagonist', label: '😈 反派' },
  { value: 'ally', label: '🤝 盟友' },
  { value: 'family', label: '👨‍👩‍👧 亲人' },
]

export default function CharacterPanel() {
  const { currentNovel, currentSetting, saveCharacter, generateCharacter, loading } = useStore()
  const [form] = Form.useForm<Character>()
  const [isMain, setIsMain] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedRole, setSelectedRole] = useState('protagonist')
  const [messageApi, contextHolder] = message.useMessage()

  const handleGenerate = async () => {
    if (!currentSetting?.world_view) {
      messageApi.error('请先构建世界观')
      return
    }
    setIsGenerating(true)
    const character = await generateCharacter(currentSetting.world_view, selectedRole)
    if (character) {
      form.setFieldsValue(character)
      messageApi.success('AI生成角色成功')
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
      const character = await values
      character.role_type = selectedRole as Character['role_type']
      await saveCharacter(currentNovel.novel_id, character, isMain)
      messageApi.success(isMain ? '主角保存成功' : '配角保存成功')
    } catch (err) {
      messageApi.error('保存失败')
    }
  }

  const handleReset = () => {
    form.resetFields()
  }

  const roleColors: Record<string, string> = {
    protagonist: 'red',
    mentor: 'purple',
    rival: 'orange',
    love_interest: 'pink',
    antagonist: 'red',
    ally: 'green',
    family: 'blue',
  }

  return (
    <App>
    {contextHolder}
    <Form form={form} layout="vertical">
    <div className="character-panel">
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 8, fontSize: 20, fontWeight: 600, color: '#2c1810' }}>
          🎭 角色矩阵设计
        </h2>
        <p style={{ color: '#8b7355', fontSize: 14 }}>
          设计立体鲜活的人物角色，构建完整的角色关系网络
        </p>
      </div>

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Select
            value={selectedRole}
            onChange={setSelectedRole}
            style={{ width: '100%' }}
            options={roleOptions}
            size="large"
          />
        </Col>
        <Col span={8}>
          <Select
            value={isMain}
            onChange={setIsMain}
            style={{ width: '100%' }}
            options={[
              { value: true, label: '设为主角' },
              { value: false, label: '设为配角' },
            ]}
            size="large"
          />
        </Col>
      </Row>

      <Card className="character-card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
          <Avatar size={80} icon={<UserOutlined />} style={{ backgroundColor: '#c04040', marginRight: 20 }} />
          <div>
            <Form.Item
              name="name"
              rules={[{ required: true, message: '请输入角色姓名' }]}
              style={{ marginBottom: 8 }}
            >
              <Input
                size="large"
                placeholder="角色姓名"
                style={{ width: 200, borderColor: '#d4c5b2' }}
              />
            </Form.Item>
            <Row gutter={16}>
              <Form.Item name="age">
                <Input type="number" placeholder="年龄" style={{ width: 80, borderColor: '#d4c5b2' }} />
              </Form.Item>
              <Form.Item name="gender">
                <Select placeholder="性别" style={{ width: 100, borderColor: '#d4c5b2' }}>
                  <Select.Option value="男">男</Select.Option>
                  <Select.Option value="女">女</Select.Option>
                </Select>
              </Form.Item>
            </Row>
          </div>
        </div>

        <Divider />

        <Form.Item name="social_identity" label="社会身份" style={{ marginBottom: 12 }}>
          <Input placeholder="例如：锦衣卫千户、江南富商、书香门第…" style={{ borderColor: '#d4c5b2' }} />
        </Form.Item>
        <Form.Item name="nickname" label="外号/称号">
          <Input placeholder="例如：玉面修罗、江南第一才子…" style={{ borderColor: '#d4c5b2' }} />
        </Form.Item>
      </Card>

      <Row gutter={16}>
        <Col span={12}>
          <Card
            title={
              <span>
                <HeartOutlined style={{ marginRight: 8, color: '#c04040' }} />
                核心矛盾
              </span>
            }
            className="character-card"
          >
            <Form.Item name="wants" label="想要" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="角色表面想要什么…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="needs" label="需要" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="角色真正需要什么…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="fears" label="害怕" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="角色内心最害怕的事…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="weakness" label="弱点">
              <TextArea rows={2} placeholder="角色的致命弱点…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title={
              <span>
                <BankOutlined style={{ marginRight: 8, color: '#c04040' }} />
                外在表现
              </span>
            }
            className="character-card"
          >
            <Form.Item name="speech_style" label="说话方式" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="例如：沉稳内敛、言辞犀利…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="habits" label="行为习惯" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="例如：喜欢把玩玉佩、思考时皱眉…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="skills" label="特殊技能" style={{ marginBottom: 12 }}>
              <TextArea rows={2} placeholder="例如：武功高强、精通医术、过目不忘…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
            <Form.Item name="fatal_flaw" label="致命缺陷">
              <TextArea rows={2} placeholder="例如：过于骄傲、轻信他人…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <span>
            <WarningOutlined style={{ marginRight: 8, color: '#c04040' }} />
            成长弧线
          </span>
        }
        className="character-card"
        style={{ marginTop: 16 }}
      >
        <Row gutter={16}>
          <Col span={6}>
            <Form.Item name="arc_start" label="起始状态">
              <TextArea rows={3} placeholder="故事开始时的状态…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="trigger_event" label="触发事件">
              <TextArea rows={3} placeholder="改变命运的关键事件…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="midpoint_change" label="中点转变">
              <TextArea rows={3} placeholder="故事中段的重大转变…" style={{ borderColor: '#d4c5b2' }} />
            </Form.Item>
          </Col>
          <Col span={6}>
            <Form.Item name="final_form" label="最终形态">
              <TextArea rows={3} placeholder="故事结束时的样子…" style={{ borderColor: '#d4c5b2' }} />
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
          ✨ AI 生成角色
        </Button>
        <Button
          type="default"
          size="large"
          icon={<PlusOutlined />}
          onClick={handleReset}
        >
          🔄 重新开始
        </Button>
        <Button
          type="primary"
          size="large"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={loading}
          style={{ background: '#c04040', borderColor: '#c04040' }}
        >
          💾 保存角色
        </Button>
      </Row>

      {currentSetting?.supporting_characters && currentSetting.supporting_characters.length > 0 && (
        <>
          <Divider />
          <Card title="已创建的配角">
            <List
              grid={{ gutter: 16, column: 4 }}
              dataSource={currentSetting.supporting_characters}
              renderItem={(item) => (
                <List.Item key={item.name}>
                  <Card hoverable>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                      <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#d4c5b2', marginRight: 8 }} />
                      <div>
                        <div style={{ fontWeight: 600 }}>{item.name}</div>
                        <Tag color={roleColors[item.role_type]}>
                          {roleOptions.find(r => r.value === item.role_type)?.label}
                        </Tag>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: '#8b7355' }}>{item.social_identity}</div>
                  </Card>
                </List.Item>
              )}
            />
          </Card>
        </>
      )}
    </div>
    </Form>
    </App>
  )
}
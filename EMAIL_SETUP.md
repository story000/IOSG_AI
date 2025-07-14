# 📧 邮件功能配置指南

为了使用自动化报告功能，您需要配置邮件发送服务。

## Gmail 配置 (推荐)

### 1. 开启两步验证
在您的Google账户中开启两步验证。

### 2. 生成应用密码
1. 访问 [Google账户设置](https://myaccount.google.com/security)
2. 在"登录Google"部分，点击"应用密码"
3. 选择"邮件"和设备类型
4. 生成16位应用密码

### 3. 配置环境变量

#### 方法1: 使用.env文件
复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-digit-app-password
```

#### 方法2: 直接在代码中配置
编辑 `app.py` 第36-37行：
```python
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-16-digit-app-password'
```

## 其他邮件服务商

### Outlook/Hotmail
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

### 163邮箱
```env
MAIL_SERVER=smtp.163.com
MAIL_PORT=587
MAIL_USERNAME=your-email@163.com
MAIL_PASSWORD=your-password
```

### QQ邮箱
```env
MAIL_SERVER=smtp.qq.com
MAIL_PORT=587
MAIL_USERNAME=your-email@qq.com
MAIL_PASSWORD=your-authorization-code
```

## 测试邮件配置

启动应用后，您可以：
1. 访问 `http://localhost:8080/auto`
2. 输入您的邮箱地址
3. 点击"开始生成报告"进行测试

## 常见问题

### Q: 邮件发送失败？
A: 检查以下配置：
- Gmail需要使用应用密码，不是登录密码
- 确保开启了两步验证
- 检查邮箱用户名和密码是否正确

### Q: 如何查看发送状态？
A: 检查运行app.py的终端，会显示邮件发送的成功/失败信息

### Q: 收不到邮件？
A: 
- 检查垃圾邮件文件夹
- 确认邮箱地址拼写正确
- 等待几分钟，邮件可能有延迟

## 安全提示

- 不要在代码中硬编码密码
- 使用应用密码而不是主密码
- 定期更换应用密码
- 不要将包含密码的.env文件提交到版本控制
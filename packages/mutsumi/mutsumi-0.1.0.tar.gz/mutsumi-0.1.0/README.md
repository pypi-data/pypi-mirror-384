🥒Mutsumi🥒
===

一个基于 openai SDK 的 AI 助手开发框架。

---

# 使用方法

---

# 配置

项目的所有配置文件位于`cfg`下，如不存在该目录，则需手动创建。

## API key

位于 `cfg/key` 中。

文件内容示例：

```
sk-7167**************************ce
```

## Email 账户
位于 `email.json` 中

文件内容示例：
```json
{
    "host": "smtp.xxx.com",
    "addr": "email_address@xxx.com",
    "name": "your_nick_name",
    "key": "password",
}
```

## Email 地址本
位于 `email_book.json` 中

文件内容示例：
```json
{
    "Li Hua":"lihua@mail.com",
    "Zhang San":"zs@mail.com"
}
```

---

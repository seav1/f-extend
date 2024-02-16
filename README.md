# Freenom 域名续费 by Github Action
* 改自 LinxiPush 林夕脚本，[LinxiPush 林夕脚本](https://github.com/linxi-520/LinxiPush)
* `Freenom域名续费`，用于`Freenom`的域名（.tk、.gq 等）自动续期，支持`AWS-WAF验证`Token

## 使用方法
* 请设置为私库
* action secret 设置的环境变量
  | 变量名        | 是否必须  | 说明 |
  | ------------ | ------   | ---- |
  | FREENOM_USERNAME  | 是 | 账户邮箱，多个账户请使用空格隔开 |
  | FREENOM_PASSWORD  | 是 | 账户密码，多个账户请使用空格隔开，与FREENOM_USERNAME数量相同 |
  | TG_BOT_TOKEN      | 否 | Telegram bot token |
  | TG_USER_ID        | 否 | Telegram user ID  |

## 注意提醒:
本仓库脚本仅用于交流学习，请下载后24之内自行删除

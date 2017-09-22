
class PlayerManager:

    @staticmethod
    def add_display():
        return {
            "fields": [
                {
                    "type": "text",
                    "label": u"玩家账号",
                    "help_id": "player_account_help",
                    "help_text": u"玩家登录账号，由字母和数字组成，唯一",
                    "name": "account",
                    "id": "_account",
                    "placeholder": "account1"
                },
                {
                    "type": "text",
                    "label": u"姓名",
                    "name": "username",
                    "id": "_username"
                },
                {
                    "type": "text",
                    "label": u"联系方式",
                    "name": "mobile",
                    "id": "_mobile"
                },
                {
                    "type": "text",
                    "label": u"QQ号码",
                    "name": "qq",
                    "id": "_qq"
                },
                {
                    "type": "button",
                    "button_type": "submit",
                    "label": u"提交"
                }
            ]
        }

    @staticmethod
    def add():
        pass
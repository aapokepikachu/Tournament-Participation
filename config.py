import os

TOKEN = os.getenv("BOT_TOKEN")
GROUP_A_ID = int(os.getenv("GROUP_A_ID", "-1001234567890"))
GROUP_P_ID = int(os.getenv("GROUP_P_ID", "-1009876543210"))
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "111111111,222222222").split(",")))

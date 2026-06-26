import os

# ==================== CONFIGURATION ====================
# 1. Path to your CSV student database
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "dataset/2025.csv")

# 2. Google Form URL
FORM_URL = os.getenv("FORM_URL", "https://docs.google.com/forms/d/e/1FAIpQLSf7Ru04vJTdsVA8QkimGY8sGy2olumHWhL0pPm7cr46eHPELA/viewform")

# 3. GPT AI API URL
AI_API_URL = os.getenv("AI_API_URL", "https://apis.prexzyvilla.site/ai/gpt-5")

# 4. Target number of questionnaire submissions
TARGET_SUBMISSIONS = int(os.getenv("TARGET_SUBMISSIONS", 5))

# 5. Delay between submissions in seconds (min/max range)
SUBMISSION_DELAY_MIN = int(os.getenv("SUBMISSION_DELAY_MIN", 3))
SUBMISSION_DELAY_MAX = int(os.getenv("SUBMISSION_DELAY_MAX", 7))
# =======================================================

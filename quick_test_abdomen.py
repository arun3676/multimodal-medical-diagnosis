import os, shutil
from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
src='00009232_004.png'
test='test-abdomen-xray.jpg'
if not os.path.exists(src):
    print('source image not found')
    exit()
shutil.copy(src,test)
print('copied',test)
ana=GeminiImageAnalyzer()
res=ana.analyze_medical_image(test,'chest_xray')
print('error:', res.get('error'))
print('message:', res.get('error_message'))
print('detected:', res.get('detected_type'))
print('requested:', res.get('requested_type'))
os.remove(test)

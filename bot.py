import os, json, time, threading
from flask import Flask
import urllib.request, urllib.parse

TOKEN="8808108179:AAEAm9ojlgS2HAhZNS3J8QdEp5zk70mFk5Q"
app=Flask(__name__)
@app.route('/')
def home(): return "BOT V8 ONLINE 24/24 - PRONO BOX"

def send(c,t,k=None):
 d={"chat_id":c,"text":t,"parse_mode":"Markdown"}
 if k: d["reply_markup"]=json.dumps(k)
 try:
  req=urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage",data=urllib.parse.urlencode(d).encode())
  urllib.request.urlopen(req,timeout=10)
 except: pass

def kb():
 return {"inline_keyboard":[[{"text":"💰 MONTANTE DU JOUR","callback_data":"m"}],[{"text":"🔥 TOP 3 SAFE","callback_data":"t"}],[{"text":"🏆 LDC CE SOIR","callback_data":"l"}]]}

def loop():
 try: urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True",timeout=5)
 except: pass
 off=0
 print("BOT V8 LANCE")
 while True:
  try:
   with urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={off}&timeout=30",timeout=35) as r:
    for u in json.loads(r.read().decode()).get("result",[]):
     off=u["update_id"]+1
     if "message" in u:
      ch=u["message"]["chat"]["id"]
      send(ch,"*🔥 PRONO BOX V8 24H/24* 🇨🇲\n\nBot en ligne H24!\nCote potion 1.45",kb())
     if "callback_query" in u:
      ch=u["callback_query"]["message"]["chat"]["id"]
      send(ch,"✅ *MONTANTE 10/09*\n\nPSG vs Atalanta - 1X+Over 1.5 @1.45\nBarca vs Newcastle - 1X+Over 1.5 @1.43\nCombo @1.45",kb())
  except Exception as e:
   print(e); time.sleep(5)

threading.Thread(target=loop,daemon=True).start()
if __name__=="__main__": app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))

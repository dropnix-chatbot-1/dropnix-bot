import os,datetime,json,io,csv 
from groq import Groq 
from dotenv import load_dotenv 
from flask import Flask, request, jsonify 
import requests

load_dotenv()
app = Flask(__name__)

SHEET_ID = "1ZCjMzADQm4cRKq1IFkpukfxX-uP-fSL66xHWwhhEyIQ"
MEMORY_FILE = "MEMORY.JSON"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq( api_key =GROQ_API_KEY)if GROQ_API_KEY else None 
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN","dropnix123")
def get_prompt_from_sheet():
    return """ tu Dropnix.ai company ka salesbot hai tuje costumre ko hamare poductke detail bataine hai
        product---
        offer no.1 1500₹/month 24/7 chatbot 
        offer no.2 3000₹/month facebook ads
        offer no.3 3000₹/month 24/7 call uthane wala recepnisest 
        best offer 8000₹/month fcebook and insta ads + offer no.3 + per day 5-8 costumer paka
        
        rula---
        1.jab customer ko ya batao to apne taraf se ore open or simple kar ke batana 
        2.phehle costumer ke welcome karo aise"hey sir welcome to the all india cosmatic family \n yaha ham all india ke sabhi cosmatic shops ko grow karne unke customer na aine ke problem ko solve karte hai ham ne ab tak 200+ shop ke saath kaam kiye hai ore wo shops hamare saath 2 saal se laga taar kam kar rahi hai \n WHAT CAN I HELP YOU SIR 
        3.rule no.2 ko apne taraf se thoda chota kar daina
        """

def get_bot_reply(user_mes,costumer_number = "default"):
    base_prompt = get_prompt_from_sheet()
    system_mes = {"role":"system","content":base_prompt}

    chat_history = []
    if os.path.exists(MEMORY_FILE) and os.path.getsize(MEMORY_FILE)>0 :
        try:
            with open(MEMORY_FILE,'r',encoding="utf-8")as f:
                chat_history = json.load(f)
        except:
            chat_history = []

    history_msg = []
    for chat in chat_history :
        if chat.get("number")== costumer_number or costumer_number =="default":
            if "user" in chat and "agent" in chat :
                history_msg.append({"role":"user","content":str(chat["user"])})  
                history_msg.append({"role":"assistant","content":str(chat["agent"])})

    to_send = [system_mes] + history_msg[-10:]
    to_send.append({"role":"user","content": user_mes})

    response = client.chat.completions.create(
        model = "openai/gpt-oss-20b",
        temperature =0,
        messages=to_send
    )
    
    reply = response.choices[0].message.content

    chat_history.append({
        "time": datetime.datetime.now().strftime("%d-%m-%y %H:%M:%S"),
        "user": user_mes,
        "agent": reply,
        "number": costumer_number
    })

    with open(MEMORY_FILE,'w',encoding = 'utf-8')as f:
        json.dump(chat_history,f,indent=4,ensure_ascii=False)

    return reply
@app.route("/",methods=["GET"])
def home():
    if request.args.get("hub.verify_token")==VERIFY_TOKEN:
        return request.args.get("hub.challenge"),200
    return "bot is live"

@app.route("/webhook",methods=["GET"])
def verify():
    if request.args.get("hub.verify_token")== VERIFY_TOKEN:
        return request.args.get("hub.challenge"),200
    return "verification failed",403

@app.route("/webhook",methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        value = data['entry'][0]['changes'][0]['value']
        if 'messages'not in value:
            return "OK",200
        
        msg_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
        from_number = msg_obj['from']
        user_text = msg_obj['text']['body']
        bot_reply = get_bot_reply(user_text,from_number)

        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization":f"Bearer {WHATSAPP_TOKEN}","Content-Type":"application/json"}
        payload = {"messaging_product":"whatsapp","to":from_number,"type":"text","text":{"body":bot_reply}}
        requests.post(url,headers=headers,json=payload)
    except Exception as e:
        print(f"Webhook error:{e}")
    return "OK",200

@app.route("/chat",methods=["POST"])
def chat_api():
    data = request.get_json()
    user_msg = data.get("message","")
    number = data.get("number","default")
    if not user_msg :
        return jsonify({"error":"massege nahi mila"}),400
    bot_reply = get_bot_reply(user_msg,number)
    print(f"{number}:{user_msg}--> {bot_reply}")  
    return jsonify({"reply":bot_reply})


if __name__== "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)

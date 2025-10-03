# TeleCare AI Concierge

**Smart, Emotion-Aware Telecom Assistant**  

---

## **Project Description**
TeleCare AI Concierge is a next-generation customer service assistant for telecom providers.  
It combines AI, sentiment analysis, and hyper-personalization to provide **empathetic, proactive, and smart support**.  

Instead of traditional reactive customer service, this prototype detects customer emotions, usage patterns, billing anomalies, or travel plans and suggests solutions automatically.  

---

## **Features**
- **AI Chat**: Understands natural language input.  
- **Emotion Awareness**: Adjusts responses based on user sentiment.  
- **Proactive Suggestions**: Temporary speed boosts, billing checks, roaming packages.  
- **Quick Actions**: One-click resolution options.  
- **Human Escalation**: Automatically creates tickets for human agents.  
- **Voice + TTS**: Optional microphone input and text-to-speech output.  

---

## **Demo Instructions**
1. Select a customer profile: Maria, Ahmed, or Jana.  
2. Toggle profile conditions in the sidebar (usage spike, billing anomaly, traveling).  
3. Example chat messages:  
   - `"My internet is slow"` → Suggests temporary speed boost.  
   - `"Why is my bill higher?"` → Detects billing anomaly.  
   - `"I’m traveling to Spain"` → Suggests roaming package.  
4. Use **Quick Actions** (Enable boost, Transfer to human) to simulate task completion.  
5. Optionally, upload a WAV file to test voice transcription and TTS output.  
6. After “Transfer to human”, check `tickets.json` for saved tickets.  

---

## **Installation & Running**
1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/TeleCare_AI_Concierge.git
cd TeleCare_AI_Concierge
pip install -r requirements.txt
streamlit run telecare_app_v3.py

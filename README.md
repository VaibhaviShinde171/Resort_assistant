#  Resort AI Assistant

An AI-powered resort management assistant built using **Streamlit**, **LangChain**, **OpenAI**, and **Tavily Search**.

This app supports:
- Resort room booking  
-  Customer management  
-  Bill generation  
-  Voice + text chat  
-  Web search using *Tavily* for general questions  
-  Short recent chat view + full history sidebar  

---

## Features

- **AI Assistant** powered by `gpt-4o`
- **Voice input** using `streamlit-mic-recorder`
- **Web search** using `TavilySearch`
- **Agent-based tool calling** with LangChain
- **Background image UI with glass effects**
- **Collapsible chat history** like ChatGPT

---

##  Installation

### 1. Clone repository
```bash
git clone https://github.com/VaibhaviShinde171/Resort_assistant.git
cd <Resort_assistant>



2. Create virtual environment
python -m venv venv
venv/Scripts/activate   # Windows

3. Install dependencies
pip install -r requirements.txt

4.Environment Variables

Create a .env file:

OPENAI_API_KEY=your_api_key
TAVILY_API_KEY=your_api_key

5.Run the App
streamlit run app.py

6. Project Structure
.
├── app.py
├── agents.py
├── tools.py
├── assets/
│   └── my_image.jpg
├── .gitignore
├── requirements.txt
└── README.md
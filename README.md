# 🧳 WanderBot – Your Travel Companion

  <a name="overview"></a>

## 📖 Overview

**WanderBot** is an intelligent travel assistant powered by **Google Gemini**, with a FastAPI backend and a sleek **Streamlit interface**. Whether you're planning a trip, need visa advice, or are looking for local insights, WanderBot is here to help—**on both desktop and mobile browsers**.

This project features:

* Natural-language travel assistance
* Chat memory through Streamlit session state
* FastAPI backend handling Gemini API
* Fully responsive design for seamless use on your phone


## 📚 Table of Contents

* [Overview](#overview)
* [Project Structure](#project-structure)
* [Use Cases](#use-cases)
* [API & App Interface](#api-interface)
* [Imported Libraries](#imported-libraries)
* [Installation & Setup](#installation-setup)
* [Limitations](#limitations)
* [Future Improvements](#future-improvements)
* [Contributors](#contributors)
* [License](#license)

<a name="project-structure"></a>

## 🏗️ Project Structure

```text
travel_bot/
├── backend/
│   └── main.py
├── images/
│   └── Wander_bot_logo.png
├── app.py
├── requirements.txt
├── .env
├── styles.css
└── README.md
```

<a name="use-cases"></a>

## 🎯 Use Cases

* 🗺️ **Trip Planning** – Custom itineraries tailored to user preferences
* 🛂 **Visa Advice** – Entry and documentation help for various countries
* 🏨 **Accommodation Tips** – Advice on budget, luxury, or local stays
* 🧳 **Travel Prep** – Packing tips, budgeting, cultural insights
* 📱 **Mobile Assistant** – Use it easily on your phone browser!

<a name="api-interface"></a>

## 🌐 API & App Interface

### 🎯 FastAPI Backend

* `POST /chat`
* Input: `message` and optional chat `history`
* Output: Travel-related response from Gemini

### 💬 Streamlit Frontend

* Clean, minimal chat interface
* GitHub link and “Clear Conversation” button
* Mobile responsive (adjusts layout and fonts for smaller screens)


<a name="imported-libraries"></a>

## 📦 Imported Libraries

* `streamlit`, `PIL.Image`
* `requests`, `os`, `dotenv`
* `fastapi`, `pydantic`, `google.genai`
* `uvicorn`, `python-multipart`
* `fastapi.middleware.cors.CORSMiddleware`


<a name="installation-setup"></a>

## ⚙️ Installation & Setup

### 🔧 Clone and set up

```bash
git clone https://github.com/hameedaah/travel_bot.git
cd travel_bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### ▶️ Run the FastAPI Backend

```bash
uvicorn backend.main:app --reload
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) to test the API.

### 🚀 Run the Streamlit Frontend

```bash
streamlit run app.py
```

This will launch the app in your browser at [http://localhost:8501](http://localhost:8501).

✅ **Tip**: The app is fully responsive—try it on your phone browser too!



<a name="limitations"></a>

## ⚠️ Limitations

* No persistent user storage
* Depends on Gemini API availability


<a name="future-improvements"></a>

## 🔧 Future Improvements

* Add downloadable PDF itineraries
* Display interactive maps or hotel previews
* Store chat history across sessions
* Integrate flight & lodging search



<a name="contributors"></a>

## 👨‍💻 Contributors

* Abdussalam Hameedat



<a name="license"></a>

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for more details.



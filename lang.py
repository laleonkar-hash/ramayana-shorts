"""Everything that depends on the video language lives here. Default = Hindi (bigger audience).
Switch back to Marathi any time with the repo variable / env LANGUAGE=mr (or change the default in config.py)."""
import config

PACKS = {
    "hi": {
        "code": "hi", "name": "Hindi", "upper": "HINDI",
        "audience": "an ordinary Hindi-speaking viewer across India",
        "male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural",
        "recap": "पिछले भाग में", "today": "आज के भाग में",
        "names": ("राम, सीता, लक्ष्मण, हनुमान, रावण, दशरथ, कैकेयी, कौशल्या, भरत, सुग्रीव, बाली, जटायु, विभीषण, कुंभकर्ण, "
                  "मेघनाद, मंदोदरी, शूर्पणखा, मारीच, शबरी, जनक, विश्वामित्र, अयोध्या, लंका"),
        "title_suffix": " | रामायण भाग {n} #Shorts",
        "next_label": "अगला भाग:",
        "seo_line": "रामायण की कथा हिंदी में | Ramayan Katha in Hindi | Ramayan Episode {n}",
        "cta": "रोज़ नई रामायण कथा। चैनल को सब्सक्राइब करें और जय श्री राम लिखें! 🙏",
        "ai_note": "इस वीडियो के चित्र और आवाज़ AI की मदद से बनाए गए हैं।",
        "hashtags": ["#Ramayan", "#JaiShreeRam", "#Shorts", "#रामायण", "#श्रीराम", "#Bhakti", "#HinduMythology", "#RamayanKatha"],
        "tags": ["Ramayan", "रामायण", "Ramayan in Hindi", "रामायण कथा", "Ramayan Katha", "Ramayan story", "Ramayan shorts",
                 "Jai Shree Ram", "जय श्री राम", "Shri Ram", "श्री राम", "Lord Rama", "Ram Sita", "Hanuman", "Bhakti",
                 "Hindu mythology", "Valmiki Ramayan", "Hindi stories", "Shorts"],
    },
    "mr": {
        "code": "mr", "name": "Marathi", "upper": "MARATHI",
        "audience": "an ordinary Maharashtrian viewer",
        "male": "mr-IN-ManoharNeural", "female": "mr-IN-AarohiNeural",
        "recap": "मागच्या भागात", "today": "आजच्या भागात",
        "names": ("राम, सीता, लक्ष्मण, हनुमान, रावण, दशरथ, कैकेयी, कौसल्या, भरत, सुग्रीव, वाली, जटायू, विभीषण, कुंभकर्ण, "
                  "इंद्रजित, मंदोदरी, शूर्पणखा, मारीच, शबरी, जनक, विश्वामित्र, अयोध्या, लंका"),
        "title_suffix": " | रामायण भाग {n} #Shorts",
        "next_label": "पुढील भाग:",
        "seo_line": "रामायणाची कथा मराठीत | Ramayan Katha in Marathi | Ramayan Episode {n}",
        "cta": "रोज दोन नवीन रामायण कथा शॉर्ट्स. चॅनेल सबस्क्राईब करा आणि जय श्री राम लिहा! 🙏",
        "ai_note": "या व्हिडिओमधील चित्रे आणि आवाज AI च्या मदतीने तयार केले आहेत.",
        "hashtags": ["#Ramayana", "#JaiShreeRam", "#Shorts", "#रामायण", "#श्रीराम", "#मराठी", "#Bhakti"],
        "tags": ["Ramayana", "रामायण", "Marathi", "मराठी", "Shorts", "Lord Rama", "Jai Shree Ram", "श्रीराम"],
    },
}


def pack():
    return PACKS.get(config.LANGUAGE, PACKS["hi"])

# `web-auto-scraper-utility`

यह Python पैकेज Google खोज के शीर्ष परिणामों से जानकारी निकालता है और उसे संरचित (structured) JSON फ़ाइल (`memory.json`) में सहेजता है।

## विशेषताएं (Features)

* **स्वचालित ड्राइवर प्रबंधन (Automatic Driver Management):** `webdriver-manager` का उपयोग करके Chrome ड्राइवर को स्वचालित रूप से डाउनलोड और कॉन्फ़िगर करता है।
* **संरचित बचत (Structured Saving):** व्यक्तियों के लिए नाम, जन्मतिथि (DOB), और संक्षिप्त विवरण (About) निकालता है।
* **बैकअप (Backup):** डेटा सहेजने से पहले `memory.json` का स्वचालित रूप से बैकअप (`memory.json.bak`) बनाता है।

## आवश्यक शर्तें (Prerequisites)

* **Python 3.8 या उच्चतर।**
* **Google Chrome ब्राउज़र** आपके सिस्टम पर इंस्टॉल होना चाहिए।

## इंस्टॉलेशन (Installation)

आप `pip` का उपयोग करके पैकेज को सीधे PyPI से इंस्टॉल कर सकते हैं:

```bash
pip install web-auto-scraper-utility
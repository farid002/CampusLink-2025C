# GPT API Quraşdırma Guide

Bu guide bütün modullar üçün GPT API quraşdırmasını izah edir. **Bütün funksiyalar yalnız OpenAI API istifadə edir!**

## 1. OpenAI API Açarı Almaq

### Addım 1: Hesab Yaratmaq

1. [OpenAI Platform](https://platform.openai.com/) saytına daxil olun
2. Qeydiyyatdan keçin (və ya giriş edin)
3. Email təsdiqləyin

### Addım 2: API Açarı Yaratmaq

1. Sol menyudan **"API keys"** bölməsinə gedin
2. **"Create new secret key"** düyməsini basın
3. Açar üçün ad verin (məsələn: "CampusLink Workshop")
4. **"Create secret key"** düyməsini basın
5. **Açarı dərhal kopyalayın!** (yalnız bir dəfə göstərilir)

⚠️ **Vacib:** API açarını itirməyin! Əgər itirsəniz, yeni açar yaratmalı olacaqsınız.

### Addım 3: Billing (Ödəniş)

GPT API istifadəsi üçün kredit lazımdır:

1. Sol menyudan **"Billing"** bölməsinə gedin
2. **"Add payment method"** düyməsini basın
3. Kart məlumatlarınızı daxil edin
4. Minimum $5 kredit əlavə edin (təhsil üçün kifayətdir)

## 2. .env Faylı Yaratmaq

### Addım 1: .env.example-dan Kopyalama

```bash
cp .env.example .env
```

### Addım 2: API Açarını Əlavə Etmək

`.env` faylını açın və API açarınızı əlavə edin:

```bash
OPENAI_API_KEY=sk-proj-abc123...your-actual-key-here
```

⚠️ **Vacib:** `.env` faylını **heç vaxt** Git-ə commit etməyin! `.gitignore`-da artıq var.

## 3. Paketləri Quraşdırma

Yalnız `openai` paketi lazımdır:

```bash
pip install openai python-dotenv
```

## 4. API Növləri

Workshop-da 4 fərqli OpenAI API istifadə olunur:

### 4.1 GPT Chat API

**İstifadə:** Mətn emalı, xülasə, yaratma  
**Model:** `gpt-3.5-turbo` (tövsiyə olunur) və ya `gpt-4`

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Salam, dünya!"}
    ]
)

print(response.choices[0].message.content)
```

### 4.2 GPT Vision API

**İstifadə:** Şəkil analizi, OCR, object detection, face detection  
**Model:** `gpt-4o-mini` (tövsiyə olunur - ucuz) və ya `gpt-4o`

```python
from openai import OpenAI
import base64

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Şəkili base64-ə çevir
with open("image.jpg", "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Bu şəkildə nə var?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    }],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### 4.3 OpenAI Whisper API

**İstifadə:** Speech-to-text (audio-dan mətn)  
**Model:** `whisper-1` (tək seçim)

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="az"  # Azərbaycan dili
    )

print(transcript.text)
```

### 4.4 OpenAI TTS API

**İstifadə:** Text-to-speech (mətndən audio)  
**Model:** `tts-1` (tövsiyə olunur - ucuz) və ya `tts-1-hd` (yüksək keyfiyyət)

**Voice seçimləri:** `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Salam, bu test mesajıdır."
)

# Audio faylını yaz
response.stream_to_file("output.mp3")
```

## 5. Model Seçimi və Xərclər

### GPT Chat API

| Model | Xərc (1M tokens) | Tövsiyə |
|-------|------------------|---------|
| `gpt-3.5-turbo` | $0.50 input / $1.50 output | ✅ Tövsiyə olunur |
| `gpt-4` | $30 input / $60 output | Yüksək keyfiyyət lazımdırsa |
| `gpt-4o` | $5 input / $15 output | Daha güclü, amma bahalı |

### GPT Vision API

| Model | Xərc (1M tokens) | Tövsiyə |
|-------|------------------|---------|
| `gpt-4o-mini` | $0.15 input / $0.60 output | ✅ Tövsiyə olunur |
| `gpt-4o` | $2.50 input / $10 output | Daha dəqiq lazımdırsa |

### Whisper API

| Model | Xərc | Tövsiyə |
|-------|------|---------|
| `whisper-1` | $0.006 / dəqiqə | ✅ Tək seçim |

### TTS API

| Model | Xərc (1M characters) | Tövsiyə |
|-------|---------------------|---------|
| `tts-1` | $15 | ✅ Tövsiyə olunur |
| `tts-1-hd` | $30 | Yüksək keyfiyyət lazımdırsa |

### Təxmini Xərclər (Workshop üçün)

- 1000 Chat sorğusu: ~$0.10-0.50
- 100 Vision sorğusu: ~$0.15-0.50
- 100 Whisper transkript: ~$0.60
- 100 TTS audio: ~$0.15-0.30
- **Ümumi:** ~$1-2 (workshop üçün $5 kifayətdir)

## 6. Kodda İstifadə

### Nümunə 1: API Açarı Yoxlama

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY tapılmadı! .env faylına əlavə edin.")
```

### Nümunə 2: OpenAI Client Yaratmaq

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

## 7. Error Handling

### API Açarı Yoxdur

```python
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY tapılmadı!")
except ValueError as e:
    flash(f"Xəta: {str(e)}", "error")
```

### Rate Limit

```python
from openai import RateLimitError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    flash("Çox sayda sorğu göndərdiniz. Bir az gözləyin.", "error")
```

### Network Xətası

```python
from openai import APIConnectionError

try:
    response = client.chat.completions.create(...)
except APIConnectionError:
    flash("İnternet bağlantısı problemi. Yenidən cəhd edin.", "error")
```

### Insufficient Quota

```python
from openai import APIError

try:
    response = client.chat.completions.create(...)
except APIError as e:
    if "insufficient_quota" in str(e):
        flash("Kredit bitib. Billing bölməsində kredit əlavə edin.", "error")
```

## 8. Prompt Dizaynı

### Yaxşı Prompt Nümunəsi

```python
prompt = f"""
Bu OCR nəticəsini təmizlə, səhvləri düzəlt və strukturlaşdır:

{extracted_text}

Cavabı yalnız təmizlədilmiş mətn kimi qaytar.
"""
```

### Prompt Best Practices

1. **Aydın təlimatlar** verin
2. **Format** tələb edin (JSON, mətn, və s.)
3. **Nümunələr** verin (əgər lazımdırsa)
4. **Dil** təyin edin (Azərbaycan, İngilis)
5. **Max tokens** təyin edin (xərcləri azaltmaq üçün)

## 9. Test

### Test Kodu (Bütün API-lər)

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def test_all_apis():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ API açarı tapılmadı!")
        return False
    
    client = OpenAI(api_key=api_key)
    
    # Test Chat API
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Salam!"}]
        )
        print("✅ Chat API işləyir!")
    except Exception as e:
        print(f"❌ Chat API xətası: {str(e)}")
        return False
    
    # Test Whisper API (əgər audio faylı varsa)
    # try:
    #     with open("test.mp3", "rb") as audio_file:
    #         transcript = client.audio.transcriptions.create(
    #             model="whisper-1",
    #             file=audio_file
    #         )
    #     print("✅ Whisper API işləyir!")
    # except Exception as e:
    #     print(f"⚠️ Whisper API test edilmədi: {str(e)}")
    
    # Test TTS API
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="Test"
        )
        print("✅ TTS API işləyir!")
    except Exception as e:
        print(f"❌ TTS API xətası: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_all_apis()
```

## 10. Troubleshooting

### Problem: "API key not found"

**Həll:**
1. `.env` faylının layihə qovluğunda olduğunu yoxlayın
2. `load_dotenv()` çağırışının olduğunu yoxlayın
3. API açarının düzgün olduğunu yoxlayın

### Problem: "Rate limit exceeded"

**Həll:**
1. Bir az gözləyin (1-2 dəqiqə)
2. Sorğu sayını azaldın
3. GPT-4 əvəzinə GPT-3.5-turbo istifadə edin

### Problem: "Insufficient quota"

**Həll:**
1. Billing bölməsinə gedin
2. Kredit əlavə edin
3. Usage limit-ləri yoxlayın

### Problem: "Model not found"

**Həll:**
1. Model adının düzgün olduğunu yoxlayın (`gpt-3.5-turbo`, `gpt-4o-mini`, `whisper-1`, `tts-1`)
2. API açarınızın bu modellərə çıxışı olduğunu yoxlayın

## 11. Best Practices

1. **Ucuz modelləri seçin:** `gpt-3.5-turbo`, `gpt-4o-mini`, `tts-1`
2. **Max tokens təyin edin:** Xərcləri azaltmaq üçün
3. **Error handling əlavə edin:** Bütün API çağırışlarında
4. **Rate limiting:** Çox sorğu göndərməyin
5. **Kredit izləyin:** Billing bölməsində usage-ı yoxlayın

## Növbəti Addımlar

İndi hər modul üçün guide fayllarını oxuyun və implementasiyaya başlayın!

- [1_Blog_OCR_Guide.md](1_Blog_OCR_Guide.md) - GPT Vision API
- [2_Blog_TTS_Guide.md](2_Blog_TTS_Guide.md) - GPT Chat + TTS API
- [3_Events_Speech_Guide.md](3_Events_Speech_Guide.md) - Whisper + Chat API
- [4_Gallery_Detection_Guide.md](4_Gallery_Detection_Guide.md) - GPT Vision API
- [5_Gallery_Faces_Guide.md](5_Gallery_Faces_Guide.md) - GPT Vision API
- [6_Forum_TTS_Guide.md](6_Forum_TTS_Guide.md) - GPT Chat + TTS API
- [7_Polls_Speech_Guide.md](7_Polls_Speech_Guide.md) - Whisper + Chat API

Uğurlar! 🚀

# Events Speech-to-Text Modulu Guide

## Problemin Təsviri

Audio faylından OpenAI Whisper API ilə mətn çıxarmaq (Speech-to-Text), sonra GPT Chat API ilə transkripti strukturlaşdırmaq (ad, email, mesaj).

**Nə üçün lazımdır?**
- Səs ilə tədbirə qeydiyyat
- Audio mesajları mətnə çevirmək
- Accessibility

## Texnologiyalar

### OpenAI Whisper API
- **Nədir?** OpenAI-nin speech-to-text API-si
- **Model:** `whisper-1` (tək seçim)
- **Niyə Whisper?** Yüksək keyfiyyət, çox dilləri dəstəkləyir, cloud-da işləyir
- **Xərc:** ~$0.006 / dəqiqə

### GPT Chat API
- **Nədir?** OpenAI-nin mətn analizi API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Transkripti strukturlaşdırmaq (ad, email, mesaj)
- **Xərc:** ~$0.50-1.50 / 1M tokens

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
```

**Qeyd:** Yalnız `openai` paketi lazımdır!

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun.

## Kod Strukturu

`events_speech.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `transcribe_audio_with_whisper(audio_path)` - **TODO: Siz implement edəcəksiniz** (Whisper)
- `parse_speech_with_gpt(transcribed_text)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `speech_register(event_id)` - GET/POST route
- `speech_result(event_id, reg_id)` - Nəticə göstərmə

## Implementasiya

### Addım 1: Whisper ilə Audio-dan Mətn Çıxarma

`transcribe_audio_with_whisper(audio_path)` funksiyasını implement edin:

```python
def transcribe_audio_with_whisper(audio_path: str) -> str:
    """
    OpenAI Whisper API ilə audio faylından mətn çıxarır.
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="az"  # Azərbaycan dili
            )
        
        return transcript.text
    except Exception as e:
        raise ValueError(f"Whisper API xətası: {str(e)}")
```

**İzah:**
- `whisper-1` tək seçimdir
- `language="az"` Azərbaycan dili üçün
- Audio faylı binary mode-da açılmalıdır

### Addım 2: GPT Chat ilə Formatlaşdırma

`parse_speech_with_gpt(transcribed_text)` funksiyasını implement edin:

```python
def parse_speech_with_gpt(transcribed_text: str) -> dict:
    """
    GPT Chat API istifadə edərək səs transkriptini strukturlaşdırır.
    """
    from openai import OpenAI
    import json
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Bu mətndən ad, email və mesajı çıxar. Yalnız JSON formatında qaytar, başqa mətn yazma.

Format:
{{"name": "ad", "email": "email@example.com", "message": "mesaj mətni"}}

Mətn:
{transcribed_text}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # JSON-dan dict-ə çevir
        if "{{" in content and "}}" in content:
            json_start = content.find("{{")
            json_end = content.rfind("}}") + 1
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
        else:
            result = json.loads(content)
        
        # Validasiya
        if not all(key in result for key in ["name", "email", "message"]):
            raise ValueError("GPT cavabında lazımi sahələr yoxdur")
        
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT cavabı JSON formatında deyil: {str(e)}")
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- JSON formatında cavab tələb edin
- JSON parsing üçün error handling əlavə edin
- Validasiya əlavə edin

## Test

### Test Addımları

1. Tədbir yaradın
2. Tədbir detail səhifəsinə gedin
3. "Speech Register" düyməsini basın
4. Test audio faylı yükləyin
5. Nəticəni yoxlayın

## Xərclər

### Təxmini Xərclər

- 1 Whisper transkript (1 dəqiqə): ~$0.006
- 1 Chat sorğu: ~$0.0001-0.0005
- **100 qeydiyyat:** ~$0.60-1.00

## Növbəti Addımlar

1. `transcribe_audio_with_whisper()` funksiyasını implement edin
2. `parse_speech_with_gpt()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin

Uğurlar! 🚀

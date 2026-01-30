# Forum TTS Modulu Guide

## Problemin Təsviri

Forum mövzularını və cavabları GPT Chat API ilə qısaltmaq (xülasə), sonra OpenAI TTS API ilə səs faylına çevirmək.

**Nə üçün lazımdır?**
- Uzun forum yazılarını qısaltmaq
- Yazıları səsə çevirib dinləmək
- Accessibility

## Texnologiyalar

### GPT Chat API
- **Nədir?** OpenAI-nin mətn emalı API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Forum yazılarını qısaltmaq (xülasə)
- **Xərc:** ~$0.50-1.50 / 1M tokens

### OpenAI TTS API
- **Nədir?** OpenAI-nin text-to-speech API-si
- **Model:** `tts-1` (tövsiyə olunur - ucuz)
- **Voice seçimləri:** `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Xərc:** ~$15 / 1M characters

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
```

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun.

## Kod Strukturu

`forum_tts.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `summarize_with_gpt(content)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `create_tts_audio_with_openai(text, voice)` - **TODO: Siz implement edəcəksiniz** (OpenAI TTS)
- `tts_topic(topic_id)` - Mövzu üçün TTS
- `tts_reply(topic_id, reply_id)` - Cavab üçün TTS
- `tts_player(topic_id, file_id)` - Audio player

## Implementasiya

### Addım 1: GPT Chat ilə Xülasə

`summarize_with_gpt(content)` funksiyasını implement edin:

```python
def summarize_with_gpt(content: str) -> str:
    """
    GPT Chat API istifadə edərək mətni qısaldır (xülasə).
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Bu forum mesajını 3-4 cümləyə qısalt.
Əsas məzmunu saxla, amma detalları çıxar.

Orijinal mətn:
{content}

Qısa xülasə:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- `max_tokens=200` qısa xülasə üçün
- `temperature=0.5` balanslı

### Addım 2: OpenAI TTS ilə Audio Yaratma

`create_tts_audio_with_openai(text, voice)` funksiyasını implement edin:

```python
def create_tts_audio_with_openai(text: str, voice: str = "alloy") -> str:
    """
    OpenAI TTS API ilə mətni səs faylına çevirir.
    """
    from openai import OpenAI
    import secrets
    import os
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    # Audio qovluğunu yoxla/yarat
    audio_folder = os.path.join(
        current_app.config.get("AUDIO_FOLDER", os.path.join(current_app.root_path, "static", "audio")),
        "forum"
    )
    os.makedirs(audio_folder, exist_ok=True)
    
    try:
        # OpenAI TTS API
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Fayl adı
        filename = f"{secrets.token_hex(8)}.mp3"
        audio_path = os.path.join(audio_folder, filename)
        
        # Audio faylını yaz
        response.stream_to_file(audio_path)
        
        return f"forum/{filename}"
    except Exception as e:
        raise ValueError(f"OpenAI TTS API xətası: {str(e)}")
```

**İzah:**
- Blog TTS ilə eyni implementasiya
- Fayl `forum/` qovluğuna yazılır

## Test

### Test Addımları

1. Forum mövzusu yaradın
2. Forum detail səhifəsinə gedin
3. "TTS" düyməsini basın
4. Audio player-də dinləyin

## Xərclər

### Təxmini Xərclər

- 1 Chat sorğu (xülasə): ~$0.0001-0.0005
- 1 TTS audio (200 sözlük): ~$0.0001
- **100 forum mesajı:** ~$0.01-0.05

## Növbəti Addımlar

1. `summarize_with_gpt()` funksiyasını implement edin
2. `create_tts_audio_with_openai()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin

Uğurlar! 🚀

# Polls Speech Modulu Guide

## Problemin Təsviri

Audio faylından OpenAI Whisper API ilə mətn çıxarmaq (Speech-to-Text), sonra GPT Chat API ilə transkripti sorğu seçimlərinə uyğunlaşdırmaq.

**Nə üçün lazımdır?**
- Səs ilə sorğuya səs vermə
- Accessibility
- Sürətli səs vermə

## Texnologiyalar

### OpenAI Whisper API
- **Nədir?** OpenAI-nin speech-to-text API-si
- **Model:** `whisper-1` (tək seçim)
- **Niyə Whisper?** Yüksək keyfiyyət, çox dilləri dəstəkləyir
- **Xərc:** ~$0.006 / dəqiqə

### GPT Chat API
- **Nədir?** OpenAI-nin mətn analizi API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Transkripti sorğu seçimlərinə uyğunlaşdırmaq
- **Xərc:** ~$0.50-1.50 / 1M tokens

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
```

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun.

## Kod Strukturu

`polls_speech.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `transcribe_audio_with_whisper(audio_path)` - **TODO: Siz implement edəcəksiniz** (Whisper)
- `match_speech_to_poll_option(transcribed_text, options)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `speech_vote(poll_id)` - GET/POST route
- `speech_result(poll_id, vote_id)` - Nəticə göstərmə

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
- Events Speech ilə eyni implementasiya
- `language="az"` Azərbaycan dili üçün

### Addım 2: GPT Chat ilə Seçim Uyğunlaşdırma

`match_speech_to_poll_option(transcribed_text, options)` funksiyasını implement edin:

```python
def match_speech_to_poll_option(transcribed_text: str, options: list) -> int:
    """
    GPT Chat API istifadə edərək səs transkriptini sorğu seçimlərinə uyğunlaşdırır.
    """
    from openai import OpenAI
    import re
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    options_str = "\n".join([f"{i}. {opt}" for i, opt in enumerate(options)])
    
    prompt = f"""Bu mətn hansı seçimə uyğundur?
Yalnız rəqəm qaytar (0, 1, 2, və s.).

Seçimlər:
{options_str}

Mətn: {transcribed_text}

Cavab: Yalnız indeks rəqəmi (0, 1, 2, ...)"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Çox deterministik
            max_tokens=10
        )
        
        content = response.choices[0].message.content.strip()
        
        # Rəqəmi çıxar
        numbers = re.findall(r'\d+', content)
        if numbers:
            index = int(numbers[0])
            if 0 <= index < len(options):
                return index
        
        # Fallback: mətn uyğunluğuna görə tap
        transcribed_lower = transcribed_text.lower()
        for i, opt in enumerate(options):
            if opt.lower() in transcribed_lower or transcribed_lower in opt.lower():
                return i
        
        raise ValueError("Seçim tapılmadı")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- `temperature=0.1` çox deterministik üçün
- Regex ilə rəqəmi çıxarın
- Fallback mətn uyğunluğu əlavə edin
- Validasiya əlavə edin

## Test

### Test Addımları

1. Sorğu yaradın
2. Sorğu detail səhifəsinə gedin
3. "Speech Vote" düyməsini basın
4. Test audio faylı yükləyin
5. Nəticəni yoxlayın

## Xərclər

### Təxmini Xərclər

- 1 Whisper transkript (10 saniyə): ~$0.001
- 1 Chat sorğu: ~$0.0001-0.0005
- **100 səs:** ~$0.10-0.15

## Növbəti Addımlar

1. `transcribe_audio_with_whisper()` funksiyasını implement edin
2. `match_speech_to_poll_option()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin

Uğurlar! 🚀

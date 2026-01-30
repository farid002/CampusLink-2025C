# Blog TTS Modulu Guide

## Problemin Təsviri

Başlıq və açar sözlərdən GPT Chat API ilə avtomatik blog yazısı yaratmaq, sonra OpenAI TTS API ilə səs faylına çevirmək.

**Nə üçün lazımdır?**
- Blog yazılarını avtomatik yaratmaq
- Yazıları səsə çevirib dinləmək
- Accessibility (görüntü qüsurlu istifadəçilər üçün)

## Texnologiyalar

### GPT Chat API
- **Nədir?** OpenAI-nin mətn generasiyası API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Başlıq və açar sözlərdən blog yazısı yaratmaq
- **Xərc:** ~$0.50-1.50 / 1M tokens

### OpenAI TTS API
- **Nədir?** OpenAI-nin text-to-speech API-si
- **Model:** `tts-1` (tövsiyə olunur - ucuz) və ya `tts-1-hd` (yüksək keyfiyyət)
- **Voice seçimləri:** `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Xərc:** ~$15 / 1M characters

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
```

**Qeyd:** Yalnız `openai` paketi lazımdır! Heç bir xarici TTS kitabxanası lazım deyil.

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun və API açarınızı `.env` faylına əlavə edin.

## Kod Strukturu

`blog_tts.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `generate_blog_with_gpt(title, keywords)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `create_tts_audio_with_openai(text, voice)` - **TODO: Siz implement edəcəksiniz** (OpenAI TTS)
- `tts_generate(post_id)` - GET/POST route
- `tts_player(post_id, file_id)` - Audio player

## Implementasiya

### Addım 1: GPT Chat ilə Blog Yazısı Yaratma

`generate_blog_with_gpt(title, keywords)` funksiyasını implement edin:

```python
def generate_blog_with_gpt(title: str, keywords: str) -> str:
    """
    GPT Chat API istifadə edərək başlıq və açar sözlərdən blog yazısı yaradır.
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Bu başlıq və açar sözlərdən 500 sözlük, maraqlı və informativ blog yazısı yaz.
Yazı strukturlaşdırılmış, oxunaqlı və məzmunlu olsun.

Başlıq: {title}
Açar sözlər: {keywords}

Blog yazısını yalnız mətn kimi qaytar, başqa formatlama olmasın."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Yaradıcılıq üçün
            max_tokens=1000
        )
        blog_content = response.choices[0].message.content.strip()
        return blog_content
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- `temperature=0.7` yaradıcılıq üçün
- `max_tokens=1000` xərcləri məhdudlaşdırır
- Prompt-da aydın təlimatlar verin

### Addım 2: OpenAI TTS ilə Audio Yaratma

`create_tts_audio_with_openai(text, voice)` funksiyasını implement edin:

```python
def create_tts_audio_with_openai(text: str, voice: str = "alloy") -> str:
    """
    OpenAI TTS API ilə mətni səs faylına çevirir.
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    # Audio qovluğunu yoxla/yarat
    audio_folder = os.path.join(
        current_app.config.get("AUDIO_FOLDER", os.path.join(current_app.root_path, "static", "audio")),
        "blog"
    )
    os.makedirs(audio_folder, exist_ok=True)
    
    try:
        # OpenAI TTS API
        response = client.audio.speech.create(
            model="tts-1",  # Ən ucuz model
            voice=voice,  # alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        # Fayl adı
        filename = f"{secrets.token_hex(8)}.mp3"
        audio_path = os.path.join(audio_folder, filename)
        
        # Audio faylını yaz
        response.stream_to_file(audio_path)
        
        return f"blog/{filename}"
    except Exception as e:
        raise ValueError(f"OpenAI TTS API xətası: {str(e)}")
```

**İzah:**
- `tts-1` ən ucuz modeldir
- `voice` parametri səs növünü seçir
- `response.stream_to_file()` audio faylını yazır
- Fayl avtomatik MP3 formatında olur

## Template-lər

### tts_generate.html
Blog yazısı yaratma formu. Artıq hazırdır.

### tts_player.html
Audio player səhifəsi. Artıq hazırdır.

## Test

### Test Addımları

1. Blog yazısı yaradın
2. Blog detail səhifəsinə gedin
3. "TTS Generate" düyməsini basın
4. Başlıq və açar sözlər daxil edin
5. "Generate" düyməsini basın
6. Audio player-də dinləyin

## Çətinliklər və Həllər

### Problem: GPT API xətası

**Həll:**
- API açarını yoxlayın
- Billing-də kredit olduğunu yoxlayın
- Rate limit-i yoxlayın

### Problem: TTS API xətası

**Həll:**
- API açarını yoxlayın
- Billing-də kredit olduğunu yoxlayın
- Mətn uzunluğunu yoxlayın (çox uzun olmamalıdır)
- Voice adının düzgün olduğunu yoxlayın

### Problem: Audio yüklənmir

**Həll:**
- Audio qovluğunun yaradıldığını yoxlayın
- Fayl yolunun düzgün olduğunu yoxlayın
- Static file serving-in işlədiyini yoxlayın

## Xərclər

### Təxmini Xərclər

- 1 Chat sorğu (blog yazısı): ~$0.001-0.002
- 1 TTS audio (500 sözlük): ~$0.0001-0.0002
- **100 blog yazısı:** ~$0.10-0.20

## Genişləndirmə İdeyaları

1. **Voice seçimi** - İstifadəçi səs növünü seçə bilər
2. **Sürət tənzimləmə** - Audio sürətini dəyişdirmə
3. **Çoxdilli dəstək** - Fərqli dillərdə blog yazıları
4. **Tarixçə** - Keçmiş yaradılmış blog yazılarını göstərmə

## Növbəti Addımlar

1. `generate_blog_with_gpt()` funksiyasını implement edin
2. `create_tts_audio_with_openai()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin
5. Voice seçimi əlavə edin

Uğurlar! 🚀

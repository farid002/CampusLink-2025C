# Workshop 2: AI/ML Modulları (GPT-Only)

## Xoş gəldiniz!

Bu workshop-da CampusLink platformasına 7 yeni AI/ML modulu əlavə edəcəksiniz. **Bütün modullar yalnız OpenAI GPT API istifadə edir** - heç bir xarici AI/ML kitabxanası lazım deyil!

## Modul Siyahısı

| # | Modul | GPT API | Fayl | Guide |
|---|-------|---------|------|-------|
| 1 | **Blog** | Vision + Chat | `blog_ocr.py` | [1_Blog_OCR_Guide.md](1_Blog_OCR_Guide.md) |
| 2 | **Blog** | Chat + TTS | `blog_tts.py` | [2_Blog_TTS_Guide.md](2_Blog_TTS_Guide.md) |
| 3 | **Events** | Whisper + Chat | `events_speech.py` | [3_Events_Speech_Guide.md](3_Events_Speech_Guide.md) |
| 4 | **Gallery** | Vision + Chat | `gallery_detection.py` | [4_Gallery_Detection_Guide.md](4_Gallery_Detection_Guide.md) |
| 5 | **Gallery** | Vision + Chat | `gallery_faces.py` | [5_Gallery_Faces_Guide.md](5_Gallery_Faces_Guide.md) |
| 6 | **Forum** | Chat + TTS | `forum_tts.py` | [6_Forum_TTS_Guide.md](6_Forum_TTS_Guide.md) |
| 7 | **Polls** | Whisper + Chat | `polls_speech.py` | [7_Polls_Speech_Guide.md](7_Polls_Speech_Guide.md) |

## Quraşdırma Addımları

### 1. Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ya da
venv\Scripts\activate  # Windows
```

### 2. Paketləri Quraşdırma

```bash
pip install -r requirements.txt
```

**Qeyd:** Yalnız `openai` paketi lazımdır! Bütün funksiyalar OpenAI API ilə işləyir.

### 3. GPT API Açarı

**Vacib:** Hər tələbə öz OpenAI API açarını əlavə etməlidir!

1. [OpenAI Platform](https://platform.openai.com/api-keys) saytına daxil olun
2. API Keys bölməsinə gedin
3. "Create new secret key" düyməsini basın
4. Açarı kopyalayın
5. Billing bölməsində kredit əlavə edin (minimum $5)

### 4. .env Faylı Yaratmaq

Layihə qovluğunda `.env` faylı yaradın:

```bash
cp .env.example .env
```

Sonra `.env` faylını açın və API açarınızı əlavə edin:

```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 5. Database Yeniləməsi

Database avtomatik yenilənəcək. Əgər mövcud DB varsa, silin və yenidən yaradın:

```bash
rm campusconnect.db
python app.py
```

## Hər Modul Üçün Tələbə Tapşırıqları

Hər modulda siz özünüz implement etməlisiniz:

1. **GPT API çağırışları** - Vision, Whisper, TTS, Chat API-ləri
2. **Prompt dizaynı** - Hər modul üçün xüsusi prompt
3. **Error handling** - Xəta mesajları
4. **Test** - Nümunə məlumatlarla test

## Guide Faylları

- **[GPT_API_Setup.md](GPT_API_Setup.md)** - GPT API quraşdırma (hamı üçün)
- **[1_Blog_OCR_Guide.md](1_Blog_OCR_Guide.md)** - Blog OCR modulu (GPT Vision)
- **[2_Blog_TTS_Guide.md](2_Blog_TTS_Guide.md)** - Blog TTS modulu (GPT Chat + TTS)
- **[3_Events_Speech_Guide.md](3_Events_Speech_Guide.md)** - Events Speech modulu (Whisper + Chat)
- **[4_Gallery_Detection_Guide.md](4_Gallery_Detection_Guide.md)** - Gallery Detection modulu (GPT Vision)
- **[5_Gallery_Faces_Guide.md](5_Gallery_Faces_Guide.md)** - Gallery Faces modulu (GPT Vision)
- **[6_Forum_TTS_Guide.md](6_Forum_TTS_Guide.md)** - Forum TTS modulu (GPT Chat + TTS)
- **[7_Polls_Speech_Guide.md](7_Polls_Speech_Guide.md)** - Polls Speech modulu (Whisper + Chat)

## Texnologiyalar (Yalnız OpenAI)

- **GPT Vision API** (`gpt-4o-mini`) - Şəkil analizi, OCR, object detection, face detection
- **OpenAI Whisper API** (`whisper-1`) - Speech-to-text
- **OpenAI TTS API** (`tts-1`) - Text-to-speech
- **GPT Chat API** (`gpt-3.5-turbo`) - Mətn emalı, xülasə, yaratma

## Üstünlüklər

✅ **Sadə quraşdırma** - Yalnız `openai` paketi lazımdır  
✅ **Heç bir model faylı yoxdur** - Bütün modellər cloud-da  
✅ **100% pip-installable** - CMake və ya başqa sistem tələbləri yoxdur  
✅ **Bütün platformalarda işləyir** - Windows, macOS, Linux  
✅ **Yüksək keyfiyyət** - OpenAI-nin professional modelləri  
✅ **Asan istifadə** - Sadə API çağırışları  

## Qeydlər

- Bütün paketlər **pip-only** (cmake lazım deyil)
- Hər modul **ayrı faylda** (bir-birinə təsir etmir)
- Bütün kod **Azərbaycan dilində** comment-lərlə
- **TODO-lar** tələbə üçün işarələnib
- **Xərclər:** GPT API istifadəsi üçün kredit lazımdır (təxminən $5 workshop üçün kifayətdir)

## Yardım

Əgər problem yaşayırsınızsa:

1. Guide fayllarını diqqətlə oxuyun
2. Error mesajlarını yoxlayın
3. GPT API açarınızın düzgün olduğunu yoxlayın
4. Billing-də kredit olduğunu yoxlayın
5. Paketlərin quraşdırıldığını yoxlayın: `pip list`

Uğurlar! 🚀

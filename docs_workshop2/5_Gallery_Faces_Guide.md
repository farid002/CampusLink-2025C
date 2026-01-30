# Gallery Faces Modulu Guide

## Problemin Təsviri

Şəkillərdə üzləri GPT Vision API ilə tapmaq, sonra GPT Chat API ilə şəkil təsviri və teqlər yaratmaq.

**Nə üçün lazımdır?**
- Şəkillərdə neçə üz olduğunu tapmaq
- Şəkil təsviri avtomatik yaratmaq
- Teqlər avtomatik yaratmaq

## Texnologiyalar

### GPT Vision API
- **Nədir?** OpenAI-nin şəkil analizi API-si
- **Model:** `gpt-4o-mini` (tövsiyə olunur - ucuz)
- **Niyə GPT Vision?** Yüksək keyfiyyət, heç bir model faylı lazım deyil
- **Xərc:** ~$0.15-0.60 / 1M tokens

### GPT Chat API
- **Nədir?** OpenAI-nin mətn generasiyası API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Şəkil təsviri və teqlər yaratmaq
- **Xərc:** ~$0.50-1.50 / 1M tokens

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
```

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun.

## Kod Strukturu

`gallery_faces.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `detect_faces_with_gpt_vision(image_path)` - **TODO: Siz implement edəcəksiniz** (GPT Vision)
- `generate_description_with_gpt(face_count)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `faces_detect(image_id)` - GET/POST route
- `faces_result(image_id, result_id)` - Nəticə göstərmə

## Implementasiya

### Addım 1: GPT Vision ilə Üz Tapma

`detect_faces_with_gpt_vision(image_path)` funksiyasını implement edin:

```python
def detect_faces_with_gpt_vision(image_path: str) -> int:
    """
    GPT Vision API ilə şəkillərdə üzləri tapır.
    """
    from openai import OpenAI
    import base64
    import re
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    # Şəkili base64-ə çevir
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Bu şəkildə neçə üz var? Yalnız rəqəm qaytar (məsələn: 0, 1, 2, 3 və s.)."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    }
                ]
            }],
            max_tokens=10
        )
        
        content = response.choices[0].message.content.strip()
        
        # Rəqəmi çıxar
        numbers = re.findall(r'\d+', content)
        if numbers:
            return int(numbers[0])
        return 0
    except Exception as e:
        raise ValueError(f"GPT Vision API xətası: {str(e)}")
```

**İzah:**
- Yalnız rəqəm qaytarılmasını tələb edin
- Regex ilə rəqəmi çıxarın
- Error handling əlavə edin

### Addım 2: GPT Chat ilə Təsvir və Teqlər

`generate_description_with_gpt(face_count)` funksiyasını implement edin:

```python
def generate_description_with_gpt(face_count: int) -> tuple:
    """
    GPT Chat API istifadə edərək şəkil təsviri və teqlər yaradır.
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    if face_count == 0:
        prompt = "Bu şəkildə üz yoxdur. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    elif face_count == 1:
        prompt = "Bu şəkildə 1 üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    else:
        prompt = f"Bu şəkildə {face_count} üz var. Şəkil haqqında qısa təsvir və 5 teq yarat. Format: Təsvir: ... | Teqlər: tag1, tag2, tag3, tag4, tag5"
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse description and tags
        if "|" in content:
            parts = content.split("|", 1)
            description = parts[0].replace("Təsvir:", "").strip()
            tags_part = parts[1].replace("Teqlər:", "").strip()
            tags = tags_part
        else:
            description = content
            tags = "şəkil, foto"
        
        return description, tags
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- Format tələb edin (Təsvir: ... | Teqlər: ...)
- Parse etmək üçün string splitting istifadə edin
- Fallback əlavə edin

## Test

### Test Addımları

1. Şəkil yükləyin
2. Gallery detail səhifəsinə gedin
3. "Detect Faces" düyməsini basın
4. Nəticəni yoxlayın

## Xərclər

### Təxmini Xərclər

- 1 Vision sorğu: ~$0.001-0.002
- 1 Chat sorğu: ~$0.0001-0.0005
- **100 detection:** ~$0.10-0.25

## Növbəti Addımlar

1. `detect_faces_with_gpt_vision()` funksiyasını implement edin
2. `generate_description_with_gpt()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin

Uğurlar! 🚀

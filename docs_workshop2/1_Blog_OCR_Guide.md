# Blog OCR Modulu Guide

## Problemin Təsviri

Blog yazılarına şəkil yükləyib, şəkildəki mətni avtomatik oxumaq (OCR - Optical Character Recognition). Sonra GPT Chat API ilə mətni təmizləmək və təkmilləşdirmək.

**Nə üçün lazımdır?**
- Qeydlərin şəkilini yükləyib mətni çıxarmaq
- Lövhələrdəki mətni oxumaq
- Sənədləri rəqəmsallaşdırmaq

## Texnologiyalar

### GPT Vision API
- **Nədir?** OpenAI-nin şəkil analizi API-si
- **Model:** `gpt-4o-mini` (tövsiyə olunur - ucuz) və ya `gpt-4o`
- **Niyə GPT Vision?** Yüksək keyfiyyət, heç bir model faylı lazım deyil, cloud-da işləyir
- **Xərc:** ~$0.15-0.60 / 1M tokens

### GPT Chat API
- **Nədir?** OpenAI-nin mətn emalı API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** OCR nəticəsini təmizləmək, səhvləri düzəltmək
- **Xərc:** ~$0.50-1.50 / 1M tokens

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv Pillow
```

**Qeyd:** Yalnız `openai` paketi lazımdır! Heç bir model faylı yükləmək lazım deyil.

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun və API açarınızı `.env` faylına əlavə edin.

## Kod Strukturu

`blog_ocr.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `extract_text_with_gpt_vision(image_path)` - **TODO: Siz implement edəcəksiniz** (GPT Vision)
- `improve_text_with_gpt(extracted_text)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `ocr_extract(post_id)` - GET/POST route
- `ocr_result(post_id, result_id)` - Nəticə göstərmə

## Implementasiya

### Addım 1: GPT Vision ilə Mətn Çıxarma

`extract_text_with_gpt_vision(image_path)` funksiyasını implement edin:

```python
def extract_text_with_gpt_vision(image_path: str) -> str:
    """
    GPT Vision API ilə şəkilərdən mətn çıxarır.
    """
    from openai import OpenAI
    import base64
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    # Şəkili base64-ə çevir
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        # GPT Vision API çağırışı
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Ən ucuz vision model
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Bu şəkildəki bütün mətni çıxar. Mətni dəqiq və tam şəkildə qaytar, heç bir şeyi buraxma."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }],
            max_tokens=1000
        )
        
        extracted_text = response.choices[0].message.content.strip()
        return extracted_text if extracted_text else "Mətn tapılmadı"
    except Exception as e:
        raise ValueError(f"GPT Vision API xətası: {str(e)}")
```

**İzah:**
- `base64.b64encode()` şəkili base64 formatına çevirir
- `gpt-4o-mini` ən ucuz vision modeldir
- `data:image/jpeg;base64,` prefix-i lazımdır
- `max_tokens=1000` xərcləri məhdudlaşdırır

### Addım 2: GPT Chat ilə Təmizləmə

`improve_text_with_gpt(extracted_text)` funksiyasını implement edin:

```python
def improve_text_with_gpt(extracted_text: str) -> str:
    """
    GPT Chat API istifadə edərək OCR mətnini təmizləyir və təkmilləşdirir.
    """
    from openai import OpenAI
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Bu OCR nəticəsini təmizlə, səhvləri düzəlt və strukturlaşdır.
Mətni daha oxunaqlı et, amma məzmunu dəyişmə.

OCR nəticəsi:
{extracted_text}

Cavabı yalnız təmizlədilmiş mətn kimi qaytar."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Daha deterministik
            max_tokens=1000
        )
        improved_text = response.choices[0].message.content.strip()
        return improved_text
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

**İzah:**
- `temperature=0.3` daha deterministik cavab üçün
- Prompt-da aydın təlimatlar verin
- Məzmunu dəyişməməyi xüsusi qeyd edin

## Template-lər

### ocr_upload.html
Şəkil yükləmə formu. Artıq hazırdır.

### ocr_result.html
OCR nəticəsini göstərir:
- Orijinal şəkil
- Çıxarılmış mətn (GPT Vision)
- Təkmilləşdirilmiş mətn (GPT Chat)

## Test

### Test Addımları

1. Blog yazısı yaradın
2. Blog detail səhifəsinə gedin
3. "OCR" düyməsini basın
4. Test şəkili yükləyin (mətn olan şəkil)
5. Nəticəni yoxlayın

### Test Şəkilləri

- Lövhə şəkli (ağ fon, qara mətn)
- Qeyd şəkli
- Sənəd şəkli

## Çətinliklər və Həllər

### Problem: GPT Vision API xətası

**Həll:**
- API açarını yoxlayın
- Billing-də kredit olduğunu yoxlayın
- Şəkil ölçüsünü yoxlayın (çox böyük olmamalıdır)
- Base64 encoding-in düzgün olduğunu yoxlayın

### Problem: OCR dəqiq deyil

**Həll:**
- Şəkil keyfiyyətini yaxşılaşdırın
- Ağ fon, qara mətn daha yaxşıdır
- GPT Chat təmizləmə funksiyası kömək edəcək
- Prompt-u daha spesifik edin

### Problem: Rate limit

**Həll:**
- Bir az gözləyin (1-2 dəqiqə)
- Sorğu sayını azaldın
- `gpt-4o-mini` istifadə edin (daha ucuz)

## Xərclər

### Təxmini Xərclər

- 1 Vision sorğu: ~$0.001-0.002
- 1 Chat sorğu: ~$0.0001-0.0005
- **100 OCR işləmi:** ~$0.10-0.25

## Genişləndirmə İdeyaları

1. **Çoxdilli dəstək** - Fərqli dilləri avtomatik tanıma
2. **Batch processing** - Bir neçə şəkili eyni vaxtda emal etmə
3. **PDF dəstəyi** - PDF sənədlərdən mətn çıxarma
4. **Tarixçə** - Keçmiş OCR nəticələrini göstərmə
5. **Formatlaşdırma** - Mətni strukturlaşdırma (başlıqlar, siyahılar)

## Növbəti Addımlar

1. `extract_text_with_gpt_vision()` funksiyasını implement edin
2. `improve_text_with_gpt()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin
5. Prompt-u təkmilləşdirin

Uğurlar! 🚀

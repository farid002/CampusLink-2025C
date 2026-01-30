# Gallery Detection Modulu Guide

## Problemin Təsviri

Şəkillərdə obyektləri GPT Vision API ilə tapmaq, sonra GPT Chat API ilə təbii dildə təsvir etmək.

**Nə üçün lazımdır?**
- Şəkillərdə nə olduğunu avtomatik tanımaq
- Obyektləri saymaq
- Şəkil təsviri yaratmaq

## Texnologiyalar

### GPT Vision API
- **Nədir?** OpenAI-nin şəkil analizi API-si
- **Model:** `gpt-4o-mini` (tövsiyə olunur - ucuz)
- **Niyə GPT Vision?** Yüksək keyfiyyət, heç bir model faylı lazım deyil
- **Xərc:** ~$0.15-0.60 / 1M tokens

### GPT Chat API
- **Nədir?** OpenAI-nin mətn generasiyası API-si
- **Model:** `gpt-3.5-turbo` (tövsiyə olunur)
- **Niyə lazımdır?** Obyektləri təbii dildə təsvir etmək
- **Xərc:** ~$0.50-1.50 / 1M tokens

### OpenCV (Optional)
- **Nədir?** Computer vision kitabxanası
- **Niyə lazımdır?** Yalnız qutular çəkmək üçün (vizualizasiya)
- **Qeyd:** Detection GPT Vision ilə edilir, OpenCV yalnız qutular üçündür

## Quraşdırma Addımları

### 1. Paketləri Quraşdırma

```bash
pip install openai python-dotenv
# Optional: opencv-python (yalnız qutular çəkmək üçün)
```

### 2. GPT API Açarı

[GPT_API_Setup.md](GPT_API_Setup.md) guide-ını oxuyun.

## Kod Strukturu

`gallery_detection.py` faylında:

- `get_gpt_api_key()` - API açarı yoxlama
- `detect_objects_with_gpt_vision(image_path)` - **TODO: Siz implement edəcəksiniz** (GPT Vision)
- `draw_boxes(image_path, detections, output_path)` - **TODO: Siz implement edəcəksiniz** (OpenCV - optional)
- `describe_objects_with_gpt(detected_objects)` - **TODO: Siz implement edəcəksiniz** (GPT Chat)
- `detect(image_id)` - GET/POST route
- `detection_result(image_id, result_id)` - Nəticə göstərmə

## Implementasiya

### Addım 1: GPT Vision ilə Obyekt Tapma

`detect_objects_with_gpt_vision(image_path)` funksiyasını implement edin:

```python
def detect_objects_with_gpt_vision(image_path: str) -> list:
    """
    GPT Vision API ilə şəkillərdə obyektləri tapır.
    """
    from openai import OpenAI
    import base64
    import json
    
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
                        "text": """Bu şəkildəki bütün obyektləri tap və JSON formatında qaytar.
Hər obyekt üçün: class (obyekt növü), confidence (0-1 arası), bbox (x1, y1, x2, y2 koordinatları).

Format:
[
  {{"class": "person", "confidence": 0.95, "bbox": [10, 20, 100, 200]}},
  {{"class": "car", "confidence": 0.87, "bbox": [150, 50, 300, 180]}}
]

Yalnız JSON qaytar, başqa mətn yazma."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                    }
                ]
            }],
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # JSON-dan list-ə çevir
        if "[" in content and "]" in content:
            json_start = content.find("[")
            json_end = content.rfind("]") + 1
            json_str = content[json_start:json_end]
            objects = json.loads(json_str)
        else:
            objects = json.loads(content)
        
        return objects if isinstance(objects, list) else []
    except json.JSONDecodeError as e:
        raise ValueError(f"GPT cavabı JSON formatında deyil: {str(e)}")
    except Exception as e:
        raise ValueError(f"GPT Vision API xətası: {str(e)}")
```

**İzah:**
- JSON formatında cavab tələb edin
- Bbox koordinatları opsional ola bilər
- JSON parsing üçün error handling əlavə edin

### Addım 2: GPT Chat ilə Təsvir

`describe_objects_with_gpt(detected_objects)` funksiyasını implement edin:

```python
def describe_objects_with_gpt(detected_objects: list) -> str:
    """
    GPT Chat API istifadə edərək tapılan obyektləri təbii dildə təsvir edir.
    """
    from openai import OpenAI
    import json
    
    api_key = get_gpt_api_key()
    client = OpenAI(api_key=api_key)
    
    if not detected_objects:
        return "Şəkildə heç bir obyekt tapılmadı."
    
    objects_str = json.dumps(detected_objects, ensure_ascii=False, indent=2)
    
    prompt = f"""Bu şəkildə tapılan obyektləri təbii dildə, maraqlı və informativ şəkildə təsvir et.
Obyektlərin sayını, növlərini və ümumi mənzərəni izah et.

Tapılan obyektlər:
{objects_str}

Cavabı Azərbaycan dilində, 3-4 cümlə ilə qaytar."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        description = response.choices[0].message.content.strip()
        return description
    except Exception as e:
        raise ValueError(f"GPT API xətası: {str(e)}")
```

## Test

### Test Addımları

1. Şəkil yükləyin
2. Gallery detail səhifəsinə gedin
3. "Detect Objects" düyməsini basın
4. Nəticəni yoxlayın

## Xərclər

### Təxmini Xərclər

- 1 Vision sorğu: ~$0.001-0.002
- 1 Chat sorğu: ~$0.0001-0.0005
- **100 detection:** ~$0.10-0.25

## Növbəti Addımlar

1. `detect_objects_with_gpt_vision()` funksiyasını implement edin
2. `describe_objects_with_gpt()` funksiyasını implement edin
3. Test edin
4. Error handling əlavə edin

Uğurlar! 🚀

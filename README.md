# Akıllı Asansör Trafiği Simülasyonu

Vize sürümü: **Streamlit** arayüzü + **SimPy** ayrık olay simülasyonu.

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

## Proje Yapısı
- `app.py`: Streamlit arayüzü (metrikler, grafikler, ısı haritası)
- `src/elevator_sim.py`: SimPy simülasyon çekirdeği
- `RAPOR.md`: vize raporu (istenen maddeler)

## Geliştirmeye Açık Alanlar (Final)
- dispatch stratejileri (nearest-car, yön bazlı toplama, destination control)
- öncelikli yolcular
- arıza/bakım senaryoları
- senaryo karşılaştırma ve optimizasyon


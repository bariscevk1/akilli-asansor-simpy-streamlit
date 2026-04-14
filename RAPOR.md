# Akıllı Asansör Trafiği Simülasyonu (Streamlit + SimPy) — Vize Raporu

## 1) Projenin çözdüğü problem
Çok katlı binalarda yoğun saatlerde (sabah giriş, öğle, akşam çıkış) **asansör bekleme süreleri artar**, katlarda kuyruk birikir ve kapasite yetersizliği yaşanır. Bu proje, **asansör sayısı / kapasitesi / hız / kontrol stratejisi** gibi parametrelerin;

- bekleme sürelerine (ortalama ve P90/P95),
- kuyruk birikimine,
- asansör doluluk/kullanım oranına

etkisini **ayrık olay simülasyonu** ile incelemeyi amaçlar.

## 2) Kullanılacak veri seti
Vize tesliminde, gerçek bir veri seti yerine **sentetik (simülasyon tabanlı) talep verisi** kullanılacaktır:

- Yolcu gelişleri: yoğunluğa göre tanımlanan dağılımlardan (örn. üstel / parça-bazlı yoğunluk)
- Başlangıç katı ve hedef katı: seçilen senaryoya göre (örn. *up-peak*, *down-peak*, *mixed*)

Final aşamasında opsiyonel olarak:
- bina içi turnike/kapı geçiş sayıları,
- asansör logları,
- derslik saatlerinden türetilmiş yoğunluk profilleri

gibi gerçek verilerle kalibrasyon yapılabilir.

## 3) Kod tarafında neler olacak (kütüphaneler)
- **SimPy**: ayrık olay simülasyonu (yolcu süreçleri, asansör süreçleri, kuyruklar)
- **Streamlit**: arayüz (parametre seçimi, simülasyonu çalıştırma, rapor/çıktı gösterimi)
- **Pandas / NumPy**: çıktıların tabloya dökülmesi ve özet istatistikler
- **Plotly**: grafikler (zaman serisi, ısı haritası vb.)

Vize sürümü kod kapsamı:
- Kat bazında yolcu kuyruğu (FIFO)
- 1 veya 2 asansör
- Basit dispatch: “bekleyen çağrılardan birini seçip” sırayla servis
- Metrikler: bekleme süreleri, kuyruk uzunluğu, asansör doluluk yaklaşımı

Final sürümü için bırakılan geliştirme alanları:
- gelişmiş kontrol stratejileri (nearest-car, yön bazlı toplama, destination control)
- öncelikli yolcu tipleri (engelli/servis/yangın modu)
- arıza/bakım senaryoları (MTBF/MTTR)
- parametre arama/optimizasyon (hedef: P90 bekleme < X sn gibi)

## 4) Arayüz teknolojisi
Arayüz **Streamlit** ile web tabanlı geliştirilecektir.

Arayüzde:
- parametre girişi (kat sayısı, asansör sayısı, hız, kapasite, trafik senaryosu, simülasyon süresi)
- “Simülasyonu çalıştır” butonu
- özet metrikler ve grafikler

## 5) Canlı izlenebilir/görselleştirilebilir yapılar (ısı haritası / GUI vb.)
Vize sürümünde:
- **Isı haritası (heatmap)**: zaman dilimlerine göre kat bazında ortalama kuyruk yoğunluğu
- **Zaman serisi grafikleri**: toplam kuyruk uzunluğu ve bekleme metrikleri

Final sürümünde opsiyonel:
- gerçek zamanlı “canlı” animasyon (asansör konumu, kat kuyruğu) veya adım adım simülasyon izleme
- daha zengin dashboard (çoklu senaryo karşılaştırma)

## 6) GitHub linki
GitHub deposu vize tesliminde boş/iskelet olarak açılacak ve finalde tamamlanacaktır.

- Repo linki: **https://github.com/bariscevk1/akilli-asansor-simpy-streamlit**

### Repo QR Kodu
![GitHub Repo QR](assets/github_repo_qr.png)

## Ek: Çalıştırma (vize sürümü)
Projede `requirements.txt` bulunmaktadır. Kurulum ve çalıştırma:

```bash
pip install -r requirements.txt
streamlit run app.py
```


# PapAuto — расширение перечня моделей по рынкам Японии, Южной Кореи и Китая

Дата исследования: 8 ноября 2026 года. Файл предназначен для внутреннего анализа; **никаких ссылок на конкурентов не публикуем на PapAuto, никому не пишем**.

## Источник и границы использования

Из открытых страниц JTECO проверены **только названия моделей и принадлежность к рыночным каталогам**, не фотографии, тексты карточек, цены, аукционные листы или база результатов продаж. На JTECO доступны отдельные разделы для японских аукционов, автомобилей из Южной Кореи и новых/подержанных автомобилей из Китая. Это **конкурентный ассортиментный ориентир**, а не подтверждение текущих продаж или доступности каждой модели у PapAuto.

Внутренние страницы проверки:

- Японская статистика: https://jteco.ru/auto/stat/
- Toyota: https://jteco.ru/auto/stat/toyota/
- Honda: https://jteco.ru/auto/stat/honda/
- Nissan: https://jteco.ru/auto/stat/nissan/
- Mazda: https://jteco.ru/auto/stat/mazda/
- Suzuki: https://jteco.ru/auto/stat/suzuki/
- Subaru: https://jteco.ru/auto/stat/subaru/
- Mitsubishi: https://jteco.ru/auto/stat/mitsubishi/
- Lexus: https://jteco.ru/auto/stat/lexus/
- Daihatsu: https://jteco.ru/auto/stat/daihatsu/
- Южная Корея: https://jteco.ru/korea-auc/auto/
- Hyundai: https://jteco.ru/korea-auc/auto/hyundai/
- Kia: https://jteco.ru/korea-auc/auto/kia/
- Genesis: https://jteco.ru/korea-auc/auto/genesis/
- BMW: https://jteco.ru/korea-auc/auto/bmw/
- Mercedes-Benz: https://jteco.ru/korea-auc/auto/mercedes-benz/
- Audi: https://jteco.ru/korea-auc/auto/audi/
- Китай (б/у): https://jteco.ru/china/auto/
- Китай (новые): https://jteco.ru/china-car-new/
- Geely: https://jteco.ru/china/auto/geely/
- Changan: https://jteco.ru/china/auto/changan/
- BYD: https://jteco.ru/china/auto/byd/
- Haval: https://jteco.ru/china/auto/haval/
- GAC: https://jteco.ru/china/auto/gac/
- Tank: https://jteco.ru/china/auto/tank/
- Zeekr: https://jteco.ru/china/auto/zeekr/
- AITO: https://jteco.ru/china/auto/aito/
- Voyah: https://jteco.ru/china/auto/voyah/
- Xiaomi: https://jteco.ru/china/auto/xiaomi/
- Jetour: https://jteco.ru/china/auto/jetour/
- Exeed: https://jteco.ru/china/auto/exeed/

## Что уже внедрено в PapAuto

Файл `vehicle-catalogue.js`: добавлены вручную отобранные названия семейств моделей для японского, корейского и китайского направления. Исходно было **181 запись, 180 уникальных по паре «марка + модель» внутри рынка**. После добавления и дедупликации — **518 уникальных записей по трём рынкам**:

- Япония: **189** моделей;
- Южная Корея: **129** моделей;
- Китай: **200** моделей.

Число означает записи справочника, **не реальные доступные машины, не лоты и не число фотографий**.

Отдельно реализованы: поиск, фильтр страны, фильтр марки, фильтр типа двигателя, локальные фотографии четырёх моделей с лицензией CC0. Для большинства дополненных моделей двигатель, комплектация и цена специально не придуманы — отображается «Характеристики уточняются». Нет сторонних URL внутри пользовательских карточек.

## Что важно для следующих этапов

1. Не использовать прямые переходы из PapAuto на JTECO, Drom, корейские/китайские площадки.
2. Не копировать фотографии/чужие описания/торговые цены из каталога конкурента.
3. Для реальных аукционных лотов подтверждать исходный лот, дату, состояние, цену, права на фото и документы; для демонстрационных модельных карточек не выдавать данные за итог торгов.
4. Проверить поставщиков и правовой статус фотографий для остальных моделей, чтобы расширять каталог изображениями с локальным хранением, а не массовой подстановкой чужих фото.
5. Для SEO приоритетные группы: Япония (Toyota Corolla, Honda Fit/Freed/Stepwgn, Nissan Note/X-Trail, Suzuki Jimny, Mazda CX-5); Корея (Hyundai Avante/Tucson/Staria, Kia K5/Sorento/Sportage, Genesis и немецкие марки); Китай (Geely Monjaro, Changan CS75/UNI, BYD Song, GAC GS8, Tank, Zeekr).

# PAPAUTO — НЕИЗМЕННОЕ ПРАВИЛО АУКЦИОННОЙ ГАЛЕРЕИ

Цель: 500 РАЗНЫХ полных карточек, а не 500 случайных красивых изображений.

**Разрешено только:** подтверждённые аукционные фотографии ИМЕННО ЭТОГО автомобиля, подлинный ПОЛНЫЙ аукционный лист того же лота, точные описание/год/пробег/оценка/аукцион/дата/номер. Фактическая цена продажи допустима только при подтверждении завершённых торгов.

**Проверенное исключение от 13.11.2026:** Audi Q2 2021 и Audi Q3 2021 (файлы `audi-q2-2021-*` и `audi-q3-2021-*`) отклонены пользователем как уличная/дилерская съёмка. Оба старых демонстрационных макета отозваны, фотографии и схемы этих двух моделей блокируются в публичной сборке с заглушкой 404. Наличие таблички AUCNET на кузове не является доказательством аукционного происхождения снимка. Старые оригиналы в исследовательских материалах не разрешено переиспользовать ни для других моделей, ни как пример будущей карточки.

**Строго запрещено навсегда:** уличные снимки, картинки с парковки или склада, дилерские/салонные/портовые/рекламные/стоковые фото, картинки другой машины, сгенерированные ИИ изображения, не подтверждённые аукционные фото, вымышленные аукционные листы, пробег и цены. Никакой подмены ракурса. Никаких переходов к конкурентам на клиентском сайте. Ранее удалённые street-photo sources НЕ возвращать.

**Требование к НОВЫМ карточкам:** оригинальный аукционный снимок и лист с идентичными номером лота, датой и аукционом; минимум один реальный полноразмерный снимок; достоверное описание; отдельное документальное разрешение на коммерческий показ/самостоятельный хостинг и фотографий, и листа. Схема повреждений, карточка дилера или предложенная цена НЕ заменяют аукционный лист и итог торгов.

**Как добавлять:** сохранять непроверенные источники только в research/; сверить документы, номер, дату, изображения и права; затем запустить scripts/import_auction_photos.py --dry-run с локальным медиапакетом и подтверждениями; после успешного импорта обязательно запустить тесты, проверить галерею в Chromium и только затем публиковать. Предупреждение: данные пользователя о праве на фото не являются проверкой прав, нужны доказательства.

**Технические пути:** assets/auction/home и assets/premium-auctions — исторический базовый комплект. assets/auction/approved — отдельное пространство новых разрешённых лотов. Регистр: data/approved-auction-lots.json. Публичная витрина: gallery.html + gallery.js + встроенный JSON + адаптивная сетка. Исследовательские подборки нельзя выдавать за опубликованные карточки.

**Текущая база (13.11.2026):** 37 ранее опубликованных исторических лотов; права повторной публикации архивных сторонних фотографий у части из них не подтверждены — не выдавать их за лицензированные. Внутренний резерв research/auction-500-candidate-queue-2026-11-13.json: 250 ссылок из 146 кандидатных лотов. Готовых новых лотов по строгому стандарту: 0. Не изменять число 37 на 500 до появления 500 полных карточек.

**Контроль качества:** CI обязан отклонять не-аукционные пути и импорт без подлинного листа, подтверждённого лота и прав. Новые фото не загружать автоматически только по URL.

Owner instruction 2026-11-19: exactly the 50 reviewed Japan archival reference records in research/owner-approved-50-archive-2026-11-19.json were authorized explicitly under the owner’s responsibility. This is not a third-party license; rights_confirmed stays false. No general exception, no street or unrelated photos, no missing sheets, no external card links, and no available-for-sale claims. Ordinary importer rights requirements remain in force for any other batch.

Owner instruction 2026-11-19, second batch: exactly the 50 cards in research/owner-approved-second-50-archive-2026-11-19.json approved after PDF/JPG presentation. No general release exception and no third-party license assertion. Keep all original photo, sheet and no-street-photo safeguards.

Owner instruction 2026-11-20: exact 49 previously displayed Xin Che Hang supplier examples explicitly approved for separate China-order section under owner responsibility. This is NOT an auction listing or a third-party license. Only immutable photo set verified by scripts/verify_china_order_release.py is allowed on china-order.html; rights_confirmed remains false, report and documented power unverified. No additional exception or alteration of auction policy. No competitor links or live-stock claims.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the 30 fixed digests in verify_china_order_release.py are newly allowed, alongside the previous 49; auction safeguards unchanged. The separate five-card preview is not included in this release.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the third batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 79; auction safeguards unchanged. Includes the five previously previewed distinct models only as part of this approved batch.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the fourth batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 109; auction safeguards unchanged.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the fifth batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 139; auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 additional power-listed supplier examples approved for china-order.html. Only the fixed sixth batch digests are allowed alongside previous 169. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact 11 additional power-listed supplier examples approved for china-order.html. Only the fixed seventh batch digests are allowed alongside previous 199. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact 10 additional power-listed supplier examples approved for china-order.html. Only the fixed eighth batch digests are allowed alongside previous 210. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact nine GoldenLane source-linked supplier examples approved for china-order.html. Only fixed ninth-batch digests permitted after validation; no license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_30_China_review.pdf expressly approved for china-order.html. Only fixed tenth-batch digests permitted, 19 GoldenLane and 11 EZ Auto Global. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch11.pdf expressly approved for china-order.html. Only fixed eleventh-batch digests permitted, 28 Xin Che Hang and 2 China Used Car. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch12.pdf expressly approved for china-order.html. Only fixed twelfth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch13.pdf expressly approved for china-order.html. Only fixed thirteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch14.pdf expressly approved for china-order.html. Only fixed fourteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

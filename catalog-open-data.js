(() => {
  "use strict";
  // PapAuto own model index: no remote photos, no outgoing seller URLs.
  const by = id => document.getElementById(id);
  const grid = by("catalogGrid"), search = by("modelQuery"), country = by("countryFilter");
  const make = by("makeFilter"), power = by("powerFilter"), count = by("catalogCount");
  const empty = by("catalogEmpty"), more = by("catalogMore");
  if (!grid || !search || !country || !make || !power || !count) return;

  const markets = {japan:"ЯПОНИЯ", "south-korea":"ЮЖНАЯ КОРЕЯ", china:"КИТАЙ"};
  const rows = Object.entries(window.PAPAUTO_CATALOG || {}).flatMap(([market, data]) =>
    (Array.isArray(data) ? data : []).map(([brand, model, engine]) =>
      ({market,brand,model,engine:engine||"Характеристики уточняются"})));
  // Locally hosted, rights-verified real CC0 model photos (not auction lot photography). Never reuse one photo for
  // another model or claim the image shows a particular sold auction vehicle.
  const photoByModel = new Map([
    ["japan|honda|freed","/assets/demo/honda-freed-hybrid-cc0.webp"],
    ["japan|toyota|prius","/assets/demo/toyota-prius-cc0.webp"],
    ["south-korea|hyundai|staria","/assets/demo/hyundai-staria-cc0.webp"],
    ["china|geely|monjaro","/assets/demo/geely-monjaro-cc0.webp"],
    ["japan|toyota|aqua","/assets/demo/toyota-aqua-cc0.webp"],
    ["japan|toyota|vitz","/assets/demo/toyota-vitz-cc0.webp"],
    ["japan|toyota|yaris","/assets/demo/toyota-yaris-cc0.webp"],
    ["japan|toyota|corolla","/assets/demo/toyota-corolla-cc0.webp"],
    ["japan|honda|vezel","/assets/demo/honda-vezel-cc0.webp"],
    ["japan|nissan|march","/assets/demo/nissan-march-cc0.webp"],
    ["south-korea|hyundai|avante / elantra","/assets/demo/hyundai-avante-cc0.webp"],
    ["south-korea|kia|k5","/assets/demo/kia-k5-cc0.webp"],
    ["south-korea|kia|sportage","/assets/demo/kia-sportage-cc0.webp"],
    ["china|byd|dolphin","/assets/demo/byd-dolphin-cc0.webp"],
    ["china|byd|qin l","/assets/demo/byd-qin-l-cc0.webp"],
    ["china|geely|coolray / binyue","/assets/demo/geely-coolray-cc0.webp"],
    ["china|changan|uni-v","/assets/demo/changan-uni-v-cc0.webp"],
    ["china|changan|uni-t","/assets/demo/changan-uni-t-cc0.webp"],
    ["china|changan|uni-z","/assets/demo/changan-uni-z-cc0.webp"],
    ["china|zeekr|007","/assets/demo/zeekr-007-cc0.webp"],
    ["japan|toyota|sienta","/assets/demo/toyota-sienta-cc0.webp"],
    ["japan|honda|fit","/assets/demo/honda-fit-cc0.webp"],
    ["japan|nissan|note","/assets/demo/nissan-note-cc0.webp"],
    ["japan|nissan|serena","/assets/demo/nissan-serena-cc0.webp"],
    ["japan|mazda|cx-5","/assets/demo/mazda-cx5-cc0.webp"],
    ["south-korea|kia|seltos","/assets/demo/kia-seltos-cc0.webp"],
    ["south-korea|kia|sorento","/assets/demo/kia-sorento-cc0.webp"],
    ["china|byd|song plus","/assets/demo/byd-song-plus-cc0.webp"],
    ["china|haval|jolion","/assets/demo/haval-jolion-cc0.webp"],
    ["japan|toyota|rav4","/assets/demo/toyota-rav4-cc0.webp"],
    ["japan|toyota|noah","/assets/demo/toyota-noah-cc0.webp"],
    ["japan|toyota|alphard","/assets/demo/toyota-alphard-cc0.webp"],
    ["japan|honda|stepwgn","/assets/demo/honda-stepwgn-cc0.webp"],
    ["japan|honda|n-box","/assets/demo/honda-nbox-cc0.webp"],
    ["japan|subaru|forester","/assets/demo/subaru-forester-cc0.webp"],
    ["japan|suzuki|jimny","/assets/demo/suzuki-jimny-cc0.webp"],
    ["japan|nissan|sakura","/assets/demo/nissan-sakura-cc0.webp"],
    ["japan|honda|n-wgn","/assets/demo/honda-nwgn-cc0.webp"],
    ["japan|toyota|land cruiser","/assets/demo/toyota-land-cruiser-cc0.webp"],
    ["japan|toyota|crown","/assets/demo/toyota-crown-cc0.webp"],
    ["japan|daihatsu|tanto","/assets/demo/daihatsu-tanto-cc0.webp"],
    ["japan|nissan|dayz","/assets/demo/nissan-dayz-cc0.webp"],
    ["japan|toyota|probox","/assets/demo/toyota-probox-cc0.webp"],
    ["south-korea|hyundai|tucson","/assets/demo/hyundai-tucson-cc0.webp"],
    ["south-korea|hyundai|sonata","/assets/demo/hyundai-sonata-cc0.webp"],
    ["south-korea|hyundai|santa fe","/assets/demo/hyundai-santa-fe-cc0.webp"],
    ["south-korea|hyundai|palisade","/assets/demo/hyundai-palisade-cc0.webp"],
    ["south-korea|kia|ev6","/assets/demo/kia-ev6-cc0.webp"],
    ["south-korea|kia|carnival","/assets/demo/kia-carnival-cc0.webp"],
    ["south-korea|kia|k3 / cerato","/assets/demo/kia-cerato-cc0.webp"],
    ["china|geely|atlas / boyue","/assets/demo/geely-atlas-cc0.webp"],
    ["china|geely|emgrand","/assets/demo/geely-emgrand-cc0.webp"],
    ["china|byd|yuan plus / atto 3","/assets/demo/byd-atto3-cc0.webp"],
    ["china|zeekr|001","/assets/demo/zeekr-001-cc0.webp"],
    ["china|tank|300","/assets/demo/tank-300-cc0.webp"],
    ["china|changan|cs55 plus","/assets/demo/changan-cs55plus-cc0.webp"],
    ["china|chery|tiggo 7","/assets/demo/chery-tiggo7-cc0.webp"],
    ["china|gac|trumpchi gs8","/assets/demo/gac-gs8-cc0.webp"],
    ["japan|toyota|camry","/assets/demo/toyota-camry-cc0.webp"],
    ["japan|toyota|raize","/assets/demo/toyota-raize-cc0.webp"],
    ["japan|toyota|voxy","/assets/demo/toyota-voxy-cc0.webp"],
    ["japan|toyota|corolla cross","/assets/demo/toyota-corolla-cross-cc0.webp"],
    ["japan|toyota|c-hr","/assets/demo/toyota-chr-cc0.webp"],
    ["japan|honda|civic","/assets/demo/honda-civic-cc0.webp"],
    ["japan|honda|cr-v","/assets/demo/honda-crv-cc0.webp"],
    ["japan|honda|odyssey","/assets/demo/honda-odyssey-cc0.webp"],
    ["japan|nissan|leaf","/assets/demo/nissan-leaf-cc0.webp"],
    ["japan|nissan|x-trail","/assets/demo/nissan-xtrail-cc0.webp"],
    ["japan|suzuki|swift","/assets/demo/suzuki-swift-cc0.webp"],
    ["japan|suzuki|hustler","/assets/demo/suzuki-hustler-cc0.webp"],
    ["japan|suzuki|wagon r","/assets/demo/suzuki-wagonr-cc0.webp"],
    ["japan|subaru|impreza","/assets/demo/subaru-impreza-cc0.webp"],
    ["japan|suzuki|spacia","/assets/demo/suzuki-spacia-cc0.webp"],
    ["japan|daihatsu|taft","/assets/demo/daihatsu-taft-cc0.webp"],
    ["japan|mitsubishi|outlander","/assets/demo/mitsubishi-outlander-cc0.webp"],
    ["japan|mazda|mazda3","/assets/demo/mazda-mazda3-cc0.webp"],
    ["south-korea|hyundai|ioniq 5","/assets/demo/hyundai-ioniq5-cc0.webp"],
    ["south-korea|kia|ev9","/assets/demo/kia-ev9-cc0.webp"],
    ["south-korea|kia|soul","/assets/demo/kia-soul-cc0.webp"],
    ["south-korea|genesis|gv80","/assets/demo/genesis-gv80-cc0.webp"],
    ["south-korea|kia|stinger","/assets/demo/kia-stinger-cc0.webp"],
    ["south-korea|genesis|g80","/assets/demo/genesis-g80-cc0.webp"],
    ["south-korea|genesis|gv70","/assets/demo/genesis-gv70-cc0.webp"],
    ["south-korea|kia|niro","/assets/demo/kia-niro-cc0.webp"],
    ["china|byd|seagull","/assets/demo/byd-seagull-cc0.webp"],
    ["china|changan|cs75 plus","/assets/demo/changan-cs75-plus-cc0.webp"],
    ["china|geely|tugella","/assets/demo/geely-tugella-cc0.webp"],
    ["china|changan|uni-k","/assets/demo/changan-uni-k-cc0.webp"],
    ["china|xiaomi|su7","/assets/demo/xiaomi-su7-cc0.webp"],
    ["china|xiaomi|su7 ultra","/assets/demo/xiaomi-su7-ultra-cc0.webp"],
    ["china|geely|galaxy e5","/assets/demo/geely-galaxy-e5-cc0.webp"],
    ["china|aito|m7","/assets/demo/aito-m7-cc0.webp"],
    ["china|voyah|free","/assets/demo/voyah-free-cc0.webp"],
    ["china|gac|trumpchi m8","/assets/demo/gac-m8-cc0.webp"],
    ["china|chery|arrizo 8","/assets/demo/chery-arrizo8-cc0.webp"],
    ["china|chery|arrizo 8 pro","/assets/demo/chery-arrizo8-pro-cc0.webp"],
    ["china|byd|han ev","/assets/demo/byd-han-ev-cc0.webp"],
    ["china|chery|tiggo 8 pro","/assets/demo/chery-tiggo8-pro-cc0.webp"],
    ["china|tank|400","/assets/demo/tank-400-cc0.webp"],
    ["china|byd|seal 06","/assets/demo/byd-seal06-cc0.webp"],
    ["japan|toyota|bb","/assets/demo/japan-toyota-bb-cc0.webp"],
    ["japan|toyota|ist","/assets/demo/japan-toyota-ist-cc0.webp"],
    ["japan|toyota|tank","/assets/demo/japan-toyota-tank-cc0.webp"],
    ["japan|toyota|wish","/assets/demo/japan-toyota-wish-cc0.webp"],
    ["japan|toyota|hilux","/assets/demo/japan-toyota-hilux-cc0.webp"],
    ["japan|toyota|passo","/assets/demo/japan-toyota-passo-cc0.webp"],
    ["japan|toyota|roomy","/assets/demo/japan-toyota-roomy-cc0.webp"],
    ["japan|toyota|mark x","/assets/demo/japan-toyota-mark-x-cc0.webp"],
    ["japan|toyota|ractis","/assets/demo/japan-toyota-ractis-cc0.webp"],
    ["japan|toyota|caldina","/assets/demo/japan-toyota-caldina-cc0.webp"],
    ["japan|toyota|esquire","/assets/demo/japan-toyota-esquire-cc0.webp"],
    ["japan|toyota|harrier","/assets/demo/japan-toyota-harrier-cc0.webp"],
    ["japan|toyota|succeed","/assets/demo/japan-toyota-succeed-cc0.webp"],
    ["japan|toyota|gr yaris","/assets/demo/japan-toyota-gr-yaris-cc0.webp"],
    ["japan|toyota|gr corolla","/assets/demo/japan-toyota-gr-corolla-cc0.webp"],
    ["japan|toyota|crown sport","/assets/demo/japan-toyota-crown-sport-cc0.webp"],
    ["japan|toyota|pixis epoch","/assets/demo/japan-toyota-pixis-epoch-cc0.webp"],
    ["japan|toyota|yaris cross","/assets/demo/japan-toyota-yaris-cross-cc0.webp"],
    ["japan|toyota|corolla axio","/assets/demo/japan-toyota-corolla-axio-cc0.webp"],
    ["japan|toyota|crown hybrid","/assets/demo/japan-toyota-crown-hybrid-cc0.webp"],
    ["japan|toyota|corolla rumion","/assets/demo/japan-toyota-corolla-rumion-cc0.webp"],
    ["japan|toyota|corolla fielder","/assets/demo/japan-toyota-corolla-fielder-cc0.webp"],
    ["japan|toyota|corolla touring","/assets/demo/japan-toyota-corolla-touring-cc0.webp"],
    ["japan|toyota|crown crossover","/assets/demo/japan-toyota-crown-crossover-cc0.webp"],
    ["japan|honda|jade","/assets/demo/japan-honda-jade-cc0.webp"],
    ["japan|honda|jazz","/assets/demo/japan-honda-jazz-cc0.webp"],
    ["japan|honda|s660","/assets/demo/japan-honda-s660-cc0.webp"],
    ["japan|honda|wr-v","/assets/demo/japan-honda-wr-v-cc0.webp"],
    ["japan|honda|grace","/assets/demo/japan-honda-grace-cc0.webp"],
    ["japan|honda|n-one","/assets/demo/japan-honda-n-one-cc0.webp"],
    ["japan|honda|n-van","/assets/demo/japan-honda-n-van-cc0.webp"],
    ["japan|honda|accord","/assets/demo/japan-honda-accord-cc0.webp"],
    ["japan|honda|freed+","/assets/demo/japan-honda-freed-cc0.webp"],
    ["japan|honda|stream","/assets/demo/japan-honda-stream-cc0.webp"],
    ["japan|honda|insight","/assets/demo/japan-honda-insight-cc0.webp"],
    ["japan|honda|shuttle","/assets/demo/japan-honda-shuttle-cc0.webp"],
    ["japan|honda|fit shuttle","/assets/demo/japan-honda-fit-shuttle-cc0.webp"],
    ["japan|honda|n-box custom","/assets/demo/japan-honda-n-box-custom-cc0.webp"],
    ["japan|honda|vezel hybrid","/assets/demo/japan-honda-vezel-hybrid-cc0.webp"],
    ["japan|honda|stepwgn spada","/assets/demo/japan-honda-stepwgn-spada-cc0.webp"],
    ["japan|nissan|ad","/assets/demo/japan-nissan-ad-cc0.webp"],
    ["japan|nissan|cube","/assets/demo/japan-nissan-cube-cc0.webp"],
    ["japan|nissan|fuga","/assets/demo/japan-nissan-fuga-cc0.webp"],
    ["japan|nissan|juke","/assets/demo/japan-nissan-juke-cc0.webp"],
    ["japan|nissan|moco","/assets/demo/japan-nissan-moco-cc0.webp"],
    ["japan|nissan|roox","/assets/demo/japan-nissan-roox-cc0.webp"],
    ["japan|nissan|ariya","/assets/demo/japan-nissan-ariya-cc0.webp"],
    ["japan|nissan|kicks","/assets/demo/japan-nissan-kicks-cc0.webp"],
    ["japan|nissan|micra","/assets/demo/japan-nissan-micra-cc0.webp"],
    ["japan|nissan|nv200","/assets/demo/japan-nissan-nv200-cc0.webp"],
    ["japan|nissan|caravan","/assets/demo/japan-nissan-caravan-cc0.webp"],
    ["japan|nissan|elgrand","/assets/demo/japan-nissan-elgrand-cc0.webp"],
    ["japan|nissan|qashqai","/assets/demo/japan-nissan-qashqai-cc0.webp"],
    ["japan|nissan|skyline","/assets/demo/japan-nissan-skyline-cc0.webp"],
    ["japan|nissan|wingroad","/assets/demo/japan-nissan-wingroad-cc0.webp"],
    ["japan|nissan|dayz roox","/assets/demo/japan-nissan-dayz-roox-cc0.webp"],
    ["japan|nissan|fairlady z","/assets/demo/japan-nissan-fairlady-z-cc0.webp"],
    ["japan|nissan|note e-power","/assets/demo/japan-nissan-note-e-power-cc0.webp"],
    ["japan|nissan|nv100 clipper","/assets/demo/japan-nissan-nv100-clipper-cc0.webp"],
    ["japan|suzuki|alto","/assets/demo/japan-suzuki-alto-cc0.webp"],
    ["japan|suzuki|xbee","/assets/demo/japan-suzuki-xbee-cc0.webp"],
    ["japan|suzuki|every","/assets/demo/japan-suzuki-every-cc0.webp"],
    ["japan|suzuki|fronx","/assets/demo/japan-suzuki-fronx-cc0.webp"],
    ["japan|suzuki|ignis","/assets/demo/japan-suzuki-ignis-cc0.webp"],
    ["japan|suzuki|solio","/assets/demo/japan-suzuki-solio-cc0.webp"],
    ["japan|suzuki|escudo","/assets/demo/japan-suzuki-escudo-cc0.webp"],
    ["japan|suzuki|alto lapin","/assets/demo/japan-suzuki-alto-lapin-cc0.webp"],
    ["japan|suzuki|jimny nomade","/assets/demo/japan-suzuki-jimny-nomade-cc0.webp"],
    ["japan|suzuki|jimny sierra","/assets/demo/japan-suzuki-jimny-sierra-cc0.webp"],
    ["japan|suzuki|solio bandit","/assets/demo/japan-suzuki-solio-bandit-cc0.webp"],
    ["japan|suzuki|spacia custom","/assets/demo/japan-suzuki-spacia-custom-cc0.webp"],
    ["japan|suzuki|wagon r smile","/assets/demo/japan-suzuki-wagon-r-smile-cc0.webp"],
    ["japan|suzuki|hustler hybrid","/assets/demo/japan-suzuki-hustler-hybrid-cc0.webp"],
    ["japan|mazda|cx-3","/assets/demo/japan-mazda-cx-3-cc0.webp"],
    ["japan|mazda|axela","/assets/demo/japan-mazda-axela-cc0.webp"],
    ["south-korea|hyundai|h-1","/assets/demo/south-korea-hyundai-h-1-cc0.webp"],
    ["south-korea|hyundai|i20","/assets/demo/south-korea-hyundai-i20-cc0.webp"],
    ["south-korea|hyundai|i30","/assets/demo/south-korea-hyundai-i30-cc0.webp"],
    ["south-korea|hyundai|kona","/assets/demo/south-korea-hyundai-kona-cc0.webp"],
    ["south-korea|hyundai|nexo","/assets/demo/south-korea-hyundai-nexo-cc0.webp"],
    ["south-korea|hyundai|creta","/assets/demo/south-korea-hyundai-creta-cc0.webp"],
    ["south-korea|hyundai|equus","/assets/demo/south-korea-hyundai-equus-cc0.webp"],
    ["south-korea|hyundai|ioniq","/assets/demo/south-korea-hyundai-ioniq-cc0.webp"],
    ["south-korea|hyundai|venue","/assets/demo/south-korea-hyundai-venue-cc0.webp"],
    ["south-korea|hyundai|ioniq 6","/assets/demo/south-korea-hyundai-ioniq-6-cc0.webp"],
    ["south-korea|hyundai|ioniq 9","/assets/demo/south-korea-hyundai-ioniq-9-cc0.webp"],
    ["south-korea|hyundai|veloster","/assets/demo/south-korea-hyundai-veloster-cc0.webp"],
    ["south-korea|hyundai|grand starex","/assets/demo/south-korea-hyundai-grand-starex-cc0.webp"],
    ["south-korea|kia|k3","/assets/demo/south-korea-kia-k3-cc0.webp"],
    ["south-korea|kia|ev5","/assets/demo/south-korea-kia-ev5-cc0.webp"],
    ["south-korea|kia|ceed","/assets/demo/south-korea-kia-ceed-cc0.webp"],
    ["south-korea|kia|carens","/assets/demo/south-korea-kia-carens-cc0.webp"],
    ["south-korea|kia|niro ev","/assets/demo/south-korea-kia-niro-ev-cc0.webp"],
    ["south-korea|kia|morning / picanto","/assets/demo/south-korea-kia-morning-picanto-cc0.webp"],
    ["south-korea|genesis|gv60","/assets/demo/south-korea-genesis-gv60-cc0.webp"],
    ["south-korea|ssangyong|musso","/assets/demo/south-korea-ssangyong-musso-cc0.webp"],
    ["south-korea|ssangyong|actyon","/assets/demo/south-korea-ssangyong-actyon-cc0.webp"],
    ["south-korea|ssangyong|rexton","/assets/demo/south-korea-ssangyong-rexton-cc0.webp"],
    ["south-korea|ssangyong|tivoli","/assets/demo/south-korea-ssangyong-tivoli-cc0.webp"],
    ["south-korea|ssangyong|korando","/assets/demo/south-korea-ssangyong-korando-cc0.webp"],
    ["south-korea|bmw|x1","/assets/demo/south-korea-bmw-x1-cc0.webp"],
    ["south-korea|bmw|i4","/assets/demo/south-korea-bmw-i4-cc0.webp"],
    ["south-korea|bmw|1 series","/assets/demo/south-korea-bmw-1-series-cc0.webp"],
    ["south-korea|bmw|2 series","/assets/demo/south-korea-bmw-2-series-cc0.webp"],
    ["south-korea|mercedes-benz|eqa","/assets/demo/south-korea-mercedes-benz-eqa-cc0.webp"],
    ["south-korea|mercedes-benz|eqe","/assets/demo/south-korea-mercedes-benz-eqe-cc0.webp"],
    ["south-korea|mercedes-benz|a-class","/assets/demo/south-korea-mercedes-benz-a-class-cc0.webp"],
    ["south-korea|mercedes-benz|g-class","/assets/demo/south-korea-mercedes-benz-g-class-cc0.webp"],
    ["south-korea|mercedes-benz|v-class","/assets/demo/south-korea-mercedes-benz-v-class-cc0.webp"],
    ["south-korea|mercedes-benz|gle-class","/assets/demo/south-korea-mercedes-benz-gle-class-cc0.webp"],
    ["south-korea|audi|a3","/assets/demo/south-korea-audi-a3-cc0.webp"],
    ["south-korea|audi|a7","/assets/demo/south-korea-audi-a7-cc0.webp"],
    ["south-korea|audi|a8","/assets/demo/south-korea-audi-a8-cc0.webp"],
    ["south-korea|volkswagen|passat","/assets/demo/south-korea-volkswagen-passat-cc0.webp"],
    ["south-korea|porsche|911","/assets/demo/south-korea-porsche-911-cc0.webp"],
    ["south-korea|porsche|macan","/assets/demo/south-korea-porsche-macan-cc0.webp"],
    ["south-korea|porsche|panamera","/assets/demo/south-korea-porsche-panamera-cc0.webp"],
    ["china|byd|e2","/assets/demo/china-byd-e2-cc0.webp"],
    ["china|byd|seal","/assets/demo/china-byd-seal-cc0.webp"],
    ["china|byd|song l","/assets/demo/china-byd-song-l-cc0.webp"],
    ["china|byd|qin plus","/assets/demo/china-byd-qin-plus-cc0.webp"],
    ["china|byd|song pro","/assets/demo/china-byd-song-pro-cc0.webp"],
    ["china|byd|song l ev","/assets/demo/china-byd-song-l-ev-cc0.webp"],
    ["china|byd|yuan plus","/assets/demo/china-byd-yuan-plus-cc0.webp"],
    ["china|byd|seal 06 gt","/assets/demo/china-byd-seal-06-gt-cc0.webp"],
    ["china|byd|seal 05 dm-i","/assets/demo/china-byd-seal-05-dm-i-cc0.webp"],
    ["china|byd|qin plus dm-i","/assets/demo/china-byd-qin-plus-dm-i-cc0.webp"],
    ["china|byd|sea lion 07 ev","/assets/demo/china-byd-sea-lion-07-ev-cc0.webp"],
    ["china|byd|song plus dm-i","/assets/demo/china-byd-song-plus-dm-i-cc0.webp"],
    ["china|geely|panda","/assets/demo/china-geely-panda-cc0.webp"],
    ["china|geely|binrui","/assets/demo/china-geely-binrui-cc0.webp"],
    ["china|geely|boyue l","/assets/demo/china-geely-boyue-l-cc0.webp"],
    ["china|geely|cityray","/assets/demo/china-geely-cityray-cc0.webp"],
    ["china|geely|preface","/assets/demo/china-geely-preface-cc0.webp"],
    ["china|geely|emgrand l","/assets/demo/china-geely-emgrand-l-cc0.webp"],
    ["china|geely|galaxy e8","/assets/demo/china-geely-galaxy-e8-cc0.webp"],
    ["china|geely|galaxy l6","/assets/demo/china-geely-galaxy-l6-cc0.webp"],
    ["china|geely|galaxy l7","/assets/demo/china-geely-galaxy-l7-cc0.webp"],
    ["china|geely|galaxy m9","/assets/demo/china-geely-galaxy-m9-cc0.webp"],
    ["china|geely|galaxy starship 7","/assets/demo/china-geely-galaxy-starship-7-cc0.webp"],
    ["china|changan|eado","/assets/demo/china-changan-eado-cc0.webp"],
    ["china|changan|alsvin","/assets/demo/china-changan-alsvin-cc0.webp"],
    ["china|changan|cs35 plus","/assets/demo/china-changan-cs35-plus-cc0.webp"],
    ["china|changan|raeton plus","/assets/demo/china-changan-raeton-plus-cc0.webp"],
    ["china|chery|omoda 5","/assets/demo/china-chery-omoda-5-cc0.webp"],
    ["china|chery|tiggo 9","/assets/demo/china-chery-tiggo-9-cc0.webp"],
    ["china|chery|arrizo 5","/assets/demo/china-chery-arrizo-5-cc0.webp"],
    ["china|chery|tiggo 5x","/assets/demo/china-chery-tiggo-5x-cc0.webp"],
    ["china|chery|tiggo 7 plus","/assets/demo/china-chery-tiggo-7-plus-cc0.webp"],
    ["china|chery|tiggo 8 plus","/assets/demo/china-chery-tiggo-8-plus-cc0.webp"],
    ["china|haval|f7","/assets/demo/china-haval-f7-cc0.webp"],
    ["china|haval|h6","/assets/demo/china-haval-h6-cc0.webp"],
    ["china|haval|h7","/assets/demo/china-haval-h7-cc0.webp"],
    ["china|haval|h9","/assets/demo/china-haval-h9-cc0.webp"],
    ["china|haval|m6","/assets/demo/china-haval-m6-cc0.webp"],
    ["china|haval|f7x","/assets/demo/china-haval-f7x-cc0.webp"],
    ["china|haval|raptor","/assets/demo/china-haval-raptor-cc0.webp"],
    ["china|haval|big dog / dargo","/assets/demo/china-haval-big-dog-dargo-cc0.webp"],
    ["china|gac|gs3","/assets/demo/china-gac-gs3-cc0.webp"],
    ["china|gac|aion y","/assets/demo/china-gac-aion-y-cc0.webp"],
    ["china|gac|trumpchi e8","/assets/demo/china-gac-trumpchi-e8-cc0.webp"],
    ["china|zeekr|7x","/assets/demo/china-zeekr-7x-cc0.webp"],
    ["china|zeekr|9x","/assets/demo/china-zeekr-9x-cc0.webp"],
    ["china|zeekr|009","/assets/demo/china-zeekr-009-cc0.webp"],
    ["china|zeekr|mix","/assets/demo/china-zeekr-mix-cc0.webp"],
    ["china|tank|500","/assets/demo/china-tank-500-cc0.webp"],
    ["china|tank|700","/assets/demo/china-tank-700-cc0.webp"],
    ["china|xiaomi|yu7","/assets/demo/china-xiaomi-yu7-cc0.webp"],
    ["china|aito|m6","/assets/demo/china-aito-m6-cc0.webp"],
    ["china|aito|m8","/assets/demo/china-aito-m8-cc0.webp"],
    ["china|aito|m9","/assets/demo/china-aito-m9-cc0.webp"],
    ["china|voyah|dream","/assets/demo/china-voyah-dream-cc0.webp"],
    ["china|voyah|courage","/assets/demo/china-voyah-courage-cc0.webp"],
    ["china|voyah|passion","/assets/demo/china-voyah-passion-cc0.webp"],
    ["china|hongqi|h5","/assets/demo/china-hongqi-h5-cc0.webp"],
    ["china|hongqi|h9","/assets/demo/china-hongqi-h9-cc0.webp"],
    ["china|hongqi|hq9","/assets/demo/china-hongqi-hq9-cc0.webp"],
    ["china|hongqi|hs5","/assets/demo/china-hongqi-hs5-cc0.webp"],
    ["china|hongqi|hs7","/assets/demo/china-hongqi-hs7-cc0.webp"],
    ["china|hongqi|e-hs9","/assets/demo/china-hongqi-e-hs9-cc0.webp"],
    ["china|jetour|x90","/assets/demo/china-jetour-x90-cc0.webp"],
    ["china|jetour|dashing","/assets/demo/china-jetour-dashing-cc0.webp"],
    ["china|jetour|x70 plus","/assets/demo/china-jetour-x70-plus-cc0.webp"],
    ["china|jetour|x90 plus","/assets/demo/china-jetour-x90-plus-cc0.webp"],
    ["china|jetour|shanhai t1","/assets/demo/china-jetour-shanhai-t1-cc0.webp"],
    ["china|exeed|lx","/assets/demo/china-exeed-lx-cc0.webp"],
    ["china|exeed|rx","/assets/demo/china-exeed-rx-cc0.webp"],
    ["china|exeed|vx","/assets/demo/china-exeed-vx-cc0.webp"],
    ["china|exeed|et5","/assets/demo/china-exeed-et5-cc0.webp"],
    ["china|exeed|txl","/assets/demo/china-exeed-txl-cc0.webp"],
    ["china|avatr|06","/assets/demo/china-avatr-06-cc0.webp"],
    ["china|avatr|07","/assets/demo/china-avatr-07-cc0.webp"],
    ["japan|mazda|cx-30","/assets/demo/japan-mazda-cx-30-cc0.webp"],
    ["japan|mazda|cx-60","/assets/demo/japan-mazda-cx-60-cc0.webp"],
    ["japan|mazda|cx-80","/assets/demo/japan-mazda-cx-80-cc0.webp"],
    ["japan|mazda|carol","/assets/demo/japan-mazda-carol-cc0.webp"],
    ["japan|mazda|demio","/assets/demo/japan-mazda-demio-cc0.webp"],
    ["japan|mazda|atenza","/assets/demo/japan-mazda-atenza-cc0.webp"],
    ["japan|mazda|biante","/assets/demo/japan-mazda-biante-cc0.webp"],
    ["japan|mazda|verisa","/assets/demo/japan-mazda-verisa-cc0.webp"],
    ["japan|mazda|roadster","/assets/demo/japan-mazda-roadster-cc0.webp"],
    ["japan|mazda|axela sport","/assets/demo/japan-mazda-axela-sport-cc0.webp"],
    ["japan|mazda|flair wagon","/assets/demo/japan-mazda-flair-wagon-cc0.webp"],
    ["japan|subaru|xv","/assets/demo/japan-subaru-xv-cc0.webp"],
    ["japan|subaru|brz","/assets/demo/japan-subaru-brz-cc0.webp"],
    ["japan|subaru|wrx","/assets/demo/japan-subaru-wrx-cc0.webp"],
    ["japan|subaru|exiga","/assets/demo/japan-subaru-exiga-cc0.webp"],
    ["japan|subaru|justy","/assets/demo/japan-subaru-justy-cc0.webp"],
    ["japan|subaru|legacy","/assets/demo/japan-subaru-legacy-cc0.webp"],
    ["japan|subaru|levorg","/assets/demo/japan-subaru-levorg-cc0.webp"],
    ["japan|subaru|sambar","/assets/demo/japan-subaru-sambar-cc0.webp"],
    ["japan|subaru|stella","/assets/demo/japan-subaru-stella-cc0.webp"],
    ["japan|daihatsu|boon","/assets/demo/japan-daihatsu-boon-cc0.webp"],
    ["japan|daihatsu|cast","/assets/demo/japan-daihatsu-cast-cc0.webp"],
    ["japan|daihatsu|move","/assets/demo/japan-daihatsu-move-cc0.webp"],
    ["japan|daihatsu|thor","/assets/demo/japan-daihatsu-thor-cc0.webp"],
    ["japan|daihatsu|wake","/assets/demo/japan-daihatsu-wake-cc0.webp"],
    ["japan|daihatsu|atrai","/assets/demo/japan-daihatsu-atrai-cc0.webp"],
    ["japan|daihatsu|copen","/assets/demo/japan-daihatsu-copen-cc0.webp"],
    ["japan|daihatsu|rocky","/assets/demo/japan-daihatsu-rocky-cc0.webp"],
    ["japan|daihatsu|mira e:s","/assets/demo/japan-daihatsu-mira-e-s-cc0.webp"],
    ["japan|daihatsu|mira cocoa","/assets/demo/japan-daihatsu-mira-cocoa-cc0.webp"],
    ["japan|daihatsu|hijet cargo","/assets/demo/japan-daihatsu-hijet-cargo-cc0.webp"],
    ["japan|daihatsu|hijet truck","/assets/demo/japan-daihatsu-hijet-truck-cc0.webp"],
    ["japan|daihatsu|move canbus","/assets/demo/japan-daihatsu-move-canbus-cc0.webp"],
    ["japan|mitsubishi|rvr","/assets/demo/japan-mitsubishi-rvr-cc0.webp"],
    ["japan|mitsubishi|ek x","/assets/demo/japan-mitsubishi-ek-x-cc0.webp"],
    ["japan|mitsubishi|pajero","/assets/demo/japan-mitsubishi-pajero-cc0.webp"],
    ["japan|mitsubishi|ek x ev","/assets/demo/japan-mitsubishi-ek-x-ev-cc0.webp"],
    ["japan|mitsubishi|ek space","/assets/demo/japan-mitsubishi-ek-space-cc0.webp"],
    ["japan|mitsubishi|ek wagon","/assets/demo/japan-mitsubishi-ek-wagon-cc0.webp"],
    ["japan|mitsubishi|delica d:2","/assets/demo/japan-mitsubishi-delica-d-2-cc0.webp"],
    ["japan|mitsubishi|delica d:5","/assets/demo/japan-mitsubishi-delica-d-5-cc0.webp"],
    ["japan|mitsubishi|delica mini","/assets/demo/japan-mitsubishi-delica-mini-cc0.webp"],
    ["japan|mitsubishi|eclipse cross","/assets/demo/japan-mitsubishi-eclipse-cross-cc0.webp"],
    ["japan|lexus|lbx","/assets/demo/japan-lexus-lbx-cc0.webp"],
    ["japan|lexus|gx 550","/assets/demo/japan-lexus-gx-550-cc0.webp"],
    ["china|avatr|11","/assets/demo/china-avatr-11-cc0.webp"],
    ["china|avatr|12","/assets/demo/china-avatr-12-cc0.webp"],
    ["china|deepal|s05","/assets/demo/china-deepal-s05-cc0.webp"],
    ["china|deepal|g318","/assets/demo/china-deepal-g318-cc0.webp"],
    ["china|leapmotor|c10","/assets/demo/china-leapmotor-c10-cc0.webp"],
    ["china|wuling|bingo","/assets/demo/china-wuling-bingo-cc0.webp"],
    ["china|wuling|starlight","/assets/demo/china-wuling-starlight-cc0.webp"],
    ["china|wuling|hongguang mini ev","/assets/demo/china-wuling-hongguang-mini-ev-cc0.webp"],
    ["china|lynk & co|01","/assets/demo/china-lynk-co-01-cc0.webp"],
    ["china|lynk & co|03","/assets/demo/china-lynk-co-03-cc0.webp"],
    ["china|lynk & co|09","/assets/demo/china-lynk-co-09-cc0.webp"],
    ["china|lynk & co|900","/assets/demo/china-lynk-co-900-cc0.webp"],
    ["china|lynk & co|08 em-p","/assets/demo/china-lynk-co-08-em-p-cc0.webp"],
    ["china|bmw|x2","/assets/demo/china-bmw-x2-cc0.webp"],
    ["china|mazda|cx-30","/assets/demo/china-mazda-cx-30-cc0.webp"],
    ["china|toyota|camry","/assets/demo/china-toyota-camry-cc0.webp"],
    ["china|honda|civic","/assets/demo/china-honda-civic-cc0.webp"],
    ["china|volkswagen|tharu","/assets/demo/china-volkswagen-tharu-cc0.webp"],
    ["china|toyota|venza","/assets/demo/china-toyota-venza-cc0.webp"],
    ["china|honda|breeze","/assets/demo/china-honda-breeze-cc0.webp"],
    ["china|volkswagen|lavida","/assets/demo/china-volkswagen-lavida-cc0.webp"],
    ["china|nissan|sylphy","/assets/demo/china-nissan-sylphy-cc0.webp"],
    ["china|volkswagen|tayron","/assets/demo/china-volkswagen-tayron-cc0.webp"],
    ["china|toyota|corolla","/assets/demo/china-toyota-corolla-cc0.webp"],
    ["china|volkswagen|magotan","/assets/demo/china-volkswagen-magotan-cc0.webp"],
    ["china|honda|odyssey","/assets/demo/china-honda-odyssey-cc0.webp"],
    ["china|nissan|qashqai","/assets/demo/china-nissan-qashqai-cc0.webp"],
    ["china|volkswagen|sagitar","/assets/demo/china-volkswagen-sagitar-cc0.webp"],
    ["china|buick|envision","/assets/demo/china-buick-envision-cc0.webp"],
    ["china|toyota|highlander","/assets/demo/china-toyota-highlander-cc0.webp"]
  ]);
  const photoDetail = {
    "japan|honda|freed":"demo-freed-jp",
    "japan|toyota|prius":"demo-prius-jp",
    "south-korea|hyundai|staria":"demo-staria-kr",
    "china|geely|monjaro":"demo-monjaro-cn"
  };
  const lower = value => String(value||"").normalize("NFKC").toLocaleLowerCase("ru").trim();
  const keyOf = r => [r.market,lower(r.brand),lower(r.model)].join("|");
  const isElectric = r => /электро|electric|\bev\b/i.test(r.engine);
  const label = (tag,value,css) => {
    const e=document.createElement(tag);
    if(value!==undefined)e.textContent=String(value);
    if(css)e.className=css;
    return e;
  };
  // Show all one hundred photo-backed model cards on initial catalog load.
  const pageSize = 120;
  let limit = pageSize;

  function fillMakes(){
    const selected=make.value;
    const brands=[...new Set(rows.filter(r=>!country.value||r.market===country.value).map(r=>r.brand))]
      .sort((a,b)=>a.localeCompare(b,"ru"));
    make.replaceChildren(label("option","Все марки"));
    make.firstChild.value="";
    for(const brand of brands){
      const option=label("option",brand);option.value=brand;make.append(option);
    }
    if(brands.includes(selected))make.value=selected;
    else make.value="";
  }
  function render(){
    const q=lower(search.value);
    const selectedMake=lower(make.value);
    const matched=rows.filter(r=>
      (!country.value||country.value===r.market) &&
      (!selectedMake||selectedMake===lower(r.brand)) &&
      (!q||lower(r.brand+" "+r.model+" "+r.engine).includes(q)) &&
      (!power.value||(power.value==="ev"?isElectric(r):!isElectric(r)))
    );
    // Photograph-backed cards first, then alphabetically by brand/model.
    matched.sort((a,b)=>Number(photoByModel.has(keyOf(b)))-Number(photoByModel.has(keyOf(a)))
      ||a.brand.localeCompare(b.brand,"ru")||a.model.localeCompare(b.model,"ru"));
    grid.replaceChildren();
    for(const r of matched.slice(0,limit)){
      const card=label("article",undefined,"model-card");
      const localPhoto=photoByModel.get(keyOf(r));
      if(localPhoto){
        const frame=label("div",undefined,"model-photo");
        const img=label("img");
        img.src=localPhoto;
        img.alt=r.brand+" "+r.model+" — фотография модели, не конкретного лота";
        img.width=900; img.height=600; img.loading="lazy";img.decoding="async";
        img.addEventListener("load",()=>img.classList.add("loaded"),{once:true});
        img.addEventListener("error",()=>{frame.remove();},{once:true});
        frame.append(img,label("span","ФОТО МОДЕЛИ"));card.append(frame);
      }
      card.append(label("small",markets[r.market]||r.market,"country"),
        label("h2",r.brand+" "+r.model),
        label("div",r.engine,"engine"));
      const detailedExample=photoDetail[keyOf(r)];
      const a=label("a",detailedExample?"Фото и расчёт →":"Рассчитать подбор →","model-request");
      a.href=detailedExample?"/auction-archive.html#"+detailedExample: "/?view=select&similar="+encodeURIComponent(r.brand+" "+r.model)+"#assistant";
      card.append(a);grid.append(card);
    }
    count.textContent="Моделей в справочнике: "+matched.length+
      " · настоящих фотографий моделей: "+photoByModel.size+
      " · фотографии с проверенными правами на коммерческое использование";
    if(empty)empty.style.display=matched.length?"none":"block";
    if(more)more.hidden=matched.length<=limit;
  }
  country.addEventListener("change",()=>{limit=pageSize;fillMakes();render()});
  make.addEventListener("change",()=>{limit=pageSize;render()});
  search.addEventListener("input",()=>{limit=pageSize;render()});
  power.addEventListener("change",()=>{limit=pageSize;render()});
  if(more)more.addEventListener("click",()=>{limit+=pageSize;render()});
  fillMakes();
  render();
})();
(() => {
  "use strict";
  const catalog = {
    japan: [
      ["Toyota","Aqua","1.5 л"],["Toyota","Prius","1.5–1.8 л"],["Toyota","Yaris","1.0–1.5 л"],["Toyota","Vitz","1.0–1.5 л"],["Toyota","Passo","1.0–1.3 л"],["Toyota","Roomy","1.0 л"],["Toyota","Tank","1.0 л"],["Toyota","Raize","1.0–1.2 л"],["Toyota","Probox","1.3–1.5 л"],["Toyota","Succeed","1.5 л"],["Toyota","Sienta","1.5 л"],["Toyota","Corolla Fielder","1.5 л"],["Toyota","Corolla Axio","1.5 л"],["Toyota","Corolla","1.5 л"],["Toyota","C-HR","1.2 л"],["Toyota","Yaris Cross","1.5 л"],["Toyota","bB","1.3–1.5 л"],["Toyota","Ractis","1.3–1.5 л"],["Toyota","Vitz","1.0–1.5 л"],["Toyota","Pixis Epoch","0.66 л"],["Toyota","Pixis Joy","0.66 л"],["Toyota","Pixis Mega","0.66 л"],
      ["Honda","Fit","1.3–1.5 л"],["Honda","Jazz","1.3–1.5 л"],["Honda","Freed","1.5 л"],["Honda","Freed+","1.5 л"],["Honda","Vezel","1.5 л"],["Honda","Shuttle","1.5 л"],["Honda","Grace","1.5 л"],["Honda","N-BOX","0.66 л"],["Honda","N-WGN","0.66 л"],["Honda","N-ONE","0.66 л"],["Honda","N-VAN","0.66 л"],["Honda","WR-V","1.5 л"],
      ["Nissan","Note","1.2–1.5 л"],["Nissan","Note e-POWER","1.2 л"],["Nissan","March","1.2–1.5 л"],["Nissan","Micra","1.2–1.5 л"],["Nissan","Juke","1.5–1.6 л (проверять версию)"],["Nissan","Qashqai","1.5 л (редкие версии; проверять рынок)"],["Nissan","Dayz","0.66 л"],["Nissan","Roox","0.66 л"],["Nissan","Moco","0.66 л"],["Nissan","Cube","1.5 л"],["Nissan","AD","1.5 л"],["Nissan","NV200","1.6 л (вне лимита 1.5)"],
      ["Mazda","Demio","1.3–1.5 л"],["Mazda","Mazda2","1.5 л"],["Mazda","CX-3","1.5 л"],["Mazda","Axela","1.5 л"],["Mazda","Verisa","1.5 л"],
      ["Suzuki","Swift","1.2–1.5 л"],["Suzuki","Solio","1.2 л"],["Suzuki","Solio Bandit","1.2 л"],["Suzuki","Ignis","1.2 л"],["Suzuki","Hustler","0.66 л"],["Suzuki","Wagon R","0.66 л"],["Suzuki","Spacia","0.66 л"],["Suzuki","Alto","0.66 л"],["Suzuki","Jimny","0.66 л"],["Suzuki","Xbee","1.0 л"],
      ["Daihatsu","Tanto","0.66 л"],["Daihatsu","Move","0.66 л"],["Daihatsu","Mira e:S","0.66 л"],["Daihatsu","Wake","0.66 л"],["Daihatsu","Thor","1.0 л"],["Daihatsu","Rocky","1.0 л"],["Mitsubishi","eK Wagon","0.66 л"],["Mitsubishi","eK X","0.66 л"],["Mitsubishi","Delica D:2","1.2 л"],["Subaru","Justy","1.0 л"],["Subaru","Stella","0.66 л"]
    ],
    "south-korea": [
      ["Hyundai","Avante / Elantra","1.6–2.0 л"],["Hyundai","Sonata","1.6–2.0 л"],["Hyundai","Kona","1.6–2.0 л"],["Hyundai","Venue","1.6 л"],["Hyundai","Tucson","1.6–2.0 л"],["Hyundai","Creta","1.6–2.0 л"],["Hyundai","Santa Fe","2.0 л (отдельные версии)"],["Hyundai","i30","1.4–2.0 л"],["Hyundai","i20","1.0–1.4 л"],["Hyundai","Bayon","1.0–1.4 л"],["Hyundai","Casper","1.0 л"],["Hyundai","Accent","1.4–1.6 л"],["Hyundai","Grandeur","2.0 л (отдельные версии)"],
      ["Kia","K3 / Cerato","1.6–2.0 л"],["Kia","K5","1.6–2.0 л"],["Kia","Seltos","1.6–2.0 л"],["Kia","Sportage","1.6–2.0 л"],["Kia","Niro","1.6 л hybrid"],["Kia","Soul","1.6–2.0 л"],["Kia","Stonic","1.0–1.4 л"],["Kia","Ceed","1.0–1.6 л"],["Kia","Morning / Picanto","1.0–1.2 л"],["Kia","Ray","1.0 л"],["Kia","Forte","1.6–2.0 л"],["Kia","KX3","1.6 л"],["Kia","Carens","1.5–2.0 л"],
      ["Genesis","G70","2.0 л (отдельные версии)"],["Chevrolet Korea","Trax","1.4–1.6 л"],["Renault Korea","XM3 / Arkana","1.3–1.6 л"],["Renault Korea","SM3","1.6–2.0 л"],["SsangYong","Tivoli","1.5–1.6 л"],["SsangYong","Korando","1.5–1.6 л"]
    ],
    china: [
      ["BYD","Qin Plus","1.5 л / DM-i"],["BYD","Qin L","1.5 л / DM-i"],["BYD","Destroyer 05","1.5 л DM-i"],["BYD","Song Pro","1.5 л / DM-i"],["BYD","Song Plus","1.5 л DM-i / EV"],["BYD","Song L","1.5 л hybrid / EV"],["BYD","Yuan Plus / Atto 3","электро"],["BYD","Dolphin","электро"],["BYD","Seagull","электро"],["BYD","Seal 06","1.5 л DM-i"],["BYD","Chaser 05","1.5 л DM-i"],["BYD","e2","электро"],
      ["Geely","Emgrand","1.5 л"],["Geely","Coolray / Binyue","1.5 л"],["Geely","Atlas / Boyue","1.5–2.0 л"],["Geely","Cityray","1.5 л"],["Geely","Binrui","1.5 л"],["Geely","Galaxy L6","1.5 л hybrid"],["Geely","Galaxy E5","электро"],["Geely","Geometry C","электро"],
      ["Chery","Tiggo 4","1.5–1.6 л"],["Chery","Tiggo 5x","1.5 л"],["Chery","Tiggo 7","1.5–1.6 л"],["Chery","Arrizo 5","1.5 л"],["Chery","Arrizo 8","1.6 л"],["Chery","Omoda 5","1.5 л"],["Chery","Jetour Dashing","1.5–1.6 л"],["Chery","Jetour X70","1.5–1.6 л"],
      ["Haval","Jolion","1.5 л"],["Haval","H6","1.5–2.0 л"],["Haval","Big Dog / Dargo","1.5–2.0 л"],["Haval","M6","1.5 л"],["Haval","Chitu","1.5 л"],["Haval","H4","1.5–2.0 л"],
      ["Changan","CS35 Plus","1.4–1.6 л"],["Changan","CS55 Plus","1.5 л"],["Changan","CS75 Plus","1.5–2.0 л"],["Changan","UNI-T","1.5 л"],["Changan","UNI-V","1.5 л"],["Changan","Eado","1.4–1.6 л"],["Changan","Alsvin","1.4 л"],["Changan","Lumin","электро"],
      ["GAC","GS3","1.5 л"],["GAC","Empow","1.5 л"],["GAC","Aion Y","электро"],["GAC","Aion S","электро"],
      ["Wuling","Bingo","электро"],["Wuling","Hongguang Mini EV","электро"],["Wuling","Starlight","1.5 л PHEV"],["Leapmotor","T03","электро"],["Leapmotor","C10","электро / range extender"],
      ["Volkswagen","Lavida","1.5 л"],["Volkswagen","Sagitar","1.2–1.5 л"],["Volkswagen","Golf","1.4–1.5 л"],["Volkswagen","T-Cross","1.5 л"],["Volkswagen","T-Roc","1.4–2.0 л (проверять версию)"],["Volkswagen","Tharu","1.4–2.0 л (проверять версию)"],["Toyota","Corolla","1.2–1.8 л"],["Toyota","Levin","1.2–1.8 л"],["Toyota","Frontlander","2.0 л"],["Toyota","C-HR","1.2–2.0 л (проверять версию)"],["Honda","Civic","1.5 л"],["Honda","Breeze","1.5–2.0 л"],["Honda","XR-V","1.5 л"],["Honda","Fit","1.5 л"],["Honda","Crider","1.0–1.5 л"],["Honda","HR-V","1.5 л"],["Nissan","Sylphy","1.6 л"],["Nissan","Qashqai","1.3–2.0 л"],["Nissan","Kicks","1.5 л"],["Mazda","CX-30","2.0 л"],["Mazda","Mazda3","2.0 л"],["BMW","X1","1.5–2.0 л"],["BMW","X2","1.5–2.0 л"],["Audi","Q3","1.4–2.0 л"],["Buick","Excelle GT","1.5 л"],["Buick","Envision","1.5–2.0 л"]
    ]
  };
  window.PAPAUTO_CATALOG = catalog;
  const country = document.getElementById("vehicleCountry");
  const make = document.getElementById("vehicleMake");
  const model = document.getElementById("vehicleModel");
  if (!country || !make || !model) return;
  const makeList = document.createElement("datalist"); makeList.id = "papautoMakes";
  const modelList = document.createElement("datalist"); modelList.id = "papautoModels";
  document.body.append(makeList, modelList);
  make.setAttribute("list", makeList.id); model.setAttribute("list", modelList.id);
  const render = () => {
    const rows = catalog[country.value] || [];
    const makes = [...new Set(rows.map(row => row[0]))].sort((a,b)=>a.localeCompare(b,"ru"));
    makeList.replaceChildren(...makes.map(name => { const o=document.createElement("option");o.value=name;return o; }));
    const chosenMake = make.value.trim().toLocaleLowerCase("ru");
    const models = rows.filter(row => !chosenMake || row[0].toLocaleLowerCase("ru") === chosenMake);
    modelList.replaceChildren(...models.map(row => { const o=document.createElement("option");o.value=row[1];o.label=row[0]+" · "+row[2];return o; }));
  };
  country.addEventListener("change", () => { make.value=""; model.value=""; render(); });
  make.addEventListener("input", render);
  render();
})();
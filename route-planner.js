(()=>{"use strict";
const $=id=>document.getElementById(id),mapNode=$("papautoRouteMap");
if(!mapNode||!window.L)return;
const cities={
"Новосибирск":[55.0084,82.9357],"Красноярск":[56.0153,92.8932],"Иркутск":[52.2864,104.2807],"Омск":[54.9885,73.3242],"Кемерово":[55.3547,86.0873],"Томск":[56.5010,84.9925],"Барнаул":[53.3474,83.7784],"Москва":[55.7558,37.6173],"Екатеринбург":[56.8389,60.6057],"Казань":[55.7961,49.1064],"Владивосток":[43.1155,131.8855]};
const origins={"japan":{name:"Йокогама",coords:[35.4437,139.6380]},"south-korea":{name:"Пусан",coords:[35.1796,129.0756]},"china":{name:"Шанхай",coords:[31.2304,121.4737]}};
const vlad=[43.1155,131.8855];
const map=L.map(mapNode,{scrollWheelZoom:false}).setView([52,110],3);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:18,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
const layer=L.featureGroup().addTo(map);
let sequence=0;
async function update(){
 const id=++sequence,origin=origins[$("routeOrigin").value]||origins.japan,city=$("routeDestination").value,dest=cities[city]||cities["Новосибирск"];
 $("routeSummaryTitle").textContent=origin.name+" → Владивосток → "+city;
 $("routeSeaLabel").textContent="Морской маршрут · схема";
 $("routeRoadDistance").textContent="Рассчитываем маршрут…";
 $("routeMapNote").textContent="Морское плечо показано схематично, а не как фактический трек судна. Дорожный маршрут — по открытой дорожной сети; тариф и срок автовоза подтверждаются перевозчиком.";
 layer.clearLayers();
 const originMarker=L.marker(origin.coords).bindPopup("Порт отправления: "+origin.name);
 const portMarker=L.marker(vlad).bindPopup("Владивосток — порт прибытия");
 const destMarker=L.marker(dest).bindPopup("Город получения: "+city);
 layer.addLayer(originMarker);layer.addLayer(portMarker);layer.addLayer(destMarker);
 const sea=L.polyline([origin.coords,vlad],{color:"#d5a45d",weight:3,dashArray:"8 8"}).bindPopup("Международное морское плечо — схематично");
 layer.addLayer(sea);
 const direct=L.polyline([vlad,dest],{color:"#8aa7bf",weight:2,dashArray:"5 7",opacity:.7}).addTo(layer);
 map.fitBounds(layer.getBounds().pad(.15));
 const from=vlad[1]+","+vlad[0],to=dest[1]+","+dest[0];
 try{
  const response=await fetch("https://router.project-osrm.org/route/v1/driving/"+from+";"+to+"?overview=full&geometries=geojson&steps=false");
  if(!response.ok)throw new Error("route unavailable");
  const data=await response.json();
  if(id!==sequence)return;
  if(data.code==="Ok"&&data.routes?.[0]){
   layer.removeLayer(direct);
   const route=data.routes[0],coords=route.geometry.coordinates.map(p=>[p[1],p[0]]);
   L.polyline(coords,{color:"#d8e3eb",weight:4,opacity:.9}).addTo(layer);
   $("routeRoadDistance").textContent=Math.round(route.distance/1000).toLocaleString("ru-RU")+" км · по дорогам";
   $("routeMapNote").textContent="Дорожное расстояние рассчитано по открытой карте OSRM/OpenStreetMap. Это не тариф перевозчика и не обещание срока доставки. Морской участок показан схематично.";
   map.fitBounds(layer.getBounds().pad(.15));
  }else throw new Error("no route");
 }catch{
  if(id!==sequence)return;
  $("routeRoadDistance").textContent="Маршрут не рассчитан";
  $("routeMapNote").textContent="Не удалось получить дорожный маршрут от Владивостока до "+city+". Показана ориентировочная линия между городами; расстояние и тариф не подставляются.";
 }
}
$("routeOrigin").addEventListener("change",update);
$("routeDestination").addEventListener("change",update);
update();
setTimeout(()=>map.invalidateSize(),250);
})();
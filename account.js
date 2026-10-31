(()=>{"use strict";
const cfg=window.PAPAUTO_CONFIG||{},KEY_REQUESTS="papauto_local_requests_v1",KEY_FAV="papauto:favorites:v1",KEY_SEARCH="papauto:saved-searches:v1";
const $=id=>document.getElementById(id),safeJson=(key,fallback=[])=>{try{const v=JSON.parse(localStorage.getItem(key)||"null");return Array.isArray(v)?v:fallback}catch{return fallback}};
const writeLocal=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}};
const localRoot=$("accountLocalRequests"),localStatus=$("accountStatus"),authPanel=$("accountAuthPanel"),signedPanel=$("accountSignedIn");
let client=null,user=null,authMode="signin",realtimeChannel=null,loading=false;
if(window.supabase?.createClient&&cfg.supabaseUrl&&cfg.supabasePublishableKey){client=window.supabase.createClient(cfg.supabaseUrl,cfg.supabasePublishableKey,{auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}})}
const say=(id,msg)=>{const el=$(id);if(el)el.textContent=msg};
const date=x=>{try{return new Date(x).toLocaleString("ru-RU")}catch{return ""}};
const countryMap={"Япония":"Japan","Южная Корея":"South Korea","Китай":"China","Не определился":"Japan"};
const statusLabels={new:"Заявка зарегистрирована",reviewing:"Проверка заявки",searching:"Идёт поиск автомобиля",auction_won:"Автомобиль выигран",purchased:"Автомобиль выкуплен",in_transit:"В пути",customs:"Таможенное оформление",delivered:"Доставлен",completed:"Завершён",cancelled:"Отменён"};
function renderLocal(){
 if(!localRoot)return;
 const items=safeJson(KEY_REQUESTS);localRoot.replaceChildren();
 if(!items.length){const p=document.createElement("p");p.textContent="Локальных заявок пока нет.";localRoot.append(p);return}
 items.slice(0,10).forEach(item=>{const card=document.createElement("article");card.className="account-order-card";const title=document.createElement("strong");title.textContent=[item.make,item.model,item.year].filter(Boolean).join(" ")||"Заявка на подбор";const meta=document.createElement("p");meta.textContent=[item.country||"Направление не указано",date(item.saved_at),item.sent?"отправлена менеджеру":"сохранена на устройстве"].join(" · ");const body=document.createElement("p");body.textContent=item.request||"Описание не сохранено";card.append(title,meta,body);localRoot.append(card)});
}
function saveLocal(lead,sent){
 if(!lead||!lead.request)return;
 const items=safeJson(KEY_REQUESTS),dedupe=String(lead.request)+"|"+String(lead.contact||"");
 const old=items.find(x=>x.dedupe===dedupe);
 if(old){old.sent=old.sent||Boolean(sent);old.saved_at=Date.now()}
 else items.unshift({id:Date.now().toString(36)+Math.random().toString(36).slice(2,7),dedupe,make:lead.make||"",model:lead.model||"",year:lead.yearTo||lead.yearFrom||"",country:lead.country||"",request:lead.request,contact:lead.contact||"",saved_at:Date.now(),sent:Boolean(sent)});
 const ok=writeLocal(KEY_REQUESTS,items.slice(0,20));renderLocal();say("accountStatus",ok?(sent?"Заявка отправлена менеджеру; локальная копия сохранена.":"Заявка сохранена на этом устройстве."):"Не удалось сохранить локальную историю.");
}
function setMode(mode){
 authMode=mode==="signup"?"signup":"signin";
 document.querySelectorAll("[data-auth-mode]").forEach(b=>{const active=b.dataset.authMode===authMode;b.classList.toggle("is-active",active);b.setAttribute("aria-pressed",String(active))});
 const nameWrap=$("accountDisplayNameWrap"),phoneWrap=$("accountPhoneWrap"),submit=$("accountAuthSubmit"),password=$("accountPassword");
 if(nameWrap)nameWrap.hidden=authMode!=="signup";if(phoneWrap)phoneWrap.hidden=authMode!=="signup";
 if(submit)submit.textContent=authMode==="signup"?"Создать аккаунт":"Войти";
 if(password)password.autocomplete=authMode==="signup"?"new-password":"current-password";
 say("accountAuthStatus",authMode==="signup"?"Укажите почту и придумайте пароль не короче 8 символов.":"Войдите, чтобы открыть заявки и синхронизировать данные.");
}
document.querySelectorAll("[data-auth-mode]").forEach(b=>b.addEventListener("click",()=>setMode(b.dataset.authMode)));
async function loadRequests(){
 if(!client||!user)return;
 const box=$("accountCloudRequests");if(!box)return;
 const {data:requests,error}=await client.from("customer_requests").select("id,country,vehicle_make,vehicle_model,vehicle_year,budget_rub,details,status,created_at,updated_at").eq("user_id",user.id).order("created_at",{ascending:false}).limit(30);
 if(error){box.textContent="Не удалось загрузить заявки: "+error.message;return}
 box.replaceChildren();
 if(!requests?.length){const p=document.createElement("p");p.textContent="Заявок в облачном кабинете пока нет. После входа отправьте заявку на подбор — она появится здесь.";box.append(p);return}
 const ids=requests.map(x=>x.id);
 const {data:events}=await client.from("order_events").select("request_id,status,message,created_at").in("request_id",ids).order("created_at",{ascending:true});
 requests.forEach(req=>{
  const card=document.createElement("article");card.className="account-order-card";
  const title=document.createElement("strong");title.textContent=[req.vehicle_make,req.vehicle_model,req.vehicle_year].filter(Boolean).join(" ")||"Заявка на автомобиль";
  const status=document.createElement("span");status.className="account-order-status";status.textContent=statusLabels[req.status]||req.status;
  const meta=document.createElement("p");meta.textContent=[req.country,date(req.created_at),req.budget_rub?new Intl.NumberFormat("ru-RU").format(req.budget_rub)+" ₽":""].filter(Boolean).join(" · ");
  const details=document.createElement("p");details.textContent=req.details||"Дополнительные пожелания не указаны.";
  const timeline=document.createElement("ol");timeline.className="account-order-timeline";
  (events||[]).filter(e=>e.request_id===req.id).forEach(ev=>{const li=document.createElement("li"),b=document.createElement("strong"),small=document.createElement("small");b.textContent=statusLabels[ev.status]||ev.status;small.textContent=date(ev.created_at)+(ev.message?" · "+ev.message:"");li.append(b,small);timeline.append(li)});
  card.append(title,status,meta,details,timeline);box.append(card);
 });
}
async function loadNotifications(){
 if(!client||!user)return;
 const box=$("accountNotifications");if(!box)return;
 const {data,error}=await client.from("notifications").select("id,title,body,link,read_at,created_at").eq("user_id",user.id).order("created_at",{ascending:false}).limit(40);
 if(error){box.textContent="Не удалось загрузить уведомления.";return}
 box.replaceChildren();
 if(!data?.length){const p=document.createElement("p");p.textContent="Уведомлений пока нет. Они появятся при изменении статуса вашей заявки.";box.append(p);return}
 data.forEach(n=>{const item=document.createElement("article");item.className="account-notification"+(n.read_at?" is-read":"");const title=document.createElement("strong"),body=document.createElement("p"),meta=document.createElement("small");title.textContent=n.title;body.textContent=n.body;meta.textContent=date(n.created_at);item.append(title,body,meta);if(!n.read_at){const btn=document.createElement("button");btn.type="button";btn.className="account-notification-read";btn.textContent="Прочитано";btn.addEventListener("click",async()=>{const {error}=await client.from("notifications").update({read_at:new Date().toISOString()}).eq("id",n.id).eq("user_id",user.id);if(!error)loadNotifications()});item.append(btn)}if(n.link){const a=document.createElement("a");a.href=n.link;a.textContent="Открыть кабинет";item.append(a)}box.append(item)});
}
async function persistFavorites(items){
 if(!client||!user)return;
 const rows=(items||[]).filter(x=>x&&x.id).map(x=>({user_id:user.id,source:({"japan":"Japan","south-korea":"South Korea","korea":"South Korea","china":"China","Japan":"Japan","South Korea":"South Korea","China":"China","PAPAUTO":"PAPAUTO"}[x.source]||"PAPAUTO"),external_id:String(x.id).slice(0,160),listing_url:String(x.url||x.link||"").slice(0,2048),vehicle_snapshot:x}));
 const {data:existing,error:readError}=await client.from("favorites").select("id,source,external_id").eq("user_id",user.id);
 if(readError){say("accountSyncStatus","Не удалось проверить избранное: "+readError.message);return}
 const keep=new Set(rows.map(x=>x.source+"|"+x.external_id)),stale=(existing||[]).filter(x=>!keep.has(x.source+"|"+x.external_id)).map(x=>x.id);
 if(stale.length){const {error}=await client.from("favorites").delete().eq("user_id",user.id).in("id",stale);if(error){say("accountSyncStatus","Не удалось удалить устаревшее избранное: "+error.message);return}}
 if(rows.length){const {error}=await client.from("favorites").upsert(rows,{onConflict:"user_id,source,external_id"});if(error){say("accountSyncStatus","Не удалось синхронизировать избранное: "+error.message);return}}
 say("accountSyncStatus","Избранное синхронизировано с аккаунтом.");
}
async function persistSearches(items){
 if(!client||!user)return;
 const rows=(items||[]).filter(x=>x&&x.filters).map(x=>({user_id:user.id,title:String(x.name||"Мой поиск").slice(0,120),filters:x.filters,notifications_enabled:true}));
 const {data:existing,error:readError}=await client.from("saved_searches").select("id,title").eq("user_id",user.id);
 if(readError){say("accountSyncStatus","Не удалось проверить сохранённые поиски: "+readError.message);return}
 const keep=new Set(rows.map(x=>x.title)),stale=(existing||[]).filter(x=>!keep.has(x.title)).map(x=>x.id);
 if(stale.length){const {error}=await client.from("saved_searches").delete().eq("user_id",user.id).in("id",stale);if(error){say("accountSyncStatus","Не удалось удалить старые поиски: "+error.message);return}}
 if(rows.length){const {error}=await client.from("saved_searches").upsert(rows,{onConflict:"user_id,title"});if(error){say("accountSyncStatus","Не удалось синхронизировать поиски: "+error.message);return}}
 say("accountSyncStatus","Сохранённые поиски синхронизированы с аккаунтом.");
}
async function hydratePersonalData(){
 if(!client||!user)return;
 const [fav,search]=await Promise.all([
  client.from("favorites").select("source,external_id,listing_url,vehicle_snapshot").eq("user_id",user.id).order("created_at",{ascending:false}).limit(50),
  client.from("saved_searches").select("title,filters,created_at").eq("user_id",user.id).order("created_at",{ascending:false}).limit(10)
 ]);
 const localFav=safeJson(KEY_FAV),localSearch=safeJson(KEY_SEARCH);
 if(fav.error)say("accountSyncStatus","Ошибка загрузки избранного: "+fav.error.message);
 else{
  const cloud=(fav.data||[]).map(x=>x.vehicle_snapshot||{id:x.external_id,source:x.source,url:x.listing_url}),seen=new Set(cloud.map(x=>String(x.id)));
  const merged=[...cloud,...localFav.filter(x=>!seen.has(String(x.id)))].slice(0,50);writeLocal(KEY_FAV,merged);if(localFav.length)await persistFavorites(merged);
 }
 if(search.error)say("accountSyncStatus","Ошибка загрузки поисков: "+search.error.message);
 else{
  const cloud=(search.data||[]).map(x=>({name:x.title,filters:x.filters,savedAt:x.created_at})),seen=new Set(cloud.map(x=>JSON.stringify(x.filters)));
  const merged=[...cloud,...localSearch.filter(x=>!seen.has(JSON.stringify(x.filters)))].slice(0,10);writeLocal(KEY_SEARCH,merged);if(localSearch.length)await persistSearches(merged);
 }
 window.dispatchEvent(new CustomEvent("papauto:cloud-data-loaded"));
 say("accountSyncStatus","Кабинет подключён. Избранное и сохранённые поиски синхронизируются.");
}
async function createRequest(lead){
 if(!client||!user||!lead?.consent)return;
 const country=countryMap[lead.country]||"Japan";
 const details=String(lead.request||"").slice(0,5000);
 const payload={user_id:user.id,country,vehicle_make:String(lead.make||"").slice(0,100),vehicle_model:String(lead.model||"").slice(0,100),vehicle_year:Number(lead.yearTo||lead.yearFrom)||null,budget_rub:Number(lead.budget)||null,details};
 const {error}=await client.from("customer_requests").insert(payload);
 if(error){say("accountSyncStatus","Заявка отправлена менеджеру, но не сохранена в кабинете: "+error.message);return}
 say("accountSyncStatus","Заявка также сохранена в вашем облачном кабинете.");
 await loadRequests();await loadNotifications();
}
async function startRealtime(){
 if(!client||!user)return;
 if(realtimeChannel)await client.removeChannel(realtimeChannel);
 realtimeChannel=client.channel("papauto-notifications-"+user.id).on("postgres_changes",{event:"INSERT",schema:"public",table:"notifications",filter:"user_id=eq."+user.id},payload=>{loadNotifications();const n=payload.new;if(window.Notification&&Notification.permission==="granted"&&document.visibilityState!=="visible"){try{new Notification(n.title||"PAPAUTO",{body:n.body||"Обновился статус вашей заявки.",icon:"/favicon.ico"})}catch{}}}).subscribe();
}
async function showSession(session){
 user=session?.user||null;
 if(authPanel)authPanel.hidden=Boolean(user);
 if(signedPanel)signedPanel.hidden=!user;
 if(user){
  say("accountUserEmail",user.email||"Аккаунт PAPAUTO");
  say("accountUserMeta","Вы вошли в личный кабинет");
  await hydratePersonalData();await Promise.all([loadRequests(),loadNotifications()]);await startRealtime();
 }else{
  if(realtimeChannel&&client){await client.removeChannel(realtimeChannel);realtimeChannel=null}
  if($("accountCloudRequests"))$("accountCloudRequests").textContent="Войдите, чтобы увидеть заявки.";
  if($("accountNotifications"))$("accountNotifications").textContent="Войдите, чтобы получать уведомления.";
 }
}
if(client){
 const authForm=$("accountAuthForm");
 if(authForm)authForm.addEventListener("submit",async e=>{
  e.preventDefault();const email=$("accountEmail").value.trim(),password=$("accountPassword").value,displayName=$("accountDisplayName")?.value.trim()||"",phone=$("accountPhone")?.value.trim()||"";
  const button=$("accountAuthSubmit");button.disabled=true;
  try{
   if(authMode==="signup"){
    const {data,error}=await client.auth.signUp({email,password,options:{data:{display_name:displayName,phone},emailRedirectTo:location.origin+"/#account"}});
    if(error)throw error;
    if(data.session){say("accountAuthStatus","Аккаунт создан. Вы вошли в систему.");await showSession(data.session)}
    else say("accountAuthStatus","Проверьте почту и подтвердите адрес, затем войдите. Если письмо не пришло, проверьте настройки SMTP и лимиты отправки Supabase.");
   }else{
    const {data,error}=await client.auth.signInWithPassword({email,password});if(error)throw error;
    say("accountAuthStatus","Вход выполнен.");await showSession(data.session);
   }
  }catch(err){say("accountAuthStatus",err.message||"Не удалось выполнить вход.")}
  finally{button.disabled=false}
 });
 const signOut=$("accountSignOut");if(signOut)signOut.addEventListener("click",async()=>{await client.auth.signOut();await showSession(null);say("accountAuthStatus","Вы вышли из аккаунта.")});
 const enablePush=$("accountEnablePush");if(enablePush)enablePush.addEventListener("click",async()=>{if(!("Notification" in window)){say("accountSyncStatus","Этот браузер не поддерживает системные уведомления.");return}try{const permission=await Notification.requestPermission();say("accountSyncStatus",permission==="granted"?"Уведомления браузера включены, пока сайт открыт.":"Разрешение на уведомления не выдано.")}catch{say("accountSyncStatus","Не удалось запросить разрешение. Проверьте настройки браузера.")}});
 const markAll=$("accountMarkAllRead");if(markAll)markAll.addEventListener("click",async()=>{if(!user)return;const {error}=await client.from("notifications").update({read_at:new Date().toISOString()}).eq("user_id",user.id).is("read_at",null);if(error)say("accountSyncStatus","Не удалось обновить уведомления: "+error.message);else loadNotifications()});
 client.auth.getSession().then(({data})=>showSession(data.session));
 client.auth.onAuthStateChange((event,session)=>{if(event==="SIGNED_IN"||event==="SIGNED_OUT"||event==="TOKEN_REFRESHED")showSession(session)});
 window.PAPAUTO_ACCOUNT={
  saveRequest:lead=>saveLocal(lead,false),
  persistFavorites,
  persistSearches,
  createRequest,
  getUser:()=>user
 };
 window.addEventListener("papauto:lead-prepared",e=>saveLocal(e.detail,false));
 window.addEventListener("papauto:lead-submitted",e=>{saveLocal(e.detail,true);if(user)createRequest(e.detail)});
 window.addEventListener("papauto:favorites-changed",e=>persistFavorites(e.detail));
 window.addEventListener("papauto:saved-searches-changed",e=>persistSearches(e.detail));
}else{
 const notice=$("accountCloudNotice");if(notice)notice.hidden=false;say("accountStatus","Облачный кабинет приостановлен до подключения российского хранилища персональных данных.");
 window.PAPAUTO_ACCOUNT={saveRequest:lead=>saveLocal(lead,false)};
 window.addEventListener("papauto:lead-prepared",e=>saveLocal(e.detail,false));
 window.addEventListener("papauto:lead-submitted",e=>saveLocal(e.detail,true));
}
const exportButton=$("exportLocalRequests");if(exportButton)exportButton.addEventListener("click",()=>{const blob=new Blob([JSON.stringify(safeJson(KEY_REQUESTS),null,2)],{type:"application/json;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="papauto-local-requests-"+new Date().toISOString().slice(0,10)+".json";document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url)});
const clear=$("clearLocalRequests");if(clear)clear.addEventListener("click",()=>{localStorage.removeItem(KEY_REQUESTS);renderLocal();say("accountStatus","Локальная история очищена.")});
renderLocal();setMode("signin");
})();
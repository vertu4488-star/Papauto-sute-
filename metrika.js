/* Yandex Metrica for PapAuto */
(function () {
  "use strict";
  var id = 114106531;
  (function(m,e,t,r,i,k,a){
    m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r)return;}
    k=e.createElement(t);a=e.getElementsByTagName(t)[0];
    k.async=1;k.src=r;a.parentNode.insertBefore(k,a);
  })(window,document,"script","https://mc.yandex.ru/metrika/tag.js?id="+id,"ym");
  ym(id,"init",{ssr:true,webvisor:false,clickmap:true,accurateTrackBounce:true,trackLinks:true});
  document.addEventListener("click",function(e){
    var a=e.target&&e.target.closest&&e.target.closest("a[href]");
    if(!a)return;
    var href=a.getAttribute("href")||"";
    if(/^tel:/i.test(href))ym(id,"reachGoal","phone_click");
    if(/^(https?:\/\/)?(t\.me|telegram\.me)\//i.test(href))ym(id,"reachGoal","telegram_click");
  });
  // Count only server-confirmed submissions; never send contact data to analytics.
  window.addEventListener("papauto:lead-submitted", function () {
    if (typeof window.ym === "function") window.ym(id, "reachGoal", "generate_lead");
    if (typeof window.gtag === "function") window.gtag("event", "generate_lead", {form_id: "assistantForm"});
  });
  // Google Analytics 4 on all landing pages. Home pages already initialize gtag.
  // Do not initialize it a second time, or page_view would be counted twice.
  if (typeof window.gtag !== "function") {
    var gaId = "G-JBPEKLFCXW";
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", gaId);
    var gaScript = document.createElement("script");
    gaScript.async = true;
    gaScript.src = "https://www.googletagmanager.com/gtag/js?id=" + gaId;
    document.head.appendChild(gaScript);
  }

})();

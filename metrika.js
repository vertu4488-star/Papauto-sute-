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
  ym(id,"init",{ssr:true,webvisor:true,clickmap:true,accurateTrackBounce:true,trackLinks:true});
  document.addEventListener("click",function(e){
    var a=e.target&&e.target.closest&&e.target.closest("a[href]");
    if(!a)return;
    var href=a.getAttribute("href")||"";
    if(/^tel:/i.test(href))ym(id,"reachGoal","phone_click");
    if(/^(https?:\/\/)?(t\.me|telegram\.me)\//i.test(href))ym(id,"reachGoal","telegram_click");
  });
})();

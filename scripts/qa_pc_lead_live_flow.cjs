// Run on the real https://papauto.ru/podbor.html from desktop Chromium.
// All lead POSTs are intercepted: no client data or test leads reach production.
const {chromium}=require("playwright");
const assert=require("node:assert/strict");
const URL="https://papauto.ru/podbor.html";
const POST="https://papauto.ru/api/leads";
async function prepare(page){
  // An approved auction-gallery prefill supplies Toyota Corolla without
  // depending on a dropdown animation. This test isolates real form submission.
  const similar="Toyota Corolla Sport 2023 · Япония";
  await page.goto(URL+"?similar="+encodeURIComponent(similar),{waitUntil:"load",timeout:45000});
  await page.locator('.sd-question[data-name="make"]').waitFor({state:"visible",timeout:15000});
  const make=await page.locator('.sd-question[data-name="make"]').innerText();
  const model=await page.locator('.sd-question[data-name="model"]').innerText();
  assert(make.includes("Toyota")&&model.includes("Corolla"),
    "Auction prefill must identify selected car, got "+JSON.stringify({make,model}));
  const next=page.getByRole("button",{name:/Далее|Продолжить|Next/i}).filter({visible:true}).last();
  await next.click({timeout:9000});
  const phone=page.locator('.sd-question[data-name="phone"] input[type="tel"]');
  await phone.waitFor({state:"visible"});
  await phone.fill("+79000000000");
  await page.locator('.sd-question[data-name="consent"] input[type="checkbox"]').first().check({force:true});
  return page.getByRole("button",{name:/Отправить заявку|Завершить|Complete/i}).filter({visible:true}).last();
}
async function scenario(browser,mode){
  const context=await browser.newContext({viewport:{width:1440,height:900},locale:"ru-RU"});
  const page=await context.newPage(),posts=[],jsErrors=[];
  page.on("pageerror",e=>jsErrors.push(e.message));
  await page.route("**/*",async route=>{
    const req=route.request(), url=req.url();
    if(req.method()!=="POST")return route.continue();
    // Protection: do not send anything to any real server.
    if(url!==POST)throw Error("Unexpected production POST: "+url.replace(/\?.*/,""));
    const payload=JSON.parse(req.postData()||"{}");
    posts.push({url,country:payload.country,make:payload.request?.includes("Марка: Toyota"),
      model:payload.request?.includes("Модель: Corolla"),consent:payload.consent,
      phone:payload.contact==="+79000000000"});
    const attempt=posts.length;
    const failure=mode==="422-retry"&&attempt===1;
    const status=failure?422:mode==="502-unconfirmed"?502:mode==="202-stored"?202:200;
    const response=failure?{detail:"Проверьте номер телефона и обязательные поля"}:
      mode==="502-unconfirmed"?{ok:false,delivery_unknown:true,detail:"Нет подтверждения"}:
      {ok:true,stored:true,notified:status===200,message:"Mock only; no data saved"};
    await route.fulfill({status,contentType:"application/json",headers:{"Cache-Control":"no-store"},body:JSON.stringify(response)});
  });
  const button=await prepare(page);
  await button.click();
  const status=page.locator("#surveyStatus");
  if(mode==="200-notified"||mode==="202-stored"){
    await page.locator("#surveySuccessDialog").waitFor({state:"visible",timeout:12000});
    const dialog=await page.locator("#surveySuccessDialog").innerText();
    assert(mode==="200-notified"?dialog.includes("отправлена"):dialog.includes("сохранена"),dialog);
    assert.equal(posts.length,1,"No repeated submission");
  }else if(mode==="422-retry"){
    await page.getByText("Заявка не отправлена",{exact:false}).first().waitFor({state:"visible",timeout:10000});
    assert.equal(await page.locator("#surveySuccessDialog").isVisible(),false);
    assert.equal(posts.length,1);
    await button.click();
    await page.locator("#surveySuccessDialog").waitFor({state:"visible",timeout:10000});
    assert.equal(posts.length,2,"Corrected request should retry exactly once");
  }else{
    await page.getByText(/Ошибка 502|Нет подтверждения|Статус заявки/,{}).first().waitFor({state:"visible",timeout:10000});
    assert.equal(await page.locator("#surveySuccessDialog").isVisible(),false);
    await button.click();
    await page.waitForTimeout(400);
    assert.equal(posts.length,1,"Ambiguous transport must not resubmit");
  }
  assert(posts.every(p=>p.url===POST&&p.consent&&p.make&&p.model&&p.phone),JSON.stringify(posts));
  assert.equal(jsErrors.length,0,JSON.stringify(jsErrors));
  console.log("PAPAUTO_PC_FORM_CASE_PASSED "+JSON.stringify({mode,requests:posts.length,payloadOk:true,duplicateSafe:true}));
  await context.close();
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const mode of ["200-notified","202-stored","422-retry","502-unconfirmed"])await scenario(browser,mode);
  console.log("PAPAUTO_PC_FORM_ALL_CASES_PASSED");
 }finally{await browser.close();}
})().catch(err=>{console.error("PAPAUTO_PC_FORM_FAILED",err.stack||err);process.exitCode=1;});

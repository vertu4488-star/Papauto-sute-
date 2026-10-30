"""Live on-demand parser for TTPAI public model transaction summaries."""
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
import httpx
class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]
    def handle_data(self,data):
        value=" ".join((data or "").split())
        if value:self.parts.append(value)
_MODELS={
("tesla","model 3"):("Tesla Model 3","https://www.ttpai.cn/shanghai/price/tesila-model3"),
("tesla","model3"):("Tesla Model 3","https://www.ttpai.cn/shanghai/price/tesila-model3"),
("tesla","model y"):("Tesla Model Y","https://www.ttpai.cn/shanghai/price/tesila-modely"),
("tesla","modely"):("Tesla Model Y","https://www.ttpai.cn/shanghai/price/tesila-modely"),
("volkswagen","polo"):("Volkswagen Polo","https://www.ttpai.cn/shanghai/price/dazhong-polo"),
("vw","polo"):("Volkswagen Polo","https://www.ttpai.cn/shanghai/price/dazhong-polo"),
("фольксваген","поло"):("Volkswagen Polo","https://www.ttpai.cn/shanghai/price/dazhong-polo"),
}
def _norm(value):return re.sub(r"\s+"," ",(value or "").strip().casefold())
async def fetch_ttpai_model_stats(make,model):
 info=_MODELS.get((_norm(make),_norm(model)))
 if not info:return None
 display_name,url=info
 try:
  async with httpx.AsyncClient(timeout=15.0,follow_redirects=True) as client:
   response=await client.get(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PAPAUTO-Statistics/1.0; +https://papauto.ru)","Accept":"text/html,application/xhtml+xml","Accept-Language":"zh-CN,zh;q=0.9,en;q=0.7"})
  response.raise_for_status(); parser=_VisibleText(); parser.feed(response.text)
  page_text=re.sub(r"\s+"," "," ".join(parser.parts)); averages={}
  for age in (3,5,7):
   match=re.search(rf"{age}\s*年车龄\s*市场均价\s*([0-9]+(?:\.[0-9]+)?)\s*万",page_text)
   averages[f"age_{age}_avg_cny"]=round(float(match.group(1))*10000) if match else None
  if not any(v is not None for v in averages.values()):
   return {"ok":False,"source":"TTPAI","source_url":url,"message":"Страница TTPAI открылась, но формат блока средних цен изменился."}
  recent=[]
  for match in re.finditer(r"最新成交\s*(.{0,180}?)\s*(20\d{2}\.\d{2}\.\d{2})成交",page_text):
   recent.append({"description":re.sub(r"\s+"," ",match.group(1)).strip(" /／·")[:180],"date":match.group(2)})
   if len(recent)>=5:break
  return {"ok":True,"country":"china","data_type":"china_model_live","source":"TTPAI · 历史成交数据","model":display_name,"currency":"CNY","averages":averages,"recent_sales":recent,"source_url":url,"retrieved_at":datetime.now(timezone.utc).isoformat(),"disclaimer":"Статистика сделок TTPAI по выбранной модели на странице города Shanghai, а не полный архив китайских аукционов. Средние по возрасту не являются ценой конкретного лота; доставка, экспорт и оформление в РФ не включены."}
 except (httpx.HTTPError,ValueError,TypeError):
  return {"ok":False,"source":"TTPAI","source_url":url,"message":"Не удалось обновить открытую статистику TTPAI. Старые примеры не подставляются вместо свежих данных."}

"""
Ultra-FastPsychologyTodayScraper
===================================

Optimizedversionwithparallelprocessing,asyncoperations,
andintelligentcachingformaximumspeed.
"""

importasyncio
importaiohttp
fromconcurrent.futuresimportThreadPoolExecutor,as_completed
fromseleniumimportwebdriver
fromselenium.webdriver.chrome.optionsimportOptions
fromselenium.webdriver.common.byimportBy
fromselenium.webdriver.support.uiimportWebDriverWait
fromselenium.webdriver.supportimportexpected_conditionsasEC
fromselenium.common.exceptionsimportTimeoutException,WebDriverException
importrequests
frombs4importBeautifulSoup
importpandasaspd
importre
importtime
importjson
importrandom
importcsv
fromdatetimeimportdatetime
fromtherapist_outreachimportTherapistInfo,EmailTemplateGenerator,EmailSender
importthreading
fromqueueimportQueue
importmultiprocessingasmp

classFastTherapistExtractor:
def__init__(self,max_workers=10,batch_size=20):
self.session=requests.Session()
self.session.headers.update({
'User-Agent':'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.36'
})
self.max_workers=max_workers#Parallelworkers
self.batch_size=batch_size#URLstoprocessperbatch
self.driver_pool=[]#Poolofseleniumdrivers
self.profile_cache={}#Cacheparsedprofiles

defsetup_driver_pool(self,pool_size=3):
"""SetuppoolofChromedriversforparallelprocessing"""
chrome_options=Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-logging')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-images')#Don'tloadimages
chrome_options.add_argument('--disable-javascript')#Fasterloading
chrome_options.add_argument('--window-size=1024,768')

foriinrange(pool_size):
try:
driver=webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(10)#Fastertimeout
self.driver_pool.append(driver)
print(f"✅Createddriver{i+1}/{pool_size}")
exceptExceptionase:
print(f"❌Failedtocreatedriver{i+1}:{e}")

returnlen(self.driver_pool)>0

defget_all_profile_urls_fast(self,state_name):
"""FastextractionofALLprofileURLs-usingworkingpaginationlogic"""
print(f"🚀FASTURLEXTRACTIONfor{state_name.upper()}")

page_urls=[]
page=1
max_pages=30#Safetylimittopreventinfiniteloops

whilepage<=max_pages:
ifpage==1:
state_url=f"https://www.psychologytoday.com/us/therapists/{state_name.lower()}"
else:
state_url=f"https://www.psychologytoday.com/us/therapists/{state_name.lower()}?page={page}"

try:
response=self.session.get(state_url,timeout=10)
ifresponse.status_code==403:
print(f"❌Accessblocked(403).Waiting30seconds...")
time.sleep(30)
response=self.session.get(state_url,timeout=10)

ifresponse.status_code!=200:
print(f"❌Failedtoloadpage{page}:{response.status_code}")
ifresponse.status_code==403:
time.sleep(60)#Waitlongerfor403errors
break

soup=BeautifulSoup(response.content,'html.parser')
results_rows=soup.select('.results-row')

ifnotresults_rows:
print(f"📄Page{page}:Nomoreresultsfound")
break

#Checkifwefoundnewprofiles
page_profiles=[]
forrowinresults_rows:
links=row.find_all('a',href=True)
forlinkinlinks:
href=link.get('href','')
if'/us/therapists/'inhrefandnotany(skipinhrefforskipin['?','#']):
ifhref.startswith('/'):
full_url='https://www.psychologytoday.com'+href
else:
full_url=href
iffull_urlnotinpage_profiles:
page_profiles.append(full_url)

ifnotpage_profiles:
print(f"📄Page{page}:Nonewprofilesfound")
break

page_urls.append(state_url)
print(f"📄Page{page}:{len(page_profiles)}profilesfound")

#Checkforpagination-lookforpagelinkswithhighernumbers
pagination_links=soup.find_all('a',href=re.compile(r'page=\\d+'))
max_page_found=page

ifpagination_links:
forlinkinpagination_links:
href=link.get('href','')
page_match=re.search(r'page=(\\d+)',href)
ifpage_match:
page_num=int(page_match.group(1))
max_page_found=max(max_page_found,page_num)

#Alsocheckfor"Next"button
next_page=soup.find('a',{'aria-label':'Nextpage'})orsoup.find('a',string='Next')
ifnext_page:
max_page_found=max(max_page_found,page+1)

print(f"➡️Goingtopage{page+1}(maxdetected:{max_page_found})")
page+=1

#Updatemax_pagesifwedetectmore
ifmax_page_found>max_pages:
max_pages=min(max_page_found+2,50)#Safetycapat50

#Smalldelaybetweenpagerequests
time.sleep(0.5)

exceptExceptionase:
print(f"❌Errorprocessingpage{page}:{e}")
break

print(f"📄Willprocess{len(page_urls)}pages")

#Processpagesinparallel
all_profile_urls=[]
start_time=time.time()

withThreadPoolExecutor(max_workers=self.max_workers)asexecutor:
#Submitallpagescrapingtasks
future_to_page={
executor.submit(self._extract_profiles_from_page,url,page_num):page_num
forpage_num,urlinenumerate(page_urls,1)
}

#Collectresultsastheycomplete
forfutureinas_completed(future_to_page):
page_num=future_to_page[future]
try:
profile_urls=future.result()
all_profile_urls.extend(profile_urls)
print(f"✅Page{page_num}:{len(profile_urls)}profiles({len(all_profile_urls)}total)")
exceptExceptionase:
print(f"❌Page{page_num}failed:{e}")

elapsed=time.time()-start_time
print(f"🎯FASTEXTRACTIONCOMPLETE:{len(all_profile_urls)}profilesin{elapsed:.1f}s")
returnlist(set(all_profile_urls))#Removeduplicates

def_extract_profiles_from_page(self,page_url,page_num):
"""ExtractprofileURLsfromasinglepage"""
try:
response=self.session.get(page_url,timeout=10)
ifresponse.status_code!=200:
return[]

soup=BeautifulSoup(response.content,'html.parser')
results_rows=soup.select('.results-row')

profile_urls=[]
forrowinresults_rows:
links=row.find_all('a',href=True)
forlinkinlinks:
href=link.get('href','')
if'/us/therapists/'inhrefandnotany(skipinhrefforskipin['?','#']):
ifhref.startswith('/'):
full_url='https://www.psychologytoday.com'+href
else:
full_url=href

iffull_urlnotinprofile_urls:
profile_urls.append(full_url)

returnprofile_urls

exceptExceptionase:
print(f"❌Errorextractingpage{page_num}:{e}")
return[]

defextract_therapists_parallel(self,profile_urls):
"""Extracttherapistdatausingparallelprocessing"""
print(f"\\n🔥PARALLELPROCESSING:{len(profile_urls)}profiles")
print(f"⚡Using{self.max_workers}workers,{len(self.driver_pool)}seleniumdrivers")

therapists_data=[]
processed_count=0
start_time=time.time()

#Processinbatches
foriinrange(0,len(profile_urls),self.batch_size):
batch=profile_urls[i:i+self.batch_size]
batch_num=i//self.batch_size+1
total_batches=(len(profile_urls)+self.batch_size-1)//self.batch_size

print(f"\\n📦Batch{batch_num}/{total_batches}:{len(batch)}profiles")

#Processbatchinparallel
withThreadPoolExecutor(max_workers=self.max_workers)asexecutor:
future_to_url={
executor.submit(self.extract_single_therapist_fast,url):url
forurlinbatch
}

batch_results=[]
forfutureinas_completed(future_to_url):
url=future_to_url[future]
try:
result=future.result()
ifresult:
batch_results.append(result)
status="📧"ifresult.get('email')else"📝"
print(f"{status}{result['name'][:40]}")
processed_count+=1
exceptExceptionase:
print(f"❌Failed:{url.split('/')[-2][:30]}-{e}")
processed_count+=1

therapists_data.extend(batch_results)

#Progressupdate
elapsed=time.time()-start_time
rate=processed_count/elapsedifelapsed>0else0
remaining=len(profile_urls)-processed_count
eta=remaining/rateifrate>0else0

print(f"📊Progress:{processed_count}/{len(profile_urls)}({rate:.1f}/s,ETA:{eta/60:.1f}m)")

#Saveprogresseverybatch
ifbatch_results:
self._save_progress(therapists_data,f"fast_progress_batch_{batch_num}")

total_time=time.time()-start_time
print(f"\\n🎉PARALLELEXTRACTIONCOMPLETE!")
print(f"⏱️Totaltime:{total_time:.1f}s({len(profile_urls)/total_time:.1f}profiles/s)")
print(f"📧Emailsfound:{len([tfortintherapists_dataift.get('email')])}")

returntherapists_data

defextract_single_therapist_fast(self,profile_url):
"""Fastsingletherapistextractionwithoptimizations"""
try:
#Usecachedresultifavailable
url_key=profile_url.split('/')[-2]
ifurl_keyinself.profile_cache:
returnself.profile_cache[url_key]

#Fastprofileextraction
response=self.session.get(profile_url,timeout=8)#Fastertimeout
ifresponse.status_code!=200:
returnNone

soup=BeautifulSoup(response.content,'html.parser')

#Quickdataextraction
therapist_data={
'profile_url':profile_url,
'name':self._fast_extract_name(soup),
'credentials':self._fast_extract_credentials(soup),
'location':self._fast_extract_location(soup),
'phone':self._fast_extract_phone(soup),
'practice_name':self._fast_extract_practice_name(soup),
'specialties':','.join(self._fast_extract_specialties(soup)),
'insurance':','.join(self._fast_extract_insurance(soup)),
'session_fee':self._fast_extract_session_fee(soup),
'languages':','.join(self._fast_extract_languages(soup)),
'therapy_types':','.join(self._fast_extract_therapy_types(soup)),
'website':'',
'email':'',
'extraction_date':datetime.now().strftime('%Y-%m-%d%H:%M:%S'),
'has_doctoral_degree':False
}

#Quickdoctoraldegreecheck
therapist_data['has_doctoral_degree']=any(
credintherapist_data['credentials'].upper()
forcredin['PHD','PSYD','EDD','MD']
)

#Quickemailextraction
direct_email=self._fast_extract_direct_email(soup)
ifdirect_email:
therapist_data['email']=direct_email
else:
#Onlyfollowwebsiteifwehavedriversavailable
website_links=soup.find_all('a',href=re.compile(r'/us/profile/\\d+/website'))
ifwebsite_linksandself.driver_pool:
website_url,website_email=self._fast_follow_website_redirect(website_links[0])
ifwebsite_url:
therapist_data['website']=website_url
ifwebsite_email:
therapist_data['email']=website_email

#Cacheresult
self.profile_cache[url_key]=therapist_data
returntherapist_data

exceptExceptionase:
returnNone

def_fast_follow_website_redirect(self,website_link):
"""Websiteredirectwithbettertimingforemailextraction"""
ifnotself.driver_pool:
return"",""

#Getavailabledriver(simpleround-robin)
driver=self.driver_pool[threading.current_thread().ident%len(self.driver_pool)]

website_redirect=website_link.get('href')
ifwebsite_redirect.startswith('/'):
website_redirect='https://www.psychologytoday.com'+website_redirect

try:
driver.set_page_load_timeout(10)#Increasedfrom8s
driver.get(website_redirect)
time.sleep(3)#Increasedfrom2stoletdynamiccontentload

final_url=driver.current_url

if('psychologytoday.com'notinfinal_urland
final_url!=website_redirect):

#Betteremailextractionwithmultipleattempts
page_source=driver.page_source
soup=BeautifulSoup(page_source,'html.parser')

#Trymultipleextractionmethods
email=self._fast_extract_emails_from_website(soup)

#Ifnoemailfound,waitabitmoreandtryagain
ifnotemail:
time.sleep(2)
page_source=driver.page_source
soup=BeautifulSoup(page_source,'html.parser')
email=self._fast_extract_emails_from_website(soup)

returnfinal_url,email

return"",""

exceptException:
return"",""

#Fastextractionmethods(simplifiedversions)
def_fast_extract_name(self,soup):
name_elem=soup.select_one('h1')
ifname_elem:
name=name_elem.get_text(strip=True)
name=re.sub(r'\\(.*?\\)','',name)
returnname.strip()
return""

def_fast_extract_credentials(self,soup):
text=soup.get_text()
patterns=[r'\\b(PhD|PsyD|EdD|MD|LCSW|LMFT|LPC|LMHC|LPCC|LCPC|LMHP)\\b']

all_creds=[]
forpatterninpatterns:
matches=re.findall(pattern,text,re.IGNORECASE)
all_creds.extend(matches)

return','.join(list(set(all_creds))[:5])

def_fast_extract_location(self,soup):
text=soup.get_text()
match=re.search(r'([A-Za-z\\s]+),\\s*([A-Z]{2})\\b',text)
ifmatch:
returnf"{match.group(1).strip()},{match.group(2)}"
return""

def_fast_extract_phone(self,soup):
text=soup.get_text()
match=re.search(r'\\(?\\d{3}\\)?[-\\s]?\\d{3}[-\\s]?\\d{4}',text)
ifmatch:
clean_phone=re.sub(r'[^\\d]','',match.group())
iflen(clean_phone)==10:
returnf"({clean_phone[:3]}){clean_phone[3:6]}-{clean_phone[6:]}"
return""

def_fast_extract_practice_name(self,soup):
selectors=['.practice-name','.organization-name']
forselectorinselectors:
elem=soup.select_one(selector)
ifelem:
returnelem.get_text(strip=True)
return""

def_fast_extract_specialties(self,soup):
text=soup.get_text().lower()
specialties=[
'anxiety','depression','trauma','ptsd','adhd','addiction',
'couplestherapy','familytherapy','grief','bipolar'
]
return[s.title()forsinspecialtiesifsintext][:5]

def_fast_extract_insurance(self,soup):
text=soup.get_text()
insurance_companies=[
'Aetna','Anthem','BlueCross','Cigna','Humana',
'Medicare','Medicaid','UnitedHealth','Tricare'
]
return[insforinsininsurance_companiesifins.lower()intext.lower()][:5]

def_fast_extract_session_fee(self,soup):
text=soup.get_text()
match=re.search(r'\\$\\d{2,3}(?:-\\$?\\d{2,3})?',text)
returnmatch.group()ifmatchelse""

def_fast_extract_languages(self,soup):
text=soup.get_text()
languages=['Spanish','French','German','Italian','Chinese','Japanese']
return[langforlanginlanguagesiflang.lower()intext.lower()]

def_fast_extract_therapy_types(self,soup):
text=soup.get_text().lower()
modalities=['cognitivebehavioral','cbt','dbt','emdr','psychodynamic','mindfulness']
return[mod.title()formodinmodalitiesifmodintext][:5]

def_fast_extract_direct_email(self,soup):
#Quickemailextractionwithbetterparsing
mailto_links=soup.find_all('a',href=re.compile(r'^mailto:',re.I))
forlinkinmailto_links:
email=link.get('href','').replace('mailto:','').strip()
#Cleanupemailaddress
if'?'inemail:
email=email.split('?')[0]
if'&'inemail:
email=email.split('&')[0]
if'@'inemailand'.'inemailandlen(email)<50:#Reasonableemaillength
returnemail.strip()

#Textpatternsearchwithbettercleanup
text=soup.get_text()
#Morerestrictiveemailpattern
emails=re.findall(r'\\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,6}\\b',text)
foremailinemails:
#Filteroutgenericemailsandoverlylongemails
if(len(email)<50and
'@'inemailand
notany(genericinemail.lower()forgenericin['noreply','admin','support','info','contact'])):
returnemail.strip()

return""

def_fast_extract_emails_from_website(self,soup):
#Improvedwebsiteemailextraction
mailto_links=soup.find_all('a',href=re.compile(r'^mailto:',re.I))
forlinkinmailto_links:
email=link.get('href','').replace('mailto:','').strip()
#Cleanupemailparameters
if'?'inemail:
email=email.split('?')[0]
if'&'inemail:
email=email.split('&')[0]
if('@'inemailand'.'inemailandlen(email)<50and
notany(genericinemail.lower()forgenericin['noreply','admin','support','info'])):
returnemail.strip()

#Extractfromtextwithbetterfiltering
text=soup.get_text()
#Morerestrictiveemailpattern
emails=re.findall(r'\\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,6}\\b',text)
foremailinemails:
if(len(email)<50and
'@'inemailand
'.'inemailand
notany(genericinemail.lower()forgenericin['noreply','admin','support','info','contact'])):
returnemail.strip()

return""

def_save_progress(self,data,filename):
"""SaveprogresstoCSV"""
try:
df=pd.DataFrame(data)
df.to_csv(f"{filename}.csv",index=False,encoding='utf-8')
exceptException:
pass

defcleanup(self):
"""Cleanupdriverpool"""
fordriverinself.driver_pool:
try:
driver.quit()
except:
pass
self.driver_pool=[]

defmain():
print("🚀ULTRA-FASTPSYCHOLOGYTODAYSCRAPER")
print("="*60)
print("⚡Optimizedformaximumspeedwithparallelprocessing")
print()

state_name=input("Enterstatename:").strip()
ifnotstate_name:
print("❌Statenamerequired")
return

#Getperformancesettings
max_workers=int(input("Maxparallelworkers(10-20):")or"15")
batch_size=int(input("Batchsize(20-50):")or"30")
use_selenium=input("UseSeleniumforemails?(y/n):").lower()=='y'

print(f"\\n🔧Settings:{max_workers}workers,batchsize{batch_size}")

#Createfastextractor
extractor=FastTherapistExtractor(max_workers=max_workers,batch_size=batch_size)

try:
#Setupseleniumpoolifrequested
ifuse_selenium:
driver_count=min(3,max_workers//3)#Reasonabledrivercount
print(f"\\n🔧Settingup{driver_count}Seleniumdrivers...")
ifnotextractor.setup_driver_pool(driver_count):
print("⚠️Seleniumsetupfailed,continuingwithoutwebsiteemailextraction")

#Phase1:FastURLextraction
start_time=time.time()
profile_urls=extractor.get_all_profile_urls_fast(state_name)

ifnotprofile_urls:
print(f"❌Noprofilesfoundfor{state_name}")
return

url_time=time.time()-start_time
print(f"⏱️URLextraction:{url_time:.1f}s({len(profile_urls)/url_time:.1f}URLs/s)")

#Phase2:Paralleldataextraction
therapists_data=extractor.extract_therapists_parallel(profile_urls)

iftherapists_data:
#Savefinalresults
filename=f"{state_name.lower()}_fast.csv"
df=pd.DataFrame(therapists_data)

#Reordercolumns
columns=[
'name','credentials','has_doctoral_degree','email','phone',
'practice_name','location','website','specialties',
'insurance','session_fee','languages','therapy_types',
'profile_url','extraction_date'
]
df=df.reindex(columns=columns,fill_value='')
df.to_csv(filename,index=False,encoding='utf-8')

total_time=time.time()-start_time
email_count=len([tfortintherapists_dataift.get('email')])

print(f"\\n🎉ULTRA-FASTEXTRACTIONCOMPLETE!")
print(f"📊Totaltherapists:{len(therapists_data)}")
print(f"📧Emailsfound:{email_count}")
print(f"⏱️Totaltime:{total_time:.1f}s")
print(f"🚀Speed:{len(therapists_data)/total_time:.1f}therapists/second")
print(f"💾Datasavedto:{filename}")

finally:
extractor.cleanup()

if__name__=="__main__":
main()


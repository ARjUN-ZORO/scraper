import requests
import lxml.html
from PIL import Image
from io import BytesIO
import argparse
import json

get_url = "https://parivahan.gov.in/rcdlstatus/?pur_cd=101"
post_url ="https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml"

parser = argparse.ArgumentParser()
parser.add_argument("dl", type=str, help="DL Number")
parser.add_argument("dob", type=str, help="Date of Birth")
args = parser.parse_args()

post_data = {"javax.faces.partial.ajax":"true",
"javax.faces.source":"form_rcdl:j_idt43",
"javax.faces.partial.execute":"@all",
"javax.faces.partial.render":"form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl",
"form_rcdl":"form_rcdl",
"form_rcdl:tf_dlNO":args.dl,
"form_rcdl:tf_dob_input":args.dob,
}

output = {}

def validate_input():
    if len(args.dl) == 16:
        return True
    else:
        print("Check DL Num")
        return False

def check_connection():
    try:
        requests.get(get_url)
        return True
    except:
        print("Unable to Connect to the Portal ")
        return False

def get_captcha(img):
    img.show()
    return input()

def get_img(doc,s):
    img_url = doc.xpath('/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[3]/div/div[2]/div/div[2]/table/tbody/tr/td[1]/img')[0]
    img_res = s.get("https://parivahan.gov.in"+img_url.get('src'))
    img_id = img_url.get('id').split(':')[:2]
    img_id = ':'.join(str(x) for x in img_id)+':CaptchaID'
    img = Image.open(BytesIO(img_res.content))
    post_data[img_id] = get_captcha(img)
    return True


def check_res(res):
    root = lxml.etree.fromstring(res.content)
    soup = lxml.html.fromstring(root.getchildren()[0].getchildren()[0].text)
    # if soup.xpath('/div/div[1]/div[0]/div[0]/ul/li/span/')[0]:
    try:
        print(soup.xpath('//span[@class="ui-messages-error-detail"]/text()')[0])
        print("Wrong Captcha, Enter again")
        return False
    except:
        return True


def submit_form(s):
    try:
        res = s.post(post_url,data=post_data)
    except Exception as e:
        print(e)
        exit()
    return res

def retrive_data(s):
    try:
        res = s.get(get_url)
    except Exception as e:
        print(e)
        exit()
    return lxml.html.fromstring(res.content)

def fill_data(res):
    root = lxml.etree.fromstring(res.content)
    soup = lxml.html.fromstring(root.getchildren()[0].getchildren()[0].text)
    all_data  = [td.text_content() for td in soup.xpath('//td')]
    # print(all_data)
    i=0
    while i<10:
        output[all_data[i][:-1]] = all_data[i+1]
        i=i+2
    output[all_data[10]] = {all_data[11][:4]:all_data[11][6:],all_data[12][:2]:all_data[12][4:]}
    output[all_data[13]] = {all_data[14][:4]:all_data[14][6:],all_data[15][:2]:all_data[15][4:]}
    output[all_data[16][:-1]] = all_data[17]
    output[all_data[18][:-1]] = all_data[19]
    j = 20
    while j<len(all_data[19:])+19:
        output['Class of Vehicle Details'] = [{'Class Of Vehicle':all_data[j+1],'COV Category':all_data[j],'COV Issue Date':all_data[j+2]}]
        j = j + 3
    with open(args.dl+'.json', 'w') as outfile:
        json.dump(output, outfile)
    exit()

def start_session():
    with requests.Session() as s:
        doc = retrive_data(s)
        get_img(doc,s)
        viewstate = doc.xpath('//*[@id="j_id1:javax.faces.ViewState:0"]')[0].get('value')
        post_data['javax.faces.ViewState'] = viewstate

        id = doc.xpath('/html/body/form/div[1]/div[3]/div[1]/div/div[2]/div[4]/div/button')[0].get('id')
        post_data['javax.faces.source'] = id
        post_data[id] = id

        res = submit_form(s)
        while check_res(res) == False:
            doc = retrive_data(s)
            get_img(doc,s)
            res = submit_form(s)
        fill_data(res)


        return True


def main():
    if validate_input() and check_connection():
        start_session()
    else:
        exit()



if __name__ == "__main__":
    main()

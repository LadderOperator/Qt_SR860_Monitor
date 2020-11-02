import requests
import html

header = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "enctype": "multipart/form-data",
    "Content-Type": "text/plain;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    }


class SR860Device():
    ip = "<Empty>"
    url = "sr865req.htm"

    def __init__(self, ip_set, url_set='sr865req.htm'):
        self.ip = ip_set
        self.url = url_set

    def queryXYRT(self) -> dict:
        """
        Get X, Y, R, Theta value and unit
        """
        cmd = {"action": "monitor", "command": "MON"}
        payload = urlencode(cmd) + "\u0000"
        header["Origin"] = "http://%s" % self.ip
        header["Referer"] = "http://%s/" % self.ip
        req = requests.post(
            "http://%s/%s" % (self.ip, self.url),
            data=payload,
            headers=header,
            timeout=1
        )
        if req.status_code == 200:
            return XYRT_parse(req.text)
        else:
            return 42

    def queryOVLoad(self) -> dict:
        """
        Check input range overload
        """
        cmd = {"action": "query", "command": "CUROVLDSTAT?"}
        header["Origin"] = "http://%s" % self.ip
        header["Referer"] = "http://%s/" % self.ip
        payload = urlencode(cmd) + "\u0000"
        req = requests.post(
            "http://%s/%s" % (self.ip, self.url),
            data=payload,
            headers=header,
            timeout=1
        )
        # print(req.text)
        if req.status_code == 200:
            bitbool = {0: False, 1: True}
            try:
                code = req.text.split("=")[-1]
                code = int(code)
                overLoadStatus = {
                    "inputRange": bitbool[(code & 1 << 4) >> 4],
                    "extRefUnlocked": bitbool[(code & 1 << 3) >> 3],
                    "CH1Output": bitbool[(code & 1 << 0) >> 0],
                    "CH2Output": bitbool[(code & 1 << 1) >> 1],
                    "dataCH1Output": bitbool[(code & 1 << 8) >> 8],
                    "dataCH2Output": bitbool[(code & 1 << 9) >> 9],
                    "dataCH3Output": bitbool[(code & 1 << 10) >> 10],
                    "dataCH4Output": bitbool[(code & 1 << 11) >> 11]
                }
                return overLoadStatus
            except Exception as e:
                print(e)
                return 42
        else:
            return 42

    def querySensitivity(self) -> int:
        """
        Return sensitivity setting code (integer)
        """
        cmd = {"action": "query", "command": "SCAL?"}
        header["Origin"] = "http://%s" % self.ip
        header["Referer"] = "http://%s/" % self.ip
        payload = urlencode(cmd) + "\u0000"
        req = requests.post(
            "http://%s/%s" % (self.ip, self.url),
            data=payload,
            headers=header,
            timeout=1
        )
        if req.status_code == 200:
            try:
                return int(req.text.split("=")[-1])
            except Exception as e:
                print(e)
                return 42
        else:
            return 42

    def setSensitivity(self, code):
        """
        Set Sensitivity
        """
        cmd = {"action": "send", "command": "SCAL %s" % code}
        header["Origin"] = "http://%s" % self.ip
        header["Referer"] = "http://%s/" % self.ip
        payload = urlencode(cmd) + "\u0000"
        req = requests.post(
            "http://%s/%s" % (self.ip, self.url),
            data=payload,
            headers=header,
            timeout=1
        )
        if req.status_code == 200:
            return 0
        else:
            return 42

    def autoPhase(self):
        """
        Set auto phase, wait for 5 seconds
        """
        cmd = {"action": "send", "command": "APHS"}
        header["Origin"] = "http://%s" % self.ip
        header["Referer"] = "http://%s/" % self.ip
        payload = urlencode(cmd) + "\u0000"
        req = requests.post("http://%s/%s" % (self.ip, self.url),
            data=payload,
            headers=header,
            timeout=1
        )
        if req.status_code == 200:
            return 0
        else:
            return 42

    def checkIP(self) -> bool:
        """
        Check if device is available
        """
        try:
            cmd = {"action": "idinfo", "command": "ID"}
            header["Origin"] = "http://%s" % self.ip
            header["Referer"] = "http://%s/" % self.ip
            payload = urlencode(cmd) + "\u0000"
            print(payload)
            req = requests.post(
            "http://%s/%s" % (self.ip, self.url),
                data=payload,
                headers=header,
                timeout=1
            )

            print(req.text)
            if req.status_code == 200 and "Stanford Research" in html.unescape(req.text):
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


def urlencode(para_dict):
    return "&".join(["%s=%s" % (k, v) for k, v in para_dict.items()])


def XYRT_parse(rtext):
    rtext = html.unescape(rtext)
    rtext_list = rtext.strip().split(",")
    try:
        if len(rtext_list) == 12:
            rtext_dict = {
                "X": {
                    "val": float(rtext_list[1]),
                    "unit": rtext_list[2]
                },
                "Y": {
                    "val": float(rtext_list[4]),
                    "unit": rtext_list[5]
                },
                "R": {
                    "val": float(rtext_list[7]),
                    "unit": rtext_list[8]
                },
                "Theta": {
                    "val": float(rtext_list[10]),
                    "unit": rtext_list[11]
                },
            }
            return rtext_dict
        else:
            return 42
    except Exception as e:
        print(e)
        return 42

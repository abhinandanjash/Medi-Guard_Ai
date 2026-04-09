import urllib.request, re, json
url = "https://mixkit.co/free-stock-video/lush-green-valley-with-mountains-and-cloudy-sky-31846/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    html = urllib.request.urlopen(req).read().decode("utf-8")
    urls = re.findall(r'"url":"([^"]+\.mp4)"', html)
    if urls:
        print("Found URLs:")
        for u in set(urls):
            print(u)
    else:
        print("No match")
except Exception as e:
    print("Failed:", e)

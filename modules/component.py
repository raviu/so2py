#!/usr/bin/python 
#Filename: helloworld.py
import sys
import os
import subprocess
from lxml import etree as ET

#"/media/shafreen/source/public/turing-new/components/proxy-admin/org.wso2.carbon.proxyadmin/4.2.1"

def is_released_component(file_path):
        
    os.chdir(file_path)
    component_pom = ET.parse('pom.xml')
    component_artifact_id = component_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
    component_version = component_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
    component_parent_artifact_id = component_pom.xpath('/p:project/p:parent/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
    component_parent_version = component_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

    if not component_version:
        component_version = component_parent_version

    # Go to product releases ???
    os.chdir("../../../../product-releases")

    # Get all the chunks available
    proc = subprocess.Popen("ls", stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    chunks = out.split()

    # Find in all chunks
    released_chunk = None
    for chunk in chunks:
        os.chdir("./{0}/components".format(chunk))
        chunk_component_pom = ET.parse('pom.xml')
        module = chunk_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(component_artifact_id[0].text, component_version[0].text),\
                                namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
        if module:
            released_chunk = chunk
            os.chdir("../..")
            break
        
        os.chdir("../..")

    # See if the parent pom is released
    if released_chunk is None: 
        for chunk in chunks:
            os.chdir("./{0}/components".format(chunk))
            chunk_component_pom = ET.parse('pom.xml')
            module = chunk_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}$')]".format(component_parent_artifact_id[0].text),\
                                  namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

            if module:
                released_chunk = chunk
                os.chdir(module[0].text)

                chunk_parent_component_pom = ET.parse('pom.xml')
                module = chunk_parent_component_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(component_artifact_id[0].text, component_version[0].text),\
                                    namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

                os.chdir("../..")               
                break
                
            os.chdir("../..")
    
    if module:
        print "{0}_{1} ->".format(component_artifact_id[0].text, component_version[0].text), released_chunk
    else:
        print("Not a released COMPONENT")

file_path = input("Enter the path : ")
is_released_component(file_path)



    

    

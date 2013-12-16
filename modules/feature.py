#!/usr/bin/python 
#Filename: file.py
import os
import logging
import sys
from lxml import etree as ET

# This has to come from the main program
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s: %(levelname)s: %(message)s', filename ='../log/component.log', filemode = 'w',)

# Setting the output console too
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(message)s'))
logging.getLogger().addHandler(ch)

dependent_projects = set([])

def find_dependent_features(component_artifact_id):

    current_path = os.path.abspath('.')
    
    for root, subFolders, files in os.walk("/media/shafreen/source/public/turing-new/features"):
        if '.svn' in subFolders:
          subFolders.remove('.svn')

        if 'target' in subFolders:
          subFolders.remove('target')

        if 'src' in subFolders:
          subFolders.remove('src')

        #if 'test' in subFolders:
        #  subFolders.remove('test')

        if 'resources' in subFolders:
          subFolders.remove('resources')

        if 'nested-categories' in subFolders:
            subFolders.remove('nested-categories')

        for file_name in files:
            if file_name == 'pom.xml':
                os.chdir(root)
                feature_pom = ET.parse('pom.xml')
                element = feature_pom.xpath("/p:project/p:dependencies/p:dependency/p:artifactId[re:match(text(), '{0}$')]".format(component_artifact_id),\
                                        namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
                if element:
                    dependent_projects.add(root)

        os.chdir(current_path)

def refactor_depenedent_result():
    ''' Take care of older versions in the result list.'''
    
    project_dic = {}
    project_path_set = set([])
    
    for project in dependent_projects:
        project_tuble = project.rpartition('/')

        if project_tuble[0] in project_dic:
            existing_version = project_dic[project_tuble[0]]
            new_version = project_tuble[2]

            existing_version_int = existing_version.replace('.', '0')
            new_version_int = new_version.replace('.', '0')
            if int(new_version_int) > int(existing_version_int):
                project_dic[project_tuble[0]] = new_version
        else:
            project_dic[project_tuble[0]] = project_tuble[2]

    for key in project_dic.keys():
        project_path_set.add(key + "/" + project_dic[key])
        
    return project_path_set

def is_released_feature(file_path):
    ''' finds if a particular component is released or not. Implemenation is based on chunk-system
            If the component is released it returns the component version.'''

    try:    
        os.chdir(file_path)
        feature_pom = ET.parse('pom.xml')
        feature_artifact_id = feature_pom.xpath('/p:project/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
        feature_version = feature_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
        #feature_parent_artifact_id = feature_pom.xpath('/p:project/p:parent/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
        feature_parent_version = feature_pom.xpath('/p:project/p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
        feature_parent_rpath = feature_pom.xpath('/p:project/p:parent/p:relativePath', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

        # This is becuase we really can't say parent artifactId is similar to its folder name
        if feature_parent_rpath:
            os.chdir(feature_parent_rpath[0].text.rpartition('/')[0])
            feature_parent_rpath = os.path.abspath('.')
        else:
            raise Exception()
       
        if not feature_version:
            feature_version = feature_parent_version

        # Go to product releases ???
        os.chdir("/media/shafreen/source/public/turing-new/product-releases")

        # Get all the chunks available
        # proc = subprocess.Popen("ls", stdout=subprocess.PIPE, shell=True)
        # (out, err) = proc.communicate()
        # chunks = out.split()

        # Find in all chunks
        released_chunk = None
        for chunk in os.listdir("."):
            if os.path.isdir(chunk):
                os.chdir("./{0}/features".format(chunk))
                chunk_feature_pom = ET.parse('pom.xml')
                module = chunk_feature_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(feature_artifact_id[0].text, feature_version[0].text),\
                                        namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})
                if module:
                    released_chunk = chunk
                    os.chdir("../..")
                    break
                
                os.chdir("../..")

        # See if the parent pom is released
        if released_chunk is None: 
            for chunk in os.listdir("."):
                os.chdir("./{0}/features".format(chunk))
                chunk_feature_pom = ET.parse('pom.xml')

                feature_parent_chunk_path = feature_parent_rpath.replace('/media/shafreen/source/public/turing-new', '../../..')
                
                module = chunk_feature_pom.xpath("//p:modules/p:module[re:match(text(), '{0}$')]".format(feature_parent_chunk_path),\
                                      namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

                if module:
                    released_chunk = chunk
                    os.chdir(module[0].text)

                    chunk_parent_feature_pom = ET.parse('pom.xml')
                    module = chunk_parent_feature_pom.xpath("//p:modules/p:module[re:match(text(), '{0}/{1}')]".format(feature_artifact_id[0].text, feature_version[0].text),\
                                        namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

                    os.chdir("../..")               
                    break
                    
                os.chdir("../..")

        if module:
            logging.info("{0}_{1} -> ".format(feature_artifact_id[0].text, feature_version[0].text) + released_chunk)
            return feature_version[0].text
        else:
            logging.info("{0}_{1} -> ".format(feature_artifact_id[0].text, feature_version[0].text) + "Not a released FEATURE")
            return None
    except KeyboardInterrupt:
        logging.error('You cancled the is_released_component is operation. You might have to manually reset the state of platform. !!!')
    except:
        logging.error("Unexpected error:", sys.exc_info()[0])
        raise

def create_new_feature(file_path, feature_version, component_artifact_id, component_artifact_version):
    ''' If the component is released this operation will create a new component '''
            
    if feature_version is not None:
        os.chdir(file_path)

        # Build the component to see if it builds before doing anything
        if os.system('mvn clean install -Dmaven.test.skip=true') == 0:
            logging.info('feature builds successfully with new changes.')
        else:
            logging.error('could not build feature with the new changes.')
            raise Exception()

        # Get the new version of the coponent using the old version
        feature_versions = feature_version.rpartition('.')
        micro_version = feature_versions[2]
        int_micro_version = int(micro_version)
        int_micro_version += 1 

        new_feature_version = feature_versions[0] + feature_versions[1] + str(int_micro_version)

        # Go back to the root of the project
        os.chdir('..')
        if os.system('svn up') == 0:
            logging.info('successfully upated the local svn copy.')
        else:
            logging.error('failed to update the local svn copy.')
            raise Exception()

        # Make sure we have done changes to the latest existing version
        if not os.path.exists(new_feature_version):
            svn_mkdir_command = 'svn copy {0} {1}'.format(feature_version, new_feature_version)

            if os.system(svn_mkdir_command) == 0:
                os.chdir(new_feature_version)
                feature_pom = ET.parse('pom.xml')

                # Update the pom file..WHAT IF THERE IS NO VERSION ELEMENT ???
                feature_version = feature_pom.xpath('/p:project/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
                feature_version[0].text = new_feature_version

                feature_component_dependency = feature_pom.xpath("/p:project/p:dependencies/p:dependency/p:artifactId[re:match(text(), '{0}$')]".format(component_artifact_id),\
                                        namespaces={'p': 'http://maven.apache.org/POM/4.0.0', 're': 'http://exslt.org/regular-expressions'})

                dependency_element = feature_component_dependency[0].getparent()
                version_element = dependency_element.find('p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})

                if version_element is not None: 
                    version_element.text = component_artifact_version
                else:
                    new_version_element = ET.fromstring('<version>{0}</version>'.format(component_artifact_version))
                    dependency_element.append(new_version_element)
                
                feature_pom.write('pom.xml')

                logging.info('successfully created a new component version -> {0}'.format(new_feature_version))
                return os.path.abspath('.')
                    
            else:
                logging.error('failed to create a new component version -> {0}'.format(new_feature_version))
        else:
            logging.error('seems you have not done the changes to latest existing version !!!')

        return None
    
def mester_method(component_artifact_id, component_artifact_version):

    find_dependent_features(component_artifact_id)
    
    for feature_path in refactor_depenedent_result():
        feature_version = is_released_feature("/media/shafreen/source/public/turing-new/features/proxyadmin/org.wso2.carbon.proxyadmin.server.feature/4.2.1")
        print feature_version
        print create_new_feature('/media/shafreen/source/public/turing-new/features/proxyadmin/org.wso2.carbon.proxyadmin.server.feature/4.2.1', feature_version, component_artifact_id, component_artifact_version)
        
    

mester_method("org.wso2.carbon.proxyadmin", '4.2.2')

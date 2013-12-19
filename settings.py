# Location of platform inside code repository  
repo_location = '/home/ravi/WORK/RD/carbon/platform/branches/turing/'

# nexus details
nexus_url = 'http://maven.wso2.org/'
nexus_repo_name = 'wso2-public'

# Run order of modules, a tuple containing list of module class names
run_order = (
            'Test',
            'Test2',
            'Component'
            )


run_last = (
            {'command_name': 'svn', 'class_name': 'Svn'},
            )

# Location of platform inside code repository  
repo_location = ''#UPDATE_REPO_LOCATION

# nexus details
nexus_url = 'http://maven.wso2.org/'
nexus_repo_name = 'wso2-public'

# Run order of modules, a tuple containing list of module class names
run_order = (
            'Test',
            'Test2',
            'Component',
	    'Feature'
            )


run_last = (
            {'command_name': 'svn', 'class_name': 'Svn'},
            )

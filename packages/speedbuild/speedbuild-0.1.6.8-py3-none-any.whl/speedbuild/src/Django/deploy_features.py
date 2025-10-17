import ast

from ...src.Django.utils.deploy import getFeatureFromTemplate, read_yaml
from ...src.Django.utils.django_utils import ManageDjangoSettings, get_project_settings, updateMiddleware
from ...src.Django.utils.feature_dependencies import arrangeChunks, getCodeBlockNameAndType
from ...src.Django.utils.venv_utils import get_activated_venv
from ...utils.installDependencies import install_dependencies


def convertFromTemplateToFeature(project_path,template_path,template_name,appName,addAppNameToInstalledApps=False,venv=None):
    """
    re work split code
    template unpack should overwrite and replace old files
    """
    if venv == None:
        venv = get_activated_venv()

    #get app settings.py and update it
    settings_path,_ = get_project_settings(project_path)

    main_django_dir = settings_path.replace(project_path,"")
    if main_django_dir.startswith("/"):
        main_django_dir = main_django_dir[1:]
    
    # remove settings.py from main_django_dir
    if "/settings.py" in main_django_dir:
        main_django_dir = main_django_dir.replace("/settings.py","")

    main_django_dir = main_django_dir.strip()

    # copy and add feature files  
    app_name,template_root,merge_conflicts = getFeatureFromTemplate(template_path,project_path,template_name,main_django_dir,appName)

    
    config_name = template_name.split("_")[-1].replace("zip","").strip()
    template_yaml = read_yaml(f"{template_root}/sb_{config_name}.yaml")
    template_apps = template_yaml['settings']['installed_apps']

    if addAppNameToInstalledApps:
        template_apps.append(appName)


    template_selected_middleware, all_middleware_from_template =  template_yaml['settings']['middlewares']

    django_settings = ManageDjangoSettings(settings_path,venv)
    django_settings.getSettingsVariablesName()

 
    installed_apps_index = django_settings.blocks.index(django_settings.all_variables['INSTALLED_APPS'])
    installed_apps = django_settings.blocks[installed_apps_index]
    installed_apps = ast.literal_eval(installed_apps.split("=", 1)[1].strip())

    #add template apps to installed apps
    # check for duplicates
    for app in template_apps:
        if app not in installed_apps:
            installed_apps.append(app)

    # reconstruct installed apps
    new_installed_apps = "INSTALLED_APPS = [\n"
    for i in installed_apps:
        new_installed_apps += f"\t'{i}',\n"

    new_installed_apps += "]"

    django_settings.blocks[installed_apps_index] = new_installed_apps

    middleware_index = django_settings.blocks.index(django_settings.all_variables['MIDDLEWARE'])

    # update middleware
    # check for duplicates
    if len(template_selected_middleware) > 0:
        updated_middleware = updateMiddleware(
            template_selected_middleware,
            all_middleware_from_template,
            django_settings.blocks[middleware_index] 
        )

        # reconstruct MIDDLEWARE
        new_middlewares = "MIDDLEWARE = [\n"
        for i in updated_middleware:
            new_middlewares += f"\t'{i}',\n"

        new_middlewares += "]"

        # set middleware
        django_settings.blocks[middleware_index] = new_middlewares


    confs = template_yaml['settings']['configurations']

    new_conf = arrangeChunks(confs,[],[])

    for i in range(len(new_conf)):
        new_conf[i] = new_conf[i].replace("<sb_ext>",main_django_dir).replace("<sb_ext_app>",app_name)

    settings_imports = template_yaml['settings']['imports']

    # block = [block for block in django_settings.blocks if list(django_settings.all_variables.keys())[0] in block]
    import_insert_index = django_settings.blocks.index(django_settings.blocks_without_comments[0])
    
    for i in settings_imports:
        if i not in django_settings.setting_imports:
            django_settings.blocks.insert(import_insert_index,i)

    # print("conf is ", django_settings.all_variables.keys())
    for conf in new_conf:
        conf_name, _ = getCodeBlockNameAndType(conf)
        
        if conf_name.strip() in django_settings.all_variables.keys():
            # print("conf name is ", conf_name)
            # check if conf is different from the one in settings
            if conf != django_settings.all_variables[conf_name]:
                # TODO : Prompt the user to handle merge, add conflict markers
                # conflictCode = f"<<<<<<< SpeedBuild update \n{oldCode}\n=======\n{chunk}\n>>>>>>>"
                print("handle merging conf ", conf_name)
        else:
            if conf not in django_settings.blocks:
                django_settings.blocks.append(conf)
            # else:
            #     # check if conf is different from the one in settings
            #     # else manage merge conflict
            #     # TODO : Prompt the user to handle merge
            #     print("handle merging conf ", conf_name)

    settings_code = "\n\n".join(django_settings.blocks)

    # save settings
    with open(settings_path,"w") as settings:
         settings.write(settings_code)

    # install dev dependencies
    print("Installing Feature dependencies")
    install_dependencies(template_yaml['dependencies'],venv)

    print("Feature deployed Successfully")

    if len(merge_conflicts) > 0:
        for conflict in merge_conflicts:
            print(f"# {conflict}")
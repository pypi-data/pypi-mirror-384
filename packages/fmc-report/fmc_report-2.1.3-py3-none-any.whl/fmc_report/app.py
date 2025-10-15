import os
import secrets
import logging

import fmc_report.accessRules as accessRules
import csv

from pprint     import pprint
from flask      import Flask, render_template, request, redirect, session, url_for, send_file
from dotenv     import load_dotenv
from fireREST   import FMC
from typing     import Optional

import requests.exceptions
import fireREST.exceptions

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(16))
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

@app.errorhandler(500)
def internal_error(error):
    return render_template('error_pages/500.html', error=error), 500
@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.info('The index page has been accessed.')
    fmc: Optional[FMC] = None
    access_policy_list: list = []
    prefilter_policy_list: list = []

    if check_and_set_credentials():
        hostname, username, password = get_credentials_from_session()
        fmc = login(hostname, username, password)

    if not fmc:
        return redirect(url_for('fmc_login'))

    if request.method == 'GET':
        if fmc:
            domains = get_domains(fmc=fmc)
            return render_template('index.html', domains=domains)

    if request.method == 'POST':
        session['domain'] = request.form.get('domain')

        domains = get_domains(fmc=fmc)
        hostname, username, password = get_credentials_from_session()
        fmc = login(hostname=hostname, username=username, password=password, domain=session.get('domain'))
        access_policies = get_access_policies(fmc=fmc)
        prefilter_policies = get_prefilter_policies(fmc=fmc)

        for policy in access_policies:
            access_policy_list.append({"id": policy.get('id'), "name": policy.get('name')})

        for policy in prefilter_policies:
            prefilter_policy_list.append({"id": policy.get('id'), "name": policy.get('name')})

        app.logger.info(f'The domain {request.form.get("domain")} has been accessed.')

        return render_template('index.html',
                               domains=domains,
                               access_policy_list=access_policy_list,
                               prefilter_policy_list=prefilter_policy_list,
                               selected_domain=session.get('domain'),
                               selected_access_list=session.get('access_lists'))

    return redirect(url_for('fmc_login'))

@app.route('/login', methods=['GET', 'POST'])
def fmc_login():
    if request.method == "POST":
        session['hostname'] = request.form.get('hostname')
        session['username'] = request.form.get('username')
        session['password'] = request.form.get('password')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/tables', methods=['GET', 'POST'])
def fmc_tables():
    if request.method == 'POST':
        domains:list = []

        app.logger.info(f'Selected access_list: {request.form.get("access_lists")}')
        app.logger.info(f'Session access_lists: {session.get("access_lists")}')

        if request.form.get('access_lists'):
            session['access_lists'] = request.form.get('access_lists')
            session['prefilter_lists'] = None

        if request.form.get('prefilter_lists'):
            session['prefilter_lists'] = request.form.get('prefilter_lists')
            session['access_lists'] = None

        if check_and_set_credentials():
            hostname, username, password = get_credentials_from_session()
            fmc = login(hostname, username, password, domain=session.get('domain'))
            domains = get_domains(fmc=fmc)
            app.logger.info(f'The domains {domains} has been received.')
        access_policy_list, prefilter_policy_list, rules, prefilter_rules, network_group_list = get_data()
        current_access_list = get_access_list_name_from_id(
            access_list_id=session.get('access_list'),
            access_policy_list=access_policy_list
        )
        return render_template('tables.html',
                               domains=domains,
                               access_policy_list=access_policy_list,
                               prefilter_policy_list=prefilter_policy_list,
                               rules=rules,
                               network_group_list=network_group_list,
                               current_access_list=current_access_list,
                               selected_domain=session.get('domain'),
                               selected_access_list=session.get('access_lists'))
    return redirect(url_for('index'))

@app.route('/prefilter_table', methods=['GET', 'POST'])
def fmc_prefilter_table():
    if request.method == 'POST':
        domains:list = []

        app.logger.info(f'Selected access_list: {request.form.get("access_lists")}')
        app.logger.info(f'Session access_lists: {session.get("access_lists")}')

        if request.form.get('access_lists'):
            session['access_lists'] = request.form.get('access_lists')
            session['prefilter_lists'] = None

        if request.form.get('prefilter_lists'):
            session['prefilter_lists'] = request.form.get('prefilter_lists')
            session['access_lists'] = None

        if check_and_set_credentials():
            hostname, username, password = get_credentials_from_session()
            fmc = login(hostname, username, password, domain=session.get('domain'))
            domains = get_domains(fmc=fmc)
            app.logger.info(f'The domains {domains} has been received.')
        access_policy_list, prefilter_policy_list, rules, prefilter_rules, network_group_list = get_data()
        current_access_list = get_access_list_name_from_id(
            access_list_id=session.get('access_list'),
            access_policy_list=access_policy_list
        )
        return render_template('prefilter_table.html',
                               domains=domains,
                               access_policy_list=access_policy_list,
                               prefilter_policy_list=prefilter_policy_list,
                               rules=prefilter_rules,
                               network_group_list=network_group_list,
                               current_access_list=current_access_list,
                               selected_domain=session.get('domain'),
                               selected_access_list=session.get('access_lists'))
    return redirect(url_for('index'))

@app.route('/download', methods=['GET', 'POST'])
def fmc_download():
    current_directory = os.getcwd()
    if request.method == 'POST':
        access_policy_list, prefilter_policy_list, rules, prefilter_rules, network_group_list = get_data()
        current_access_list = get_access_list_name_from_id(
            access_list_id=session.get('access_lists'),
            access_policy_list=access_policy_list
        )
        csv_file_path = os.path.join(current_directory, f'{current_access_list}.csv')
        create_access_list_csv(data=rules, network_group_list=network_group_list, filename=f"{current_access_list}.csv")
        return send_file(csv_file_path, as_attachment=True, download_name=f"{current_access_list}.csv")

@app.route('/fmc_prefilter_download', methods=['GET', 'POST'])
def fmc_prefilter_download():
    current_directory = os.getcwd()
    if request.method == 'POST':
        access_policy_list, prefilter_policy_list, rules, prefilter_rules, network_group_list = get_data()
        current_prefilter_list = get_prefilter_list_name_from_id(
            prefilter_list_id=session.get('prefilter_lists'),
            prefilter_policy_list=prefilter_policy_list
        )
        csv_file_path = os.path.join(current_directory, f'{current_prefilter_list}.csv')
        create_prefilter_list_csv(data=prefilter_rules, network_group_list=network_group_list, filename=f"{current_prefilter_list}.csv")
        return send_file(csv_file_path, as_attachment=True, download_name=f"{current_prefilter_list}.csv")

def get_access_list_name_from_id(access_list_id: str, access_policy_list: list) -> Optional[str]:
    for access_policy in access_policy_list:
        if access_policy.get('id') == access_list_id:
            return access_policy.get('name')
    return "None"

def get_prefilter_list_name_from_id(prefilter_list_id: str, prefilter_policy_list: list) -> Optional[str]:
    for prefilter_policy in prefilter_policy_list:
        if prefilter_policy.get('id') == prefilter_list_id:
            return prefilter_policy.get('name')
    return "None"

def get_data():
    if check_and_set_credentials():
        access_rules = []
        prefilter_rules = []
        network_group_list = []

        hostname, username, password = get_credentials_from_session()
        fmc = login(hostname, username, password, domain=session.get('domain'))
        access_policy_list = get_access_policies(fmc=fmc)
        prefilter_policy_list = get_prefilter_policies(fmc=fmc)
        access_policy = session.get('access_lists')
        prefilter_policy = session.get('prefilter_lists')

        if access_policy:
            access_rules = get_access_rules(fmc=fmc, access_policy_id=access_policy)
            access_rules_list = accessRules.create_access_rules_from_dicts(access_rules)
            network_group_list = get_network_group_list(fmc=fmc, access_rules_list=access_rules_list)

        if prefilter_policy:
            prefilter_rules = get_prefilter_rules(fmc=fmc, prefilter_policy_id=prefilter_policy)
            network_group_list = get_network_group_list_from_prefilter(fmc=fmc, prefilter_rules_list=prefilter_rules)
            pprint(prefilter_rules)

        return access_policy_list, prefilter_policy_list, access_rules, prefilter_rules, network_group_list

def get_network_group_list(fmc, access_rules_list):
    network_group_list = []
    network_group_names = find_network_groups(access_rules_list=access_rules_list)
    for network_group_name in network_group_names:
        network_group = get_network_group(fmc=fmc, group_name=network_group_name)
        objects = []
        try:
            for obj in get_objects_from_network_group(network_group):
                objects.append(obj.get("name"))
            network_group_list.append({"name": network_group_name, "objects": objects})
        except Exception as error:
            app.logger.error(f"get_network_group_list: {error}")
    return network_group_list

def get_network_group_list_from_prefilter(fmc, prefilter_rules_list):
    network_group_list = []
    network_group_names = find_network_groups_in_prefilter(prefilter_rules_list=prefilter_rules_list)
    for network_group_name in network_group_names:
        network_group = get_network_group(fmc=fmc, group_name=network_group_name)
        objects = []
        try:
            for obj in get_objects_from_network_group(network_group):
                objects.append(obj.get("name"))
            network_group_list.append({"name": network_group_name, "objects": objects})
        except Exception as error:
            app.logger.error(f"get_network_group_list_from_prefilter: {error}")
    return network_group_list

def find_network_groups_in_prefilter(prefilter_rules_list):
    network_groups: set = set()
    for rule in prefilter_rules_list:
        try:
            if rule.get('sourceNetworks').get('objects'):
                for sourceNetworks in rule.get('sourceNetworks').get('objects'):
                    if sourceNetworks.get('type') == 'NetworkGroup':
                        network_groups.add(sourceNetworks.get('name'))
        except Exception as error:
            app.logger.error(f"find_network_groups_in_prefilter: {error}")
    return network_groups

def find_network_groups(access_rules_list: list[accessRules.AccessRule]):
    network_groups: set = set()
    for rule in access_rules_list:
        # print(rule.name)
        # print(type(rule.sourceNetworks.get('objects')))
        try:
            if rule.sourceNetworks.get('objects'):
                for sourceNetwork in rule.sourceNetworks.get('objects'):
                    # print(sourceNetwork)
                    if sourceNetwork.get('type') == 'NetworkGroup':
                        network_groups.add(sourceNetwork.get('name'))
        except Exception as error:
            app.logger.error(f"find_network_groups: {error}")
        # if rule.destinationNetworks.get('type') == 'NetworkGroup':
        #     print(rule.destinationNetworks.get('name'))
    return network_groups

def check_for_entry(current_list: list, entry: dict[str, list]):
    for list_entry in current_list:
        for key, value in entry.items():
            if key in list_entry and list_entry[key] == value:
                return True
    return False

def get_fmc() -> Optional[FMC]:
    fmc: Optional[FMC] = None
    try:
        if check_and_set_credentials():
            hostname, username, password = get_credentials_from_session()
            fmc = login(hostname, username, password)
    except Exception as error:
        app.logger.error(f"get_fmc: {error}")
    return fmc

def get_domains(fmc: FMC) -> Optional[list]:
    domains: list = []
    try:
        domains = fmc.system.info.domain.get()
        app.logger.info(f'The domains are {domains}')
    except Exception as error:
        app.logger.error(f"get_domains: {error}")
    return domains

def get_access_policies(fmc: FMC) -> Optional[list]:
    access_policies: list = []
    try:
        access_policies = fmc.policy.accesspolicy.get()
    except Exception as error:
        app.logger.error(f"get_access_policies: {error}")
    return access_policies

def get_prefilter_policies(fmc: FMC) -> Optional[list]:
    prefilter_policies = []
    try:
        prefilter_policies: list = fmc.policy.prefilterpolicy.get()
    except Exception as error:
        app.logger.error(f"get_prefilter_policies: {error}")
    return prefilter_policies

def get_access_rules(fmc: FMC, access_policy_id: str) -> Optional[list]:
    rules: list = []
    try:
        rules = fmc.policy.accesspolicy.accessrule.get(container_uuid=access_policy_id)
    except Exception as error:
        app.logger.error(f"get_access_rules: {error}")
    return rules

def get_prefilter_rules(fmc: FMC, prefilter_policy_id: str) -> Optional[list]:
    rules: list = []
    try:
        rules = fmc.policy.prefilterpolicy.accessrule.get(container_uuid=prefilter_policy_id)
        pprint(prefilter_policy_id)
    except Exception as error:
        app.logger.error(f"get_prefilter_rules: {error}")
    return rules

def get_network_group(fmc: FMC, group_name: str) -> Optional[dict]:
    network_group: dict = {}
    try:
        network_group = fmc.object.networkgroup.get(name=group_name)
    except Exception as error:
        app.logger.error(f"get_network_group: {error}")
    return network_group

def get_objects_from_network_group(network_group: dict) -> Optional[list]:
    objects: list = []
    try:
        objects = network_group.get('objects')
    except Exception as error:
        app.logger.error(f"get_objects_from_network_group: {error}")
    return objects

def check_and_set_credentials():
    try:
        if not check_for_session():
            if check_for_environment():
                environment_to_session()
                return True
            return False
        return True
    except Exception as error:
        app.logger.error(f"check_and_set_credentials: {error}")

def check_for_environment() -> bool:
    hostname = os.getenv("HOSTNAME")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    return all(var is not None for var in [hostname, username, password])

def environment_to_session():
    if check_for_environment():
        session["hostname"] = os.getenv("HOSTNAME")
        session["username"] = os.getenv("USERNAME")
        session["password"] = os.getenv("PASSWORD")

def check_for_session() -> bool:
    hostname, username, password = get_credentials_from_session()
    return all(var is not None for var in [hostname, username, password])

def get_credentials_from_session() -> (str, str, str):
    hostname = session.get('hostname')
    username = session.get('username')
    password = session.get('password')
    return hostname, username, password

def login(hostname: str, username: str, password: str, domain = "") -> Optional[FMC]:
    try:
        fmc = FMC(hostname=hostname, username=username, password=password, timeout=30)
        if domain != "":
            fmc = FMC(hostname=hostname, username=username, password=password, domain=domain, timeout=30)
        uuid = fmc.domain.get('uuid')
        return fmc
    except requests.exceptions.ConnectTimeout as exception:
        app.logger.error(f"login_connection_timeout: {exception}")
        return None
    except fireREST.exceptions.AuthError as exception:
        app.logger.error(f"login_auth_error: {exception}")
        return None

def create_access_list_csv(data, network_group_list: list, filename: str = "export.csv") -> None:
    current_directory = os.getcwd()
    csv_file_path = os.path.join(current_directory, filename)
    with open(csv_file_path, mode='w+', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Action',
                         'Name',
                         'Source Zones',
                         'Destination Zones',
                         'Source Networks',
                         'Destination Networks',
                         'Source Ports',
                         'Destination Ports',
                         'Dynamic Attribute',
                         'Applications',
                         'URLs'])

        for rule in data:
            row = []
            objects = []
            subobjects = []
            row.append(rule['action'])
            row.append(rule['name'])

            for object in rule.get('sourceZones', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('destinationZones', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('sourceNetworks', {'objects': [{'name': '-'}]}).get('objects'):
                if object.get('type') == 'NetworkGroup':
                    for network_group in network_group_list:
                        subobjects.append(', '.join(network_group.get('objects')))
                    objects.append(f"{object.get('name')}: {subobjects}")
                else:
                    objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []
            subobjects = []

            for object in rule.get('destinationNetworks', {'objects': [{'name': '-'}]}).get('objects'):
                if object.get('type') == 'NetworkGroup':
                    for network_group in network_group_list:
                        subobjects.append(', '.join(network_group.get('objects')))
                    objects.append(f"{object.get('name')}: {subobjects}")
                else:
                    objects.append(object.get('name'))
            row.append(',\n'.join(objects))

            objects = []
            subobjects = []

            for object in rule.get('sourcePorts', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('destinationPorts', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('sourceSecurityGroupTags', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('applications', {'applications': [{'name': '-'}]}).get('applications'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('urls', {'urlCategoriesWithReputation': [{'category': {'name': '-'}}]}).get('urlCategoriesWithReputation'):
                objects.append(object.get('category').get('name'))
            row.append(',\n'.join(objects))
            objects = []

            writer.writerow(row)

    # output.seek(0)
    # return output.getvalue()

def create_prefilter_list_csv(data, network_group_list: list, filename: str = "export.csv") -> None:
    current_directory = os.getcwd()
    csv_file_path = os.path.join(current_directory, filename)
    with open(csv_file_path, mode='w+', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Rule Type',
                         'Name',
                         'Source Interface Objects',
                         'Destination Interface Objects',
                         'Source Networks',
                         'Destination Networks',
                         'Source Port',
                         'Destination Port',
                         'VLAN Tag',
                         'Action',
                         'Tunnel Zone'])

        for rule in data:
            row = []
            objects = []
            subobjects = []
            row.append(rule['ruleType'])
            row.append(rule['name'])

            for object in rule.get('sourceInterfaces', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('destinationInterfaces', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('sourceNetworks', {'objects': [{'name': '-'}]}).get('objects'):
                if object.get('type') == 'NetworkGroup':
                    for network_group in network_group_list:
                        subobjects.append(', '.join(network_group.get('objects')))
                    objects.append(f"{object.get('name')}: {subobjects}")
                else:
                    objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []
            subobjects = []

            for object in rule.get('destinationNetworks', {'objects': [{'name': '-'}]}).get('objects'):
                if object.get('type') == 'NetworkGroup':
                    for network_group in network_group_list:
                        subobjects.append(', '.join(network_group.get('objects')))
                    objects.append(f"{object.get('name')}: {subobjects}")
                else:
                    objects.append(object.get('name'))
            row.append(',\n'.join(objects))

            objects = []
            subobjects = []

            for object in rule.get('sourcePorts', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            for object in rule.get('destinationPorts', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            # for object in rule.get('sourceSecurityGroupTags', {'objects': [{'name': '-'}]}).get('objects'):
            #     objects.append(object.get('name'))
            # row.append(',\n'.join(objects))
            # objects = []

            for object in rule.get('vlanTags', {'objects': [{'name': '-'}]}).get('objects', [{'name': '-'}]):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            # for object in rule.get('applications', {'applications': [{'name': '-'}]}).get('applications'):
            #     objects.append(object.get('name'))
            # row.append(',\n'.join(objects))
            # objects = []

            row.append(rule['action'])

            # for object in rule.get('urls', {'urlCategoriesWithReputation': [{'category': {'name': '-'}}]}).get('urlCategoriesWithReputation'):
            #     objects.append(object.get('category').get('name'))
            # row.append(',\n'.join(objects))
            # objects = []

            for object in rule.get('tunnelZone', {'objects': [{'name': '-'}]}).get('objects'):
                objects.append(object.get('name'))
            row.append(',\n'.join(objects))
            objects = []

            writer.writerow(row)

    # output.seek(0)
    # return output.getvalue()

if __name__ == '__main__':
    app.run()

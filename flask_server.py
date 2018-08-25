import json
import logging
import os
import requests
from flask import Flask, request
from keystoneauth1.identity import v3
from keystoneauth1 import session
from mistralclient.api import client as mistral_client

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

SCALE_UP_WF_NAME = 'ppg_scale_up'
SCALE_DOWN_WF_NAME = 'placeholder'

auth = v3.Password(auth_url=os.environ['OS_AUTH_URL'],
                   username=os.environ['OS_USERNAME'],
                   password=os.environ['OS_PASSWORD'],
                   project_name=os.environ['OS_PROJECT_NAME'],
                   user_domain_id='default',
                   project_domain_name=os.environ['OS_PROJECT_DOMAIN_NAME'])
sess = session.Session(auth=auth, verify=False)
CLIENT = mistral_client.client(session=sess,
                               mistral_url='http://192.168.100.10:8989/v2')
LOG.info("Mistral client authorized")

app = Flask(__name__)


def get_workflow_id(client, wf_name):
    LOG.info("Getting workflow: %s" % wf_name)
    wfs = client.workflows.list()
    wfs = map(lambda w: w.to_dict(), wfs)

    try:
        wf_id = filter(lambda w: w['name'] == wf_name, wfs)[0]['id']
        return wf_id
    except IndexError as e:
        LOG.warning("No such workflow: %s" % name)
        return


def execute_workflow(client, wf_id, wf_input):
    LOG.info("Execution workflow %s with input: %s" % (wf_id, wf_input))
    client.executions.create(workflow_identifier=wf_id,
                             workflow_input=wf_input)



@app.route('/alarm/vm_create', methods=['POST'])
def receive_alarm_data():
    data = request.get_json()
    traits = data['reason_data']['event']['traits']

    _, _, instance_id = filter(lambda t: t[0]=='instance_id', traits)[0]
    wf_id = get_workflow_id(CLIENT, SCALE_UP_WF_NAME)
    if wf_id:
        import time
        time.sleep(5)
        data = {"instance_id": instance_id}
        execute_workflow(CLIENT, wf_id, data)
        LOG.info("Workflow executed")
        return "OK"

    LOG.warning("Workflow %s failed to execute" % wf_id)
    return "NOK"


if __name__ == '__main__':
    app.run(host='192.168.100.10', port=5002)

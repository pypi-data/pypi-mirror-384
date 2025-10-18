import json
import logging
import os
import sys
import subprocess

import otupy as oc2

from otupy.actuators.ctxd.ctxd_actuator_docker import CTXDActuator_docker
from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.actuators.ctxd.ctxd_actuator_openstack import CTXDActuator_openstack
from otupy.actuators.ctxd.ctxd_actuator_kubernetes import CTXDActuator_kubernetes
import otupy.profiles.ctxd as ctxd

# Declare the logger name
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.WARNING)
# Create stdout handler for logging to the console 
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.WARNING)
stdout_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True))
hdls = [ stdout_handler ]
# Add both handlers to the logger
logger.addHandler(stdout_handler)




def main():


    try:
        #read the configuration file
        configuration_file = os.path.dirname(os.path.abspath(__file__))+"/configuration.json"
        with open(configuration_file, 'r') as file:
            configuration_parameters = json.load(file)
        
        #process = subprocess.Popen('source ./matteo-astrid.rc', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #stdout, stderr = process.communicate()

        actuators = {}
        
        for element in configuration_parameters['clusters']:
            if (element["type"] == "openstack"):
                #CTXDActuator_openstack is able to find vm connected to the cloud service openstack
                actuators[(ctxd.Profile.nsid,element['asset_id'])] = CTXDActuator_openstack(domain= None, 
                                                                            asset_id= element['asset_id'],
                                                                            hostname = element['hostname'],
                                                                            ip = element['ip'],
                                                                            port = element['port'],
                                                                            protocol = element['protocol'],
                                                                            endpoint = element['endpoint'],
                                                                            transfer = element['transfer'],
                                                                            encoding = element['encoding'],
                                                                            file_enviroment_variables = element['file_enviroment_variables'])
            
            elif (element["type"] == "kubernetes"):
                #CTXDActuator_kubernetes is able to find the connected VM, containers and namespaces to the kuberenetes cloud
                actuators[(ctxd.Profile.nsid, element['asset_id'])] = CTXDActuator_kubernetes(domain= None,
                                                                                                asset_id= element['asset_id'],
                                                                                                hostname = element['hostname'],
                                                                                                actuators = actuators,
                                                                                                ip = element['ip'],
                                                                                                port = element['port'],
                                                                                                protocol = element['protocol'],
                                                                                                endpoint = element['endpoint'],
                                                                                                transfer = element['transfer'],
                                                                                                encoding = element['encoding'],
                                                                                                namespace = element['namespace'],
                                                                                                config_file = element['config_file'],
                                                                                                kube_context = element['kube_context'])
            
            elif(element["type"] == "docker"):
                #CTXDActuator_docker is able to find the hosting VM and managed containers
                actuators[(ctxd.Profile.nsid, element['asset_id'])] = CTXDActuator_docker(domain= None,
                                                                                                asset_id= element['asset_id'],
                                                                                                hostname = element['hostname'],
                                                                                                ip = element['ip'],
                                                                                                port = element['port'],
                                                                                                protocol = element['protocol'],
                                                                                                endpoint = element['endpoint'],
                                                                                                transfer = element['transfer'],
                                                                                                encoding = element['encoding'],
                                                                                                actuators = actuators)

            else:
                raise Exception("type must be equal to openstack or kubernetes")

        #-----------------------RUN THE CONSUMER with multiple actuators-----------------------------------------
        c = oc2.Consumer("testconsumer", actuators, JSONEncoder(), HTTPTransfer(configuration_parameters['consumer']['ip'],
                                                                                configuration_parameters['consumer']['port'],
                                                                                configuration_parameters['consumer']['endpoint']))
        c.run()  



    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    
		main()
              

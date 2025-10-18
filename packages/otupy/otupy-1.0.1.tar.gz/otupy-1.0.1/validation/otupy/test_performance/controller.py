#!../../../.venv/bin/python3
# Example to use the OpenC2 library
#

import logging
import sys

import otupy as oc2

from otupy.encoders.json import JSONEncoder
from otupy.transfers.http import HTTPTransfer
from otupy.transfers.mqtt import MQTTTransfer, OpenC2Role

import otupy.profiles.slpf as slpf
import otupy.profiles.dumb as dumb

from helpers import load_json

#logging.basicConfig(filename='openc2.log',level=logging.DEBUG)
#logging.basicConfig(stream=sys.stdout,level=logging.INFO)
#logger = logging.getLogger('openc2producer')
logger = logging.getLogger()
# Ask for 4 levels of logging: INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# Add file logger
file_handler = logging.FileHandler("controller.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(oc2.LogFormatter(datetime=True,name=True, datefmt='%t'))
logger.addHandler(file_handler)

command_path_good = "openc2-commands-good"
NUM_TESTS = 100

def main():
	logger.info("Creating Producer")

#p = oc2.Producer("producer.example.net", JSONEncoder(), HTTPTransfer("127.0.0.1", 8080))
	p = oc2.Producer("myproducer", JSONEncoder(), MQTTTransfer("150.145.8.217", 1883,  OpenC2Role.Producer, device_id="myproducer"))


	cmd_list = load_json(command_path_good) 
	for i in range(1, NUM_TESTS+1):
		print("Running test #", i)
		for c in cmd_list:
			cmd = oc2.Encoder.decode(oc2.Command, c)
	
			logger.info("Sending command: %s", cmd)
			resp = p.sendcmd(cmd, consumers=["testconsumer"])
#			logger.info("Got response: %s", resp)
			logger.info("Got response: ")


if __name__ == '__main__':
	main()

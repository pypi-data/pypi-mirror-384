""" HTTP Transfer Protocol

	This module defines implementation of the `Transfer` interface for the 
  	HTTP/HTTPs protocols. This implementation is mostly provided for 
	research and development purposes, but it is not suitable for production
	environments.

	The implementation follows the Specification for Transfer of OpenC2 Messages via HTTPS
	Version 1.1, which is indicated as the "Specification" in the following.
"""
import dataclasses
import requests
import logging
import copy

from flask import Flask, request, make_response
from werkzeug.exceptions import HTTPException, UnsupportedMediaType

import otupy as oc2
from otupy.transfers.http.message import Message


logger = logging.getLogger(__name__)
""" The logging facility in otupy """

class HTTPTransfer(oc2.Transfer):
	""" HTTP Transfer Protocol

		This class provides an implementation of the Specification. It builds on Flask and so it is not
		suitable for production environments.

		Use `HTTPTransfer` to build OpenC2 communication stacks in `Producer` and `Consumer`.
	"""
	def __init__(self, host, port = 80, endpoint = '/.well-known/openc2', usessl=False):
		""" Builds the `HTTPTransfer` instance

			The `host` and `port` parameters are used either for selecting the remote server (`Producer`) or
			for local binding (`Consumer`). This implementation only supports TCP as transport protocol.
			:param host: Hostname or IP address of the OpenC2 server.
			:param port: Transport port of the OpenC2 server.
			:param endpoint: The remote endpoint to contact the OpenC2 server (`Producer` only).
			:param usessl: Enable (`True`) or disable (`False`) SSL. Internal use only. Do not set this argument,
				use the `HTTPSTransfer` instead.
		"""
		self.host = host
		self.port = port
		self.endpoint = endpoint
		self.scheme = 'https' if usessl else 'http'
		self.url = f"{self.scheme}://{host}:{port}{endpoint}"
		self.ssl_context = None

	def _tohttp(self, msg, encoder):
		""" Convert otupy `Message` to HTTP `Message` """
		m = Message()
		m.set(msg)

		# Encode the data
		if encoder is not None:
			data = encoder.encode(m)
		else:
			data = oc2.Encoder().encode(m)

		return data

	def _fromhttp(self, hdr, data):
		""" Convert HTTP `Message` to otupy `Message` """

		# TODO: Check the HTTP headers for version/encoding
		content_type =hdr['Content-type']

		if not content_type.removeprefix('application/').startswith(oc2.Message.content_type):
			raise UnsupportedMediaType("Unsupported content type")

		enctype = (content_type.removeprefix('application/'+oc2.Message.content_type+'+').split(';')[0]).strip()
		try:
			encoder = oc2.Encoders[enctype].value
		except KeyError:
			raise UnsupportedMediaType("Unsupported encoding scheme: " + enctype)

		# HTTP processing to extract the headers
		# and the transport body
		if encoder.is_binary:
			data_text = data.decode('utf-8') #binary data (cbor)
		else:
			data_text = data # text data 
		msg = encoder.decode(data_text, Message).get()
		msg.content_type = hdr['Content-type'].removeprefix('application/').split('+')[0]
		msg.version = oc2.Version.fromstr(hdr['Content-type'].split(';')[1].removeprefix("version="))
		msg.encoding = encoder

		try:
			msg.status = msg.content['status']
		except:
			msg.status = None


		return msg, encoder


	# This function is used to send an HTTP request
	def send(self, msg, encoder):
		""" Sends OpenC2 message

			This method implements the required `Transfer` interface to send message to an OpenC2 server.
			:param msg: The message to send (otupy `Message`).
			:param encoder: The encoder to use for encoding the `msg`.
			:return: An OpenC2  response (`Response`).
		"""
		# The HTTP Transfer Specification requires the "to" field, even if this is not mandatory for the Language Specification.
		# If no "to" field is provided, use the destination host.
		if msg.to is None:
			msg.to = []  
		if not msg.to:
			msg.to.append(self.host)

		# Convert the message to the specific HTTP representation
		openc2data = self._tohttp(msg, encoder)

		# Building the requested headers for the Request
		content_type = f"application/{msg.content_type}+{encoder.getName()};version={msg.version}"
		date = msg.created if msg.created else int(oc2.DateTime())
		openc2headers={'Content-Type': content_type, 
							'Accept': content_type, 
							'Content-Encoding': encoder.getName(),
							'Date': oc2.DateTime(date).httpdate()}

		logger.info("Sending to %s", self.url)
		logger.info("HTTP Request Content:\n%s", openc2data)

		# Send the OpenC2 message and get the response
		if self.scheme == 'https':
			logger.warning("Certificate validation disabled!")
		response = requests.post(self.url, data=openc2data, headers=openc2headers, verify=False)
		logger.info("HTTP got response: %s", response)
		logger.info("HTTP Response Content:\n%s", response.text)
	
		# TODO: How to manage HTTP response code? Can we safely assume they always match the Openc2 response?
		try:
			content_encoding = response.headers['Content-Encoding']
			if content_encoding is not None and oc2.Encoders[content_encoding].value.is_binary:
				logger.debug("Content is not text!")
				msg, encoder = self._fromhttp(response.headers, response.content)
			else:
				if response.text != "":
					msg, encoder = self._fromhttp(response.headers, response.text)
				else:
					msg = None
		except ValueError as e:
			msg = oc2.Message(oc2.Content())
			msg.status = response.status_code
			logger.error("Unable to parse data: >%s<", response.text)
			logger.error(str(e))

		return msg

	# This function is used to prepare the headers and content in a response
	def _respond(self, msg, encoder):
		""" Responds to received OpenC2 message """

		headers = {}
		if msg is not None:
			if encoder is not None:
				content_type = f"application/{msg.content_type}+{encoder.getName()};version={msg.version}"
			else:	
				content_type = f"text/plain"
			headers['Content-Type']= content_type
			# This is not required by the HTTP Transfer specification, but
			# it helps manage binary data
			headers['Content-encoding']=encoder.getName()
			date = msg.created if msg.created else int(oc2.DateTime())
			data = self._tohttp(msg, encoder)
		else:
			content_type = None
			data = None
			date = int(oc2.DateTime())

		# Date is currently autmatically inserted by Flask (probably 
		# after I used 'make_response')
		#headers['Date'] = oc2.DateTime(date).httpdate()

		return headers, data

	def _recv(self, headers, data):
		""" Retrieve HTTP messages
			
			Internal function to convert Flask data into otupy `Message` structure and `Encoder`.
			The `encoder` is derived from the HTTP header, to provide the ability to manage multiple
			clients that use different encoding formats.
			:param headers: HTTP headers.
			:param data: HTTP body.
			:return: An otupy `Message` (first) and an `Encoder` instance (second).
		"""

		logger.info("Received HTTP body: \n%s", str(data))
		logger.debug(data)
		msg, encoder = self._fromhttp(headers, data)
  			
		return msg, encoder
	
	def receive(self, callback, encoder):
		""" Listen for incoming messages

			This method implements the `Transfer` interface to listen for and receive OpenC2 messages.
			The internal implementation uses `Flask` as HTTP server. The method invokes the `callback`
			for each received message, which must be provided by a `Producer` to properly dispatch 
			`Command`s to the relevant server(s). It also takes an `Encoder` that is used to create
			responses to `Command`s encoded with unknown encoders.
			:param callback: The function that is invoked to process OpenC2 messages.
			:param encoder: Default `Encoder` instance to respond to unknown or wrong messages.
			:return :None
		"""
		app = Flask(__name__)
		app.config['OPENC2']=self
		app.config['CALLBACK']=callback
		app.config['ENCODER']=encoder

		@app.route(self.endpoint, methods=['POST'])
		def _consumer():
			""" Serving endpoint for `Flask` """
			server = app.config['OPENC2']
			callback = app.config['CALLBACK']
			encoder=app.config['ENCODER']
			
			try:
				cmd, encoder = server._recv(request.headers, request.data)
				# TODO: Add the code to answer according to 'response_requested'
			except UnsupportedMediaType as e:
				# We were not able to understand the OpenC2 Message. 
				#	We must include "to" to be compliant; we'll use the client address.
				logger.warn("Unsupported MediaType: discarding request")
				content = oc2.Response(status=oc2.StatusCode.BADREQUEST, status_text=str(e))
				resp = oc2.Message(content)
				resp.content_type = oc2.Message.content_type
				resp.to = [ str(request.remote_addr) ]
				resp.version = oc2.Message.version
				resp.encoder = encoder
				resp.status=oc2.StatusCode.BADREQUEST
				resp.to = [ str(request.remote_addr) ]
			except oc2.EncoderError as e:
				logger.warn("Unable to understand the request: discarding")
				# TODO: Find better formatting (what should be returned if the request is not understood?)
				content = oc2.Response(status=oc2.StatusCode.BADREQUEST, status_text=str(e))
				resp = oc2.Message(content)
				resp.content_type = oc2.Message.content_type
				resp.version = oc2.Message.version
				resp.encoder = encoder
				resp.status=oc2.StatusCode.BADREQUEST
				# Partial decoding of the OpenC2 message is trickly with the current encoder,
				# hence it is not implemented. A non-HTTP exception means no fields in the 
				# OpenC2 message were read (this might be improved in the future according to
				# the LS requirements.
				resp.to = [ str(request.remote_addr) ]
			# WARNING: The following code catch any exception and may prevent debugging
			except Exception as e:
				# TODO: Find better formatting (what should be returned if the request is not understood?)
				logger.warn("Internal error: discarding request. Reason: %s", e)
				content = oc2.Response(status=oc2.StatusCode.INTERNALERROR, status_text=str(e))
				resp = oc2.Message(content)
				resp.content_type = oc2.Message.content_type
				resp.version = oc2.Message.version
				resp.encoder = encoder
				resp.status=oc2.StatusCode.INTERNALERROR
				resp.to = [ str(request.remote_addr) ]
			else:
				logger.info("Received command: %s", cmd)
				resp = callback(cmd)

			
			logger.info("Got response: %s", resp)
			
			# TODO: Set HTTP headers as appropriate
			hdrs, data = server._respond(resp, encoder)
			logger.info("Sending response:\n%s", data)
			httpresp = make_response(data if data is not None else "") 
			httpresp.headers = hdrs

			if data is None:
				resp_code = 200
			else:
				resp_code = resp.status.value

			return httpresp, resp_code

		app.run(debug=True, host=self.host, port=self.port, ssl_context=self.ssl_context)


class HTTPSTransfer(HTTPTransfer):
	""" HTTP Transfer Protocol with SSL

		This class provides an implementation of the Specification. It builds on Flask and so it is not
		suitable for production environments.

		Use `HTTPSTransfer` to build OpenC2 communication stacks in `Producer` and `Consumer`.
		Usage and methods of `HTTPSTransfer` are semanthically the same as for `HTTPTransfer`.
	"""
	def __init__(self, host, port = 443, endpoint = '/.well-known/openc2'):
		""" Builds the `HTTPSTransfer` instance

			The `host` and `port` parameters are used either for selecting the remote server (`Producer`) or
			for local binding (`Consumer`). This implementation only supports TCP as transport protocol.
			:param host: Hostname or IP address of the OpenC2 server.
			:param port: Transport port of the OpenC2 server.
			:param endpoint: The remote endpoint to contact the OpenC2 server (`Producer` only).
		"""
		HTTPTransfer.__init__(self, host, port, endpoint, usessl=True)
		self.ssl_context = "adhoc"



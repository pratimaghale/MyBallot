# -*- coding: utf-8 -*-
import random
import logging
import json
import sys
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response, IntentRequest
import requests
from ask_sdk_model.services.monetization import (
    EntitledState, PurchasableState, InSkillProductsResponse, Error,
    InSkillProduct)
from ask_sdk_model.interfaces.monetization.v1 import PurchaseResult
from ask_sdk_model.interfaces.connections import SendRequestDirective
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.api_client import DefaultApiClient

#Skill name and help prompts
SKILL_NAME = "My Ballot"
PROMPT = "Sorry My Ballot skill can't help you with that."
STOP_MESSAGE = "Thanks for using My Ballot. Goodbye!"

#For Google Civics API
API_KEY = 'AIzaSyDwOfoDKzlycJhNBXu2qGK-qXEd5rmEG4g'
HOST = "https://www.googleapis.com/civicinfo/v2/"

# sb = SkillBuilder()
sb = CustomSkillBuilder(api_client=DefaultApiClient())
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Built-in Intent Handlers

class LaunchHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return (is_request_type("LaunchRequest")(handler_input))
    def handle(self, handler_input):
        logger.info("In LaunchHandler")
        apiAccessToken = handler_input.request_envelope.context.system.api_access_token
        speech = "Welcome to my ballot. Please specify a U.S. address to learn about elections near you."
        handler_input.response_builder.speak(speech).ask("Please specify an address")
        return handler_input.response_builder.response

class AddressIntentHandler(AbstractRequestHandler):
    """Handler for GetAddress Intent. This handles the case when user gives their address."""
    def can_handle(self, handler_input):
        return  (is_intent_name("AddressIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In AddressIntentHandler")
        address = handler_input.request_envelope.request.intent.slots["address"].value  #get address that the user provided
        session_attr = dict({'address':address})
        handler_input.attributes_manager.session_attributes = session_attr #save it to the session attributes
        speech = "Thank you. What would you like to hear? You can say upcoming elections, polling stations, or candidates."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

class ElectionIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""
    def can_handle(self, handler_input):
        return  (is_intent_name("ElectionIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In ElectionIntentHandler")
        session_attr = handler_input.attributes_manager.session_attributes
        address = session_attr["address"] #get address provided by the user in the beginning of the session
        #create the Google civics path to hit; Get the incoming election details
        path = '%svoterinfo?address=%s&key=%s' %(HOST,address,API_KEY)
        response = requests.get(path)
        data = response.json()
        if 'election' in data:
            election = data["election"]["name"]
            electionDay = data["election"]["electionDay"]
            speech = "You have following upcoming elections: %s on %s. Would you like to hear more? Say Polling Stations or Candidates." %(election,electionDay)
        else:
            speech = "You have no upcoming elections. Please try again later."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

class PollingIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""
    def can_handle(self, handler_input):
        return  is_intent_name("PollingIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In PollingIntentHandler")
        session_attr = handler_input.attributes_manager.session_attributes
        address = session_attr["address"]
        path = '%svoterinfo?address=%s&key=%s' %(HOST,address,API_KEY)
        response = requests.get(path)
        data = response.json()
        # for every polling station in the incoming election details data
        if 'pollingLocations' in data:
            pollingLocations = data["pollingLocations"]
            pollinglocation = ""
            for pl in pollingLocations:
                pollinglocation = pollinglocation + pl["address"]["locationName"] + " at "+ pl["address"]["line1"]+". "
            speech = "Here are the polling stations: %s If you want to hear more, say candidates or election date." %(pollinglocation)
        else:
            speech = "You have no polling stations around you. Make sure there is an upcoming election."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

class CandidateIntentHandler(AbstractRequestHandler):
    """Handler for Skill Launch and GetNewFact Intent."""
    def can_handle(self, handler_input):
        return  is_intent_name("CandidateIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In CandidateIntentHandler")
        session_attr = handler_input.attributes_manager.session_attributes
        address = session_attr["address"]
        path = '%svoterinfo?address=%s&key=%s' %(HOST,address,API_KEY)
        response = requests.get(path)
        data = response.json()

        # for every contest, ensure it's a national level election and canidate
        if 'contests' in data:
            contests = data["contests"]
            candidates = ""
            for c in contests:
                for key in c:
                    if key == "level":
                        if c[key][0] == 'country':
                            candidates = candidates+ " For the office of "+c["office"]+" the candidates are "
                            for can in c["candidates"]:
                                candidates = candidates + can["name"] +" of "+can["party"]+". "

            speech = "Here are the candidates: %s  If you want to hear more, say polling stations or election date." %(candidates)
        else:
            speech = "There are no candidates at the moment. Make sure there is an upcoming election."
        handler_input.response_builder.speak(speech).ask(speech)
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In HelpIntentHandler")
        if handler_input.attributes_manager.session_attributes is none:
            HELP_PROMPT = PROMPT + " What would you like to hear? You can say upcoming elections, polling stations, or candidates."
        else:
            HELP_PROMPT = PROMPT +" Please specify a U.S. address to learn about elections near you."

        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_PROMPT)
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        logger.info("In CancelOrStopIntentHandler")

        handler_input.response_builder.speak(STOP_MESSAGE)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.
    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        if "address" in handler_input.attributes_manager.session_attributes:
            HELP_PROMPT = PROMPT + " What would you like to hear? You can say upcoming elections, polling stations, or candidates."
        else:
            HELP_PROMPT = PROMPT +" Please specify a U.S. address to learn about elections near you."
        handler_input.response_builder.speak(HELP_PROMPT).ask(
            HELP_PROMPT)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)
        if "address" in handler_input.attributes_manager.session_attributes:
            HELP_PROMPT = PROMPT + " What would you like to hear? You can say upcoming elections, polling stations, or candidates."
        else:
            HELP_PROMPT = PROMPT +" Please specify a U.S. address to learn about elections near you."
        handler_input.response_builder.speak(EXCEPTION_MESSAGE).ask(
            HELP_PROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        logger.debug("Alexa Response: {}".format(response))


# Register intent handlers
sb.add_request_handler(LaunchHandler())
sb.add_request_handler(AddressIntentHandler())
sb.add_request_handler(ElectionIntentHandler())
sb.add_request_handler(PollingIntentHandler())
sb.add_request_handler(CandidateIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# TODO: Uncomment the following lines of code for request, response logs.
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()

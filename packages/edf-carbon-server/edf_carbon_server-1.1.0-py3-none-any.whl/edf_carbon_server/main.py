"""Carbon server entrypoint"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from aiohttp.web import Application, Request, run_app
from edf_carbon_core.concept import Case, Constant, Event
from edf_fusion.concept import Identity, Info
from edf_fusion.helper.config import ConfigError
from edf_fusion.helper.logging import get_logger
from edf_fusion.server.auth import FusionAuthAPI, get_fusion_auth_api
from edf_fusion.server.case import FusionCaseAPI
from edf_fusion.server.constant import FusionConstantAPI
from edf_fusion.server.event import FusionEventAPI
from edf_fusion.server.info import FusionInfoAPI
from edf_fusion.server.storage import get_fusion_storage

from .__version__ import version
from .api import (
    attach_case_impl,
    create_case_impl,
    enumerate_cases_impl,
    retrieve_case_impl,
    setup_api,
    update_case_impl,
)
from .config import CarbonServerConfig
from .pubsub import setup_pubsub
from .storage import Storage

_LOGGER = get_logger('server.main', root='carbon')


async def _authorize_impl(
    identity: Identity, request: Request, context: dict
) -> bool:
    """Authorize implementation"""
    storage = get_fusion_storage(request)
    case_guid = context.get('case_guid')
    if not case_guid:
        return True
    case = await storage.retrieve_case(case_guid)
    if not case:
        _LOGGER.warning("case not found!")
        return False
    fusion_auth_api = get_fusion_auth_api(request)
    can_access = fusion_auth_api.can_access_case(identity, case)
    if not can_access:
        return False
    case_open_check = context.get('case_open_check')
    if case_open_check and case.closed:
        _LOGGER.warning("case closed!")
        return False
    return can_access


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="Carbon API Server")
    parser.add_argument(
        '--config',
        '-c',
        type=Path,
        default=Path('carbon.yml'),
        help="Carbon server configuration file",
    )
    return parser.parse_args()


async def _init_app(config: CarbonServerConfig) -> Application | None:
    webapp = Application(client_max_size=config.server.client_max_size)
    config.setup(webapp)
    fusion_auth_api = FusionAuthAPI(
        config=config.auth_api,
        authorize_impl=_authorize_impl,
    )
    fusion_auth_api.setup(webapp)
    info = Info(api='carbon', version=version)
    fusion_info_api = FusionInfoAPI(info=info, config=config.info_api)
    fusion_info_api.setup(webapp)
    fusion_constant_api = FusionConstantAPI(
        config=config.constant_api, constant_cls=Constant
    )
    fusion_constant_api.setup(webapp)
    fusion_case_api = FusionCaseAPI(
        config=config.case_api,
        case_cls=Case,
        attach_case_impl=attach_case_impl,
        create_case_impl=create_case_impl,
        update_case_impl=update_case_impl,
        retrieve_case_impl=retrieve_case_impl,
        enumerate_cases_impl=enumerate_cases_impl,
    )
    fusion_case_api.setup(webapp)
    fusion_event_api = FusionEventAPI(config=config.event_api, event_cls=Event)
    fusion_event_api.setup(webapp)
    setup_api(webapp)
    setup_pubsub(webapp)
    storage = Storage(config=config.storage)
    storage.setup(webapp)
    return webapp


# pylint: disable=W0702


def app():
    """Carbon server entrypoint"""
    _LOGGER.info("Carbon API Server %s", version)
    args = _parse_args()
    try:
        config = CarbonServerConfig.from_filepath(args.config)
    except:
        _LOGGER.exception("invalid configuration file: %s", args.config)
        return
    if not config:
        _LOGGER.error("failed to load configuration file: %s", args.config)
        return
    try:
        run_app(
            app=_init_app(config),
            host=config.server.host,
            port=config.server.port,
            handle_signals=True,
        )
    except ConfigError as exc:
        _LOGGER.error("configuration error: %s", exc)

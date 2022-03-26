# -*- coding: utf-8 -*-
__desc__ = '''bilibili-toolman 哔哩哔哩搬运工具'''
__version__ = '1.0.6.8'

from . import providers
from .bilisession import logger
from .bilisession.common.submission import Submission,SubmissionVideos
from .bilisession.web import BiliSession as BiliWebSession
from .bilisession.client import BiliSession as BiliClientSession
from .cli.main import upload_sources,download_sources

#coding=utf-8
__author__ = 'xiyuanbupt'
# e-mail : xywbupt@gmail.com

import json
import datetime

import tornado
import tornado.web

from tornado import gen
from tornado.httpclient import AsyncHTTPClient,HTTPRequest

from tornado.web import MissingArgumentError

from bson.objectid import ObjectId
from scrapy.pipelines.files import FilesPipeline

from conf_util import ConfUtil
from util.xmlGenerator import XMLGenerator



class UnSupportWebError(Exception):

    def __init__(self, web_str):
        self.web_str = web_str

    def __str__(self):
        return 'Web string %s is unsuported'%self.web_str

xmlGenerator = XMLGenerator()

class XXXSender(tornado.web.RequestHandler):

    def initialize(self,collection,web_str):
        self.collection = collection
        self.web_str = web_str

    # 推送数据到cnr的索贝接口
    @gen.coroutine
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode('utf-8'))
        _ids = data.get('_ids',None)
        force_push = data.get('force_push',False)
        if not _ids:
            raise MissingArgumentError("_ids")
        coll = self.application.db[self.collection]
        if force_push:
            audios = yield [coll.find_one({
                "_id":ObjectId(_id)
            }) for _id in _ids]
        else:
            audios = yield [coll.find_one({
                "_id":ObjectId(_id),
                "sendToCNRTime":None
            }) for _id in _ids]
        # 如果对应的audio与媒体文件没有被下载，那么下载对应的audio与媒体文件
        if self.web_str == 'kl':
            pass
        elif self.web_str == 'xmly':
            pass
        elif self.web_str == 'qt':
            pass
        else:
            raise UnSupportWebError(self.web_str)

        xmls = [xmlGenerator.getXMLContentFromAudio(self.web_str,audio) for audio in audios if audio ]
        resps = yield [self.sendXMLToCNR(xml) for xml in xmls]
        # 将推送到cnr 的时间设置到数据库中
        yield [coll.update(
            {"_id":audio["_id"]},
            {
                "$set":{
                    "sendToCNRTime":datetime.datetime.now()
                }
            }
        ) for audio in audios]
        self.write({"audios":[audio.get('album_title') for audio in audios],
                    "resps":[{'code':resp.code,'reason':resp.reason} for resp in resps],
                    "request_push_count":len(_ids),
                    "real_push_count":len(xmls),
                    "force_push":force_push
                    })

    @gen.coroutine
    def sendXMLToCNR(self,xml):
        '''
        将xml 内容推送到cnr
        :param xml:
        :return:
        '''
        client = AsyncHTTPClient()
        headers = {'Content-Type':'application/xml'}
        request = HTTPRequest(
            ConfUtil.getCnrUri(),headers = headers,
            body=xml.encode('utf=8'),
            method="POST"
        )
        resp = yield client.fetch(request)
        raise gen.Return(resp)
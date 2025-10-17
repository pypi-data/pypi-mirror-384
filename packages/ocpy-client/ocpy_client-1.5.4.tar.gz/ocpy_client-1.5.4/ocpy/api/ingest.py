#!/usr/bin/env python3
import tempfile
import xml
import os
from loguru import logger
from random import choice

import requests
from requests import Request, Session
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import json
import xmltodict
from pprint import pprint

from typing import List, Tuple, Optional
import xml.etree.ElementTree as ElemTree

from ocpy.model.mediapackage import MediaPackage
from ocpy.api.api_client import OpenCastBaseApiClient, \
    OpenCastDigestBaseApiClient, OpenCastApiService
from ocpy.utils import create_acl_xml


class IngestApi(OpenCastApiService, OpenCastBaseApiClient,
                OpenCastDigestBaseApiClient):
    def __init__(
            self,
            service_url,
            user=None,
            password=None,
            digest_user=None,
            digest_password=None,
            use_digest_auth=False,
            **kwargs
    ):
        OpenCastApiService.__init__(self, service_url)
        OpenCastBaseApiClient.__init__(self, user, password)
        OpenCastDigestBaseApiClient.__init__(self, digest_user,
                                             digest_password, optional=True)
        self.use_digest_auth = self.use_digest_auth

        self.session = Session()
        if self.use_digest_auth:
            self.session.auth = HTTPDigestAuth(self.digest_user,
                                               self.digest_password)
            self.session.headers.update({"X-Requested-Auth": "Digest"})
        else:
            self.session.auth = HTTPBasicAuth(self.user, self.password)

    def create_empty_media_package(self, **kwargs) -> MediaPackage:
        url = self.base_url + "/createMediaPackage"
        res = self.session.get(
            url,
            **kwargs
        )
        if res.ok:
            try:
                return MediaPackage(res.text)
            except xml.parsers.expat.ExpatError:
                raise Exception(
                    "No valid XML response (probably authentication failure)!"
                )
        raise Exception(
            "Could not create empty media_package! ({})".format(
                res.status_code)
        )

    def add_attachment(
            self, media_package: MediaPackage, flavor: str, file: str, **kwargs
    ):
        url = self.base_url + "/addAttachment"
        data = {"flavor": flavor, "mediaPackage": media_package.get_xml()}

        with open(os.path.expanduser(file), "rb") as f:
            files = {"file": f}
            request = Request(
                method="POST",
                url=url,
                data=data,
                files=files,
                **kwargs
            )
            res = self.session.send(self.session.prepare_request(request))
            print(res.url)
            if res.ok:
                return MediaPackage(res.content)
            print(res.content)
            print(res.status_code)
            raise Exception("Could not add attachment!")

    def add_track(
            self,
            media_package: MediaPackage,
            flavor: str = "presentation/source",
            file: Optional[str] = None,
            url: Optional[str] = None,
    ):
        print("adding track")
        if (file is None and url is None) or (
                file is not None and url is not None):
            raise ValueError(
                "exactly one of file and url has to be specified!")
        track_url = self.base_url + "/addTrack"
        if url is not None:
            data = {
                "url": url,
                "flavor": flavor,
                "mediaPackage": media_package.get_xml(),
            }
            request = Request(
                method="POST",
                url=track_url,
                data=data,
            )
            res = self.session.send(self.session.prepare_request(request))
        elif file is not None:
            with open(os.path.expanduser(file), "rb") as f:
                files = {"file": f}

                data = {"flavor": flavor,
                        "mediaPackage": media_package.get_xml()}
                request = Request(
                    method="POST",
                    url=track_url,
                    data=data,
                    files=files,
                )
                res = self.session.send(self.session.prepare_request(request))

        print(res.url)
        if res.ok:
            return MediaPackage(res.content)
        print(res.content)
        print(res.status_code)
        raise Exception("Could not add track!")

    def add_media_package(
            self, files: List[Tuple[str, str]], workflow_id: str = None,
            **kwargs
    ):
        """
        :param files:
        :param workflow_id:
        :param kwargs:
        :return:
        """
        if "title" not in kwargs:
            raise ValueError("Title must be specified!")
        url = self.base_url + "/addMediaPackage"
        if workflow_id is not None:
            url += "/" + workflow_id
        form_data = []
        for k in kwargs:
            form_data.append((k, (None, kwargs[k])))
        if isinstance(files, str):
            files = [files]
        if len(files) == 1 and isinstance(files[0], str):
            form_data.append(("flavor", (None, "presentation/source")))
            form_data.append(("file", open(files[0], "rb")))
        else:
            for file in files:
                if not isinstance(file, tuple):
                    raise ValueError(
                        "files must be a list of tuples in the form: (flavor, file)"
                    )
                form_data.append(("flavor", (None, file[0])))
                form_data.append(("file", open(file[1], "rb")))

        for k, v in kwargs.items():
            form_data.append((k, v))

        request = Request(
            method="POST",
            url=url,
            files=form_data,
        )
        res = self.session.send(self.session.prepare_request(request))
        if res.ok:
            return res.text
        else:
            logger.critical("Could not add media package to Opencast!")
            logger.critical("Status code: " + str(res.status_code))
            print(request.url)
            print(request.headers)

        raise Exception("Could not add media package to Opencast!")

    def add_dc_catalog(
            self,
            media_package: MediaPackage,
            dublin_core_xml: str,
            flavor="dublincore/episode",
    ):
        url = self.base_url + "/addDCCatalog"
        data = {"mediaPackage": media_package.get_xml(),
                "dublinCore": dublin_core_xml}
        if flavor is not None:
            data["flavor"] = flavor

        request = Request(
            method="POST",
            url=url,
            data=data,
        )
        res = self.session.send(self.session.prepare_request(request))
        if res.ok:
            return MediaPackage(res.content)
        logger.critical("Could not add dc catalog")
        logger.critical("Status code: " + str(res.status_code))
        raise Exception("Could not add dc catalog!")

    def add_metadata(
            self,
            media_package: MediaPackage,
            flavor="dublincore/episode",
            root_element_name="dublincore",
            abstract: str = None,
            accessRights: str = None,
            available: str = None,
            contributor: str = None,
            coverage: str = None,
            created: str = None,
            creator: str = None,
            date: str = None,
            description: str = None,
            extent: str = None,
            format: str = None,
            identifier: str = None,
            isPartOf: str = None,
            isReferencedBy: str = None,
            isReplacedBy: str = None,
            language: str = None,
            license: str = None,
            publisher: str = None,
            relation: str = None,
            replaces: str = None,
            rights: str = None,
            rightsHolder: str = None,
            source: str = None,
            spatial: str = None,
            subject: str = None,
            temporal: str = None,
            title: str = None,
            type: str = None,
            **kwargs
    ):
        """

        :param media_package:
        :param flavor:
        :param abstract:
        :param accessRights:
        :param available:
        :param contributor:
        :param coverage:
        :param created:
        :param creator:
        :param date:
        :param description:
        :param extent: length of media file (in ISO8601 format) can perhaps left empty
        :param format:
        :param identifier:
        :param isPartOf:
        :param isReferencedBy:
        :param isReplacedBy:
        :param language:
        :param license:
        :param publisher:
        :param relation:
        :param replaces:
        :param rights:
        :param rightsHolder:
        :param source:
        :param spatial:
        :param subject:
        :param temporal:
        :param title:
        :param type:
        :return:
        """

        # TODO: implement other metadata fields

        root = ElemTree.Element(root_element_name)
        root.set('xmlns', 'http://www.opencastproject.org/xsd/1.0/dublincore/')
        root.set('xmlns:dcterms', 'http://purl.org/dc/terms/')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        if title is not None:
            ElemTree.SubElement(root, 'dcterms:title').text = title
        if description is not None:
            ElemTree.SubElement(root, 'dcterms:description').text = description
        if isPartOf is not None:
            ElemTree.SubElement(root, 'dcterms:isPartOf').text = isPartOf
        if source is not None:
            ElemTree.SubElement(root, 'dcterms:source').text = source
        if creator is not None:
            ElemTree.SubElement(root, 'dcterms:creator').text = creator
        if spatial is not None:
            ElemTree.SubElement(root, 'dcterms:spatial').text = spatial
        if rightsHolder is not None:
            ElemTree.SubElement(root,
                                'dcterms:rightsHolder').text = rightsHolder
        if temporal is not None:
            ElemTree.SubElement(root, 'dcterms:temporal').set('xsi:type',
                                                              'dcterms:Period')
            ElemTree.SubElement(root, 'dcterms:temporal').text = temporal

        temporal_str = "start={start}; end={end}; scheme=W3C-DTF;"

        """
         $start_end_string_iso = (new ilDateTime(
            strtotime($this->metadata->getField('startDate')->getValue() . ' ' . $this->metadata->getField('startTime')->getValue()),
            IL_CAL_UNIX)
        )->get(IL_CAL_FKT_DATE, 'Y-m-d\TH:i:s.u\Z');
        $xml_writer->xmlElement('dcterms:temporal', [
            'xsi:type' => 'dcterms:Period'
        ], 'start=' . $start_end_string_iso . '; ' . 'end=' . $start_end_string_iso . '; scheme=W3C-DTF;');
        """

        # ElemTree.SubElement(root, 'dcterms:created').text = created
        """
        $xml_writer->xmlElement(
            'dcterms:created',
            [],
            (new ilDateTime(time(), IL_CAL_UNIX))
                ->get(IL_CAL_FKT_DATE, 'Y-m-d\TH:i:s.u\Z', 'UTC')
        );
        """

        for k, v in kwargs.items():
            ElemTree.SubElement(root, f"dcterms:{k}").text = v

        dublin_core_xml = ElemTree.tostring(root, method='xml').decode()

        return self.add_dc_catalog(media_package,
                                   dublin_core_xml=dublin_core_xml,
                                   flavor=flavor)

    def ingest(
            self,
            media_package: MediaPackage,
            workflow_definition_id: str,
            workflow_instance_id: str = None,
            # workflow_parameters: List[str] = [],
            **kwargs
    ):
        url = self.base_url + "/ingest"
        if workflow_instance_id is None:
            url += "/" + workflow_definition_id
            data = {
                **kwargs,
                "mediaPackage": media_package.get_xml()
            }
        else:
            data = {
                **kwargs,
                "mediaPackage": media_package.get_xml(),
                "workflowDefinitionId": workflow_definition_id,
                "workflowInstanceId": workflow_instance_id
            }

        request = Request(
            method="POST",
            url=url,
            data=data
        )
        res = self.session.send(self.session.prepare_request(request))

        print(res.url)
        if res.ok:
            return res.content
        print(res.content)
        print(res.status_code)
        raise Exception("Could not ingest media package!")

    def add_acl_attachment(self, media_package: MediaPackage, event_id: str, role_right_tuples: List[Tuple[str, str]],
                           **kwargs):
        flavor = "security/xacml+episode"
        """
         $plupload = new Plupload();
        $tmp_name = uniqid('tmp');
        file_put_contents($plupload->getTargetDir() . '/' . $tmp_name, (new ACLtoXML($event->getAcl()))->getXML());
        $upload_file = new xoctUploadFile();
        $upload_file->setFileSize(filesize($plupload->getTargetDir() . '/' . $tmp_name));
        $upload_file->setPostVar('attachment');
        $upload_file->setTitle('attachment');
        $upload_file->setTmpName($tmp_name);
        return $upload_file;
        :return:
        """

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'security-policy-episode.xml')
            create_acl_xml(event_id, role_right_tuples, output=path)

            return self.add_attachment(media_package, flavor, file=path)


def main():
    from ocpy.api.service import ServiceApi, ServiceType

    user = "api_user"
    password = "..."
    digest_user = "opencast_system_account"
    digest_password = "..."
    s_api = ServiceApi(
        server_url="https://opencast-qa.bibliothek.kit.edu",
        user=user,
        password=password,
    )
    # s_api = ServiceApi(server_url="http://localhost:8080", user="admin", password="opencast")
    # s_api = ServiceApi()
    ingest_service = choice(s_api.get_available(ServiceType.ingest))

    api = IngestApi(
        ingest_service.get_url(),
        user=user,
        password=password,
        digest_user=digest_user,
        digest_password=digest_password,
    )
    print(api)
    print("Create empty media_package:")
    m_p = api.create_empty_media_package()
    print(m_p)
    print(m_p.get_xml())
    m_p_xml = m_p.get_xml()
    m_p = api.add_attachment(m_p, "audio/123", "/home/tobias/Music/Poison.mp3")
    print(m_p)
    # TODO: check if it is necessary to update the local mediapackage with a function result?!
    # api.add_track(m_p, url="https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_2mb.mp4")
    api.add_track(m_p, file="/home/tobias/Videos/vid2.mp4")
    # m_p = api.add_attachment(m_p, "presentation/source", "/home/tobias/Videos/vid2.mp4")
    print(m_p)
    # m_p2 = api.add_media_package("/home/tobias/Videos/vid2.mp4", "fast", title="tests ingest per API")
    # print(m_p2)
    # api.ingest(m_p, "fast")

    exit()

    # res = api.add_attachment("presentation/source", m_p, "/tmp/swtag.log")
    if os.path.exists("/Users/tobias/Movies"):  # on MAC
        res = api.add_media_package(
            [
                (
                    "presentation/source",
                    "/Users/tobias/Movies/SampleVideo_1280x720_5mb.mp4",
                )
            ],
            "fast",
            title="Test media package (MAC)",
        )
    else:  # on Linux
        # res = api.add_media_package(["/home/tobias/Videos/vid2.mp4"],
        #                            "fast", title="Test (Linux, two-files)")
        #        res = api.add_media_package([("presentation/source", "/home/tobias/Videos/vid2.mp4")],
        #                                    "fast", title="Test (Linux, two-files)")
        res = api.add_media_package(
            [
                ("presentation/source", "/home/tobias/Videos/vid1.mp4"),
                ("presenter/source", "/home/tobias/Videos/vid2.mp4"),
            ],
            "fast",
            title="New vid tests (Linux, two-files)",
        )
    print(res)


if __name__ == "__main__":
    main()

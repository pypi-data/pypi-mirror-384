import hashlib
import logging
import os
import io
import random
from typing import List

from .. import entities, PlatformException, exceptions, repositories, miscellaneous
from ..services.api_client import ApiClient
from ..services.api_client import client as client_api

logger = logging.getLogger(name='dtlpy')


class Codebases:
    """
    Codebase Repository

    The Codebases class allows the user to manage codebases and their properties.
    The codebase is the code the user uploads for the user's packages to run.
    Read more about `codebase <https://developers.dataloop.ai/tutorials/faas/introduction/chapter/>`_ in our FaaS (function as a service).
    """

    def __init__(self,
                 client_api: ApiClient,
                 project: entities.Project = None,
                 dataset: entities.Dataset = None,
                 project_id: str = None):
        self._client_api = client_api
        self._project = project
        self._project_id = project_id
        self._dataset = dataset
        self._items_repository = None
        self.git_utils = miscellaneous.GitUtils()

    @property
    def items_repository(self) -> repositories.Items:
        if self._items_repository is None:
            if self._dataset is not None or self._project is not None:
                self._items_repository = self.dataset.items
            else:
                self._items_repository = repositories.Items(client_api=client_api)
        assert isinstance(self._items_repository, repositories.Items)
        return self._items_repository

    @property
    def project(self) -> entities.Project:
        if self._project is None:
            # project is None - try dataset
            if self._dataset is None:
                # dataset is None - try from project id
                if self._project_id is None:
                    raise PlatformException(error='400',
                                            message='Cannot perform this action without a project')
                else:
                    self._project = repositories.Projects(client_api=self._client_api).get(project_id=self._project_id)
            else:
                # dataset is not None - take project from there
                self._project = self.dataset.project
        assert isinstance(self._project, entities.Project)
        return self._project

    @property
    def dataset(self) -> entities.Dataset:
        if self._dataset is None:
            # get dataset from project
            try:
                self._dataset = self.project.datasets._get_binaries_dataset()
            except exceptions.NotFound:
                raise ValueError('Missing "Binaries" dataset in the project. Please contact support for help')
        assert isinstance(self._dataset, entities.Dataset)
        return self._dataset

    @dataset.setter
    def dataset(self, dataset: entities.Dataset):
        if not isinstance(dataset, entities.Dataset):
            raise ValueError('Must input a valid Dataset entity')
        self._dataset = dataset

    @staticmethod
    def __file_hash(filepath):
        m = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                m.update(chunk)
        return m.hexdigest()

    def list_versions(self, codebase_name: str) -> entities.PagedEntities:
        """
        List all codebase versions.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        **Example**:

        .. code-block:: python

            package.codebases.list_versions(codebase_name='codebase_name')

        :param str codebase_name: code base name
        :return: list of versions
        :rtype: list
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/codebases/{}/*'.format(codebase_name))
        versions = self.items_repository.list(filters=filters)
        return versions

    def list(self) -> entities.PagedEntities:
        """
        List all codebases.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        **Example**:

        .. code-block:: python

            package.codebases.list()

        :return: Paged entity
        :rtype: dtlpy.entities.paged_entities.PagedEntities
        """
        filters = entities.Filters()
        filters.add(field='filename', values='/codebases/*')
        filters.add(field='type', values='dir')
        codebases = self.items_repository.list(filters=filters)
        return codebases

    def get(self,
            codebase_name: str = None,
            codebase_id: str = None,
            version: str = None):
        """
        Get a Codebase object to use in your code.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        **Example**:

        .. code-block:: python

            package.codebases.get(codebase_name='codebase_name')

        :param str codebase_name: optional - search by name
        :param str codebase_id: optional - search by id
        :param str version: codebase version. default is latest. options: "all", "latest" or ver number - "10"
        :return: Codebase object
        """
        if codebase_id is not None:
            matched_version = self.items_repository.get(item_id=codebase_id)
            # verify input codebase name is same as the given id
            if codebase_name is not None and matched_version.name != codebase_name:
                logger.warning(
                    "Mismatch found in codebases.get: codebase_name is different then codebase.name: "
                    "{!r} != {!r}".format(
                        codebase_name,
                        matched_version.name))
            codebase = entities.Codebase(type='item',
                                         client_api=self._client_api,
                                         itemId=matched_version.id,
                                         item=matched_version)
            return codebase

        if codebase_name is None:
            raise PlatformException(error='400', message='Either "codebase_name" or "codebase_id" is needed')
        if version is None:
            version = 'latest'

        if version not in ['all', 'latest']:
            try:
                matched_version = self.items_repository.get(
                    filepath='/codebases/{}/{}.zip'.format(codebase_name, version))
            except Exception:
                raise PlatformException(error='404',
                                        message='No matching version was found. version: {}'.format(version))
            codebase = entities.Codebase(type='item',
                                         client_api=self._client_api,
                                         itemId=matched_version.id,
                                         item=matched_version)
            return codebase

        # get all or latest
        versions_pages = self.list_versions(codebase_name=codebase_name)
        if versions_pages.items_count == 0:
            raise PlatformException(error='404', message='No codebase was found. name: {}'.format(codebase_name))
        else:
            if version == 'all':
                codebase = [entities.Codebase(type='item',
                                              client_api=self._client_api,
                                              itemId=mv.id,
                                              item=mv) for mv in versions_pages.all()]
            elif version == 'latest':
                max_ver = -1
                matched_version = None
                for page in versions_pages:
                    for ver in page:
                        if ver.type == 'dir':
                            continue
                        # extract version from filepath
                        ver_int = int(os.path.splitext(ver.name)[0])
                        if ver_int > max_ver:
                            max_ver = ver_int
                            matched_version = ver
                if matched_version is None:
                    raise PlatformException(error='404',
                                            message='No codebase was found. name: {}'.format(codebase_name))
                else:
                    codebase = entities.Codebase(type='item',
                                                 client_api=self._client_api,
                                                 itemId=matched_version.id,
                                                 item=matched_version)
            else:
                raise PlatformException(error='404', message='Unknown version string: {}'.format(version))

        return codebase

    @staticmethod
    def get_current_version(all_versions_pages, zip_md):
        """
        This method returns the current version of the codebase and other versions found.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param codebase all_versions_pages: codebase object
        :param zip_md: zipped file of codebase
        :return: current version and all versions found of codebase
        :rtype: int, int

        **Example**:

        .. code-block:: python

            package.codebases.get_current_version(all_versions_pages='codebase_entity', zip_md='path')
        """
        latest_version = 0
        same_version_found = None
        # go over all existing versions
        for v_item in all_versions_pages:
            # get latest version
            if int(os.path.splitext(v_item.item.name)[0]) > latest_version:
                latest_version = int(os.path.splitext(v_item.item.name)[0])
            # check md5 to find same codebase
            if 'md5' in v_item.item.metadata['system'] and v_item.item.metadata['system']['md5'] == zip_md:
                same_version_found = v_item
                break
        return latest_version + 1, same_version_found

    def pack(self,
             directory: str,
             name: str = None,
             extension: str = 'zip',
             description: str = '',
             ignore_directories: List[str] = None,
             ignore_max_file_size: bool = False):
        """
        Zip a local code directory and post to codebases.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param str directory: local directory to pack
        :param str name: codebase name
        :param str extension: the extension of the file
        :param str description: codebase description
        :param list[str] ignore_directories: directories to ignore.
        :return: Codebase object
        :rtype: dtlpy.entities.codebase.Codebase

        **Example**:

        .. code-block:: python

            package.codebases.pack(directory='path_dir', name='codebase_name')
        """
        # create/get .dataloop dir
        cwd = os.getcwd()
        dl_dir = os.path.join(cwd, '.dataloop')
        if not os.path.isdir(dl_dir):
            os.mkdir(dl_dir)

        # get codebase name
        if name is None:
            name = os.path.basename(directory)

        # create/get dist folder
        zip_filename = os.path.join(dl_dir, '{}_{}.{}'.format(name, str(random.randrange(0, 1000)), extension))

        try:
            if not os.path.isdir(directory):
                raise PlatformException(error='400', message='Not a directory: {}'.format(directory))
            directory = os.path.abspath(directory)

            # create zipfile
            miscellaneous.Zipping.zip_directory(zip_filename=zip_filename,
                                                directory=directory,
                                                ignore_directories=ignore_directories,
                                                ignore_max_file_size=ignore_max_file_size)
            zip_md = self.__file_hash(zip_filename)

            # get latest version
            same_version_found = None
            try:
                all_versions_pages = self.get(codebase_name=name, version='all')
            except exceptions.NotFound:
                all_versions_pages = None
            if all_versions_pages is None:
                # no codebase with that name - create new version
                current_version = 0
            else:
                current_version, same_version_found = self.get_current_version(all_versions_pages=all_versions_pages,
                                                                               zip_md=zip_md)

            if same_version_found is not None:
                # same md5 hash file found in version - return the matched version
                codebase = same_version_found
            else:
                # no matched version was found - create a new version
                # read from zipped file
                with open(zip_filename, 'rb') as f:
                    buffer = io.BytesIO(f.read())
                    buffer.name = '{}.{}'.format(str(current_version), extension)

                # upload item
                item = self.items_repository.upload(local_path=buffer,
                                                    remote_path='/codebases/{}'.format(name))
                if isinstance(item, list) and len(item) == 0:
                    raise PlatformException(error='400', message='Failed upload codebase, check log file for details')

                # add source code to metadata
                if 'system' not in item.metadata:
                    item.metadata['system'] = dict()
                item.metadata['system']['description'] = description
                item.metadata['system']['md5'] = zip_md

                # add git info to metadata
                if miscellaneous.GitUtils.is_git_repo(path=directory):
                    # create 'git' field in metadata
                    if 'git' not in item.metadata:
                        item.metadata['git'] = dict()

                    # add to metadata
                    item.metadata['git']['status'] = miscellaneous.GitUtils.git_status(path=directory)
                    item.metadata['git']['log'] = miscellaneous.GitUtils.git_log(path=directory)
                    item.metadata['git']['url'] = miscellaneous.GitUtils.git_url(path=directory)

                # update item
                item = self.items_repository.update(item=item, system_metadata=True)
                codebase = entities.Codebase(type='item',
                                             client_api=self._client_api,
                                             itemId=item.id,
                                             item=item)
        except Exception:
            logger.error('Error when packing:')
            raise
        finally:
            # cleanup
            if zip_filename is not None:
                if os.path.isfile(zip_filename):
                    os.remove(zip_filename)
        return codebase

    def _unpack_single(self,
                       codebase,
                       download_path: str,
                       local_path: str):
        """
        :param dtlpy.entities.codebase.Codebase codebase: codebase object
        :param str download_path:
        :param str local_path:
        """
        # downloading with specific filename
        if isinstance(codebase, entities.ItemCodebase):
            artifact_filepath = self.items_repository.download(items=codebase.item_id,
                                                               save_locally=True,
                                                               local_path=os.path.join(download_path,
                                                                                       codebase.item.name),
                                                               to_items_folder=False)
            if not os.path.isfile(artifact_filepath):
                raise PlatformException(error='404',
                                        message='error downloading codebase. see above for more information')
            miscellaneous.Zipping.unzip_directory(zip_filename=artifact_filepath,
                                                  to_directory=local_path)
            os.remove(artifact_filepath)
            logger.info('Source code was unpacked to: {}'.format(artifact_filepath))
        elif isinstance(codebase, entities.Item):
            artifact_filepath = codebase.download(save_locally=True,
                                                  local_path=os.path.join(download_path,
                                                                          codebase.name),
                                                  to_items_folder=False)
            if not os.path.isfile(artifact_filepath):
                raise PlatformException(error='404',
                                        message='error downloading codebase. see above for more information')
            miscellaneous.Zipping.unzip_directory(zip_filename=artifact_filepath,
                                                  to_directory=local_path)
            os.remove(artifact_filepath)
            logger.info('Source code was unpacked to: {}'.format(artifact_filepath))
        elif isinstance(codebase, entities.GitCodebase):
            if codebase.is_git_repo(local_path) or \
                    codebase.is_git_repo(os.path.join(local_path, codebase.git_repo_name)):
                artifact_filepath = self.pull_git(codebase=codebase, local_path=local_path)
            else:  # Clone the repo if not exist
                artifact_filepath = self.clone_git(codebase=codebase, local_path=local_path)
        else:
            raise ValueError('Not implemented: "_unpack_single" for codebase type: {!r}'.format(codebase.type))
        return artifact_filepath

    def _get_single(self, codebase: entities.GitCodebase, name: str):
        value = None
        integration_id = codebase.credentials.get(name, {}).get('id', None)
        key = codebase.credentials.get(name, {}).get('key', None)
        if integration_id is not None:
            try:
                key = self.project.integrations.get(integrations_id=integration_id).name
            except Exception:
                pass
            value = os.environ.get(key, None)

        return value

    def _get_credential(self, codebase: entities.GitCodebase):
        username = password = None

        if codebase.credentials:
            try:
                username = self._get_single(codebase=codebase, name='username')
                password = self._get_single(codebase=codebase, name='password')
            except Exception:
                logger.exception('Failed to get credentials from codebase')

        return username, password

    def clone_git(self,
                  codebase: entities.Codebase,
                  local_path: str):
        """
        Clone code base

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.codebase.Codebase codebase: codebase object
        :param str local_path: local path
        :return: path where the clone will be
        :rtype: str

         **Example**:

        .. code-block:: python

            package.codebases.clone_git(codebase='codebase_entity', local_path='local_path')
        """
        if not isinstance(codebase, entities.GitCodebase):
            raise RuntimeError('only support Git Codebase')
        username, password = self._get_credential(codebase=codebase)
        response = self.git_utils.git_clone(path=local_path,
                                            git_url=codebase.git_url,
                                            tag=codebase.git_tag,
                                            username=username,
                                            password=password)
        if response:
            logger.info('Source code was cloned from {}(Git) to: {}'.format(codebase.git_url, local_path))
        else:
            raise RuntimeError('Failed cloning. See above for full log. codebase: {}'.format(codebase))
        return local_path

    def pull_git(self, codebase, local_path):
        """
        Pull (download) a codebase.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.codebase.Codebase codebase: codebase object
        :param str local_path: local path
        :return: path where the Pull will be
        :rtype: str

        **Example**:

        .. code-block:: python

            package.codebases.pull_git(codebase='codebase_entity', local_path='local_path')
        """
        pull_cmd = 'git pull'
        if not codebase.is_git_repo(local_path):
            local_path = os.path.join(local_path, codebase.git_repo_name)
        response = self.git_utils.git_command(path=local_path, cmd=pull_cmd)
        if response:
            logger.info('pull successful {}(Git) to: {}'.format(codebase.git_url, os.path.dirname(local_path)))
        else:
            logger.critical("Could not pull")

        # we can test if this is not the same repo if needed...
        # FIXME need to change the order - checkout new branch and pull
        response_2 = self.git_utils.git_command(path=local_path, cmd='git checkout {}'.format(codebase.git_tag))
        return local_path

    def unpack(self,
               codebase: entities.Codebase = None,
               codebase_name: str = None,
               codebase_id: str = None,
               local_path: str = None,
               version: str = None):
        """
        Unpack codebase locally. Download source code and unzip.

        **Prerequisites**: You must be in the role of an *owner* or *developer*. You must have a package.

        :param dtlpy.entities.codebase.Codebase codebase: `dl.Codebase` object
        :param str codebase_name: search by name
        :param str codebase_id: search by id
        :param str local_path: local path to save codebase
        :param str version: codebase version to unpack. default - latest
        :return: String (dirpath)
        :rtype: str

        **Example**:

        .. code-block:: python

            package.codebases.unpack(codebase='codebase_entity', local_path='local_path')
        """
        # get the codebase / multiple codebase
        if codebase is None:
            codebase = self.get(codebase_name=codebase_name,
                                codebase_id=codebase_id,
                                version=version)
        elif codebase_name is not None or codebase_id is not None:
            logger.warning("Using given codebase. Does not preforming search with name {!r} / id {!r}".
                           format(codebase_name, codebase_id))
        download_path = local_path
        if isinstance(codebase, entities.PagedEntities):
            for page in codebase:
                for item in page:
                    local_path = os.path.join(download_path, 'v.' + item.name.split('.')[0])
                    self._unpack_single(codebase=item,
                                        download_path=download_path,
                                        local_path=local_path)
            return os.path.dirname(local_path)
        elif isinstance(codebase, list):
            for item in codebase:
                local_path = os.path.join(download_path, 'v.' + item.item.name.split('.')[0])
                self._unpack_single(codebase=item,
                                    download_path=download_path,
                                    local_path=local_path)
            return os.path.dirname(local_path)
        elif isinstance(codebase, (entities.ItemCodebase, entities.Item, entities.GitCodebase)):
            artifact_filepath = self._unpack_single(codebase=codebase,
                                                    download_path=download_path,
                                                    local_path=local_path)
            if isinstance(codebase, (entities.ItemCodebase, entities.Item)):
                dir_path = os.path.dirname(artifact_filepath)  # use the directory of the artifact
            else:
                dir_path = artifact_filepath
            logger.info('Source code was unpacked to: {}'.format(dir_path))
        else:
            raise PlatformException(
                error='404',
                message='Codebase was not found! name:{name}, id:{id}'.format(name=codebase_name,
                                                                              id=codebase_id))
        return dir_path
